from __future__ import annotations
import importlib
import logging
import os
from multiprocessing import Process, freeze_support, Queue, set_start_method
from sys import platform
from typing import List, Optional

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.worker.worker_config import resolve_worker_config

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)

_decorated_functions = {}
_mp_fork_set = False
if not _mp_fork_set:
    try:
        if platform == "win32":
            set_start_method("spawn")
        else:
            set_start_method("fork")
        _mp_fork_set = True
    except Exception as e:
        logger.info("error when setting multiprocessing.set_start_method - maybe the context is set %s", e.args)
    if platform == "darwin":
        os.environ["no_proxy"] = "*"

def register_decorated_fn(name: str, poll_interval: int, domain: str, worker_id: str, func,
                         thread_count: int = 1, register_task_def: bool = False,
                         poll_timeout: int = 100, lease_extend_enabled: bool = True):
    logger.info("decorated %s", name)
    _decorated_functions[(name, domain)] = {
        "func": func,
        "poll_interval": poll_interval,
        "domain": domain,
        "worker_id": worker_id,
        "thread_count": thread_count,
        "register_task_def": register_task_def,
        "poll_timeout": poll_timeout,
        "lease_extend_enabled": lease_extend_enabled
    }


def get_registered_workers() -> List[Worker]:
    """
    Get all registered workers from decorated functions.

    Returns:
        List of Worker instances created from @worker_task decorated functions
    """
    workers = []
    for (task_def_name, domain), record in _decorated_functions.items():
        worker = Worker(
            task_definition_name=task_def_name,
            execute_function=record["func"],
            poll_interval=record["poll_interval"],
            domain=domain,
            worker_id=record["worker_id"],
            thread_count=record.get("thread_count", 1)
        )
        workers.append(worker)
    return workers


def get_registered_worker_names() -> List[str]:
    """
    Get names of all registered workers.

    Returns:
        List of task definition names
    """
    return [name for (name, domain) in _decorated_functions.keys()]


class TaskHandler:
    """
    Unified task handler that manages worker processes.

    Architecture:
        - Always uses multiprocessing: One Python process per worker
        - Each process continuously polls for tasks (non-blocking)
        - Tasks execute in thread pool (controlled by thread_count parameter)
        - Polling continues while tasks are executing in background
        - Polling and updates are always synchronous (requests library)

    Execution Modes (asyncio parameter):

        asyncio=False (default) - Recommended:
            - Sync workers: Execute directly in the worker process
            - Async workers: Execute via BackgroundEventLoop (1.5-2x faster)
            - Best for: All use cases

        asyncio=True (deprecated, works same as False):
            - Kept for compatibility, but behaves identically to asyncio=False
            - Both sync and async workers use the same execution path
            - Recommendation: Use default (asyncio=False)

    Usage:
        # Default mode (asyncio=False)
        handler = TaskHandler(configuration=config)
        handler.start_processes()
        handler.join_processes()

        # AsyncIO execution mode
        handler = TaskHandler(configuration=config, asyncio=True)
        handler.start_processes()
        handler.join_processes()

        # Context manager (recommended)
        with TaskHandler(configuration=config) as handler:
            handler.start_processes()
            handler.join_processes()

    Worker Examples:
        # Async worker (works with both modes)
        @worker_task(task_definition_name='fetch_data')
        async def fetch_data(url: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
            return {'data': response.json()}

        # Sync worker (works with both modes)
        @worker_task(task_definition_name='process_data')
        def process_data(data: dict) -> dict:
            result = expensive_computation(data)
            return {'result': result}
    """

    def __init__(
            self,
            workers: Optional[List[WorkerInterface]] = None,
            configuration: Optional[Configuration] = None,
            metrics_settings: Optional[MetricsSettings] = None,
            scan_for_annotated_workers: bool = True,
            import_modules: Optional[List[str]] = None,
            asyncio: bool = False
    ):
        workers = workers or []
        self.asyncio = asyncio
        self.logger_process, self.queue = _setup_logging_queue(configuration)

        # imports
        importlib.import_module("conductor.client.http.models.task")
        importlib.import_module("conductor.client.worker.worker_task")
        if import_modules is not None:
            for module in import_modules:
                logger.info("loading module %s", module)
                importlib.import_module(module)

        elif not isinstance(workers, list):
            workers = [workers]
        if scan_for_annotated_workers is True:
            for (task_def_name, domain), record in _decorated_functions.items():
                fn = record["func"]

                # Get code-level configuration from decorator
                code_config = {
                    'poll_interval': record["poll_interval"],
                    'domain': domain,
                    'worker_id': record["worker_id"],
                    'thread_count': record.get("thread_count", 1),
                    'register_task_def': record.get("register_task_def", False),
                    'poll_timeout': record.get("poll_timeout", 100),
                    'lease_extend_enabled': record.get("lease_extend_enabled", True)
                }

                # Resolve configuration with environment variable overrides
                resolved_config = resolve_worker_config(
                    worker_name=task_def_name,
                    **code_config
                )

                worker = Worker(
                    task_definition_name=task_def_name,
                    execute_function=fn,
                    worker_id=resolved_config['worker_id'],
                    domain=resolved_config['domain'],
                    poll_interval=resolved_config['poll_interval'],
                    thread_count=resolved_config['thread_count'],
                    register_task_def=resolved_config['register_task_def'],
                    poll_timeout=resolved_config['poll_timeout'],
                    lease_extend_enabled=resolved_config['lease_extend_enabled'])
                logger.info("created worker with name=%s and domain=%s", task_def_name, resolved_config['domain'])
                workers.append(worker)

        self.__create_task_runner_processes(workers, configuration, metrics_settings)
        self.__create_metrics_provider_process(metrics_settings)
        logger.info("TaskHandler initialized")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_processes()

    def stop_processes(self) -> None:
        self.__stop_task_runner_processes()
        self.__stop_metrics_provider_process()
        logger.info("Stopped worker processes...")
        self.queue.put(None)
        self.logger_process.terminate()

    def start_processes(self) -> None:
        logger.info("Starting worker processes...")
        freeze_support()
        self.__start_task_runner_processes()
        self.__start_metrics_provider_process()
        logger.info("Started all processes")

    def join_processes(self) -> None:
        try:
            self.__join_task_runner_processes()
            self.__join_metrics_provider_process()
            logger.info("Joined all processes")
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt: Stopping all processes")
            self.stop_processes()

    def __create_metrics_provider_process(self, metrics_settings: MetricsSettings) -> None:
        if metrics_settings is None:
            self.metrics_provider_process = None
            return
        self.metrics_provider_process = Process(
            target=MetricsCollector.provide_metrics,
            args=(metrics_settings,)
        )
        logger.info("Created MetricsProvider process")

    def __create_task_runner_processes(
            self,
            workers: List[WorkerInterface],
            configuration: Configuration,
            metrics_settings: MetricsSettings
    ) -> None:
        self.task_runner_processes = []
        self.workers = []
        for worker in workers:
            self.__create_task_runner_process(
                worker, configuration, metrics_settings
            )
            self.workers.append(worker)

    def __create_task_runner_process(
            self,
            worker: WorkerInterface,
            configuration: Configuration,
            metrics_settings: MetricsSettings
    ) -> None:
        task_runner = TaskRunner(worker, configuration, metrics_settings, asyncio=self.asyncio)
        process = Process(target=task_runner.run)
        self.task_runner_processes.append(process)

    def __start_metrics_provider_process(self):
        if self.metrics_provider_process is None:
            return
        self.metrics_provider_process.start()
        logger.info("Started MetricsProvider process")

    def __start_task_runner_processes(self):
        n = 0
        for i, task_runner_process in enumerate(self.task_runner_processes):
            task_runner_process.start()
            worker = self.workers[i]
            paused_status = "PAUSED" if worker.paused() else "ACTIVE"
            logger.info("Started worker '%s' [%s]", worker.get_task_definition_name(), paused_status)
            n = n + 1
        logger.info("Started %s TaskRunner process(es)", n)

    def __join_metrics_provider_process(self):
        if self.metrics_provider_process is None:
            return
        self.metrics_provider_process.join()
        logger.info("Joined MetricsProvider processes")

    def __join_task_runner_processes(self):
        for task_runner_process in self.task_runner_processes:
            task_runner_process.join()
        logger.info("Joined TaskRunner processes")

    def __stop_metrics_provider_process(self):
        self.__stop_process(self.metrics_provider_process)

    def __stop_task_runner_processes(self):
        for task_runner_process in self.task_runner_processes:
            self.__stop_process(task_runner_process)

    def __stop_process(self, process: Process):
        if process is None:
            return
        try:
            logger.debug("Terminating process: %s", process.pid)
            process.terminate()
        except Exception as e:
            logger.debug("Failed to terminate process: %s, reason: %s", process.pid, e)
            process.kill()
            logger.debug("Killed process: %s", process.pid)


# Setup centralized logging queue
def _setup_logging_queue(configuration: Configuration):
    queue = Queue()
    if configuration:
        configuration.apply_logging_config()
        log_level = configuration.log_level
        logger_format = configuration.logger_format
    else:
        log_level = logging.DEBUG
        logger_format = None

    logger.setLevel(log_level)

    # start the logger process
    logger_p = Process(target=__logger_process, args=(queue, log_level, logger_format))
    logger_p.start()
    return logger_p, queue


# This process performs the centralized logging
def __logger_process(queue, log_level, logger_format=None):
    c_logger = logging.getLogger(
        Configuration.get_logging_formatted_name(
            __name__
        )
    )

    c_logger.setLevel(log_level)

    # configure a stream handler
    sh = logging.StreamHandler()
    if logger_format:
        formatter = logging.Formatter(logger_format)
        sh.setFormatter(formatter)
    c_logger.addHandler(sh)

    # run forever
    while True:
        # consume a log message, block until one arrives
        message = queue.get()
        # check for shutdown
        if message is None:
            break
        # log the message
        c_logger.handle(message)
