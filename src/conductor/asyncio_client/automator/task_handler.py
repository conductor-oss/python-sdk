from __future__ import annotations

import asyncio
import importlib
import logging
import os
from multiprocessing import Process, Queue, freeze_support, set_start_method
from sys import platform
from typing import List, Optional

from conductor.asyncio_client.automator.task_runner import AsyncTaskRunner
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.telemetry.metrics_collector import AsyncMetricsCollector
from conductor.asyncio_client.worker.worker import Worker
from conductor.asyncio_client.worker.worker_interface import WorkerInterface
from conductor.shared.configuration.settings.metrics_settings import MetricsSettings

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))

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
        logger.error(
            "Error when setting multiprocessing.set_start_method - maybe the context is set %s",
            e.args,

        )
    if platform == "darwin":
        os.environ["no_proxy"] = "*"


def register_decorated_fn(
    name: str, poll_interval: int, domain: str, worker_id: str, func
):
    logger.info("Registering decorated function: %s", name)
    _decorated_functions[(name, domain)] = {
        "func": func,
        "poll_interval": poll_interval,
        "domain": domain,
        "worker_id": worker_id,
    }


class TaskHandler:
    def __init__(
        self,
        workers: Optional[List[WorkerInterface]] = None,
        configuration: Optional[Configuration] = None,
        metrics_settings: Optional[MetricsSettings] = None,
        scan_for_annotated_workers: bool = True,
        import_modules: Optional[List[str]] = None,
    ):
        workers = workers or []
        self.logger_process, self.queue = _setup_logging_queue(configuration)

        # imports
        importlib.import_module("conductor.asyncio_client.adapters.models.task_adapter")
        importlib.import_module("conductor.asyncio_client.worker.worker_task")
        if import_modules is not None:
            for module in import_modules:
                logger.debug("Loading module %s", module)
                importlib.import_module(module)

        elif not isinstance(workers, list):
            workers = [workers]
        if scan_for_annotated_workers is True:
            for (task_def_name, domain), record in _decorated_functions.items():
                fn = record["func"]
                worker_id = record["worker_id"]
                poll_interval = record["poll_interval"]

                worker = Worker(
                    task_definition_name=task_def_name,
                    execute_function=fn,
                    worker_id=worker_id,
                    domain=domain,
                    poll_interval=poll_interval,
                )
                logger.info(
                    "Created worker with name: %s; domain: %s", task_def_name, domain
                )
                workers.append(worker)

        self.__create_task_runner_processes(workers, configuration, metrics_settings)
        self.__create_metrics_provider_process(metrics_settings)
        logger.info("TaskHandler initialized")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_processes()

    @staticmethod
    def coroutine_as_process_target(awaitable_func, *args, **kwargs):
        coroutine = awaitable_func(*args, **kwargs)
        asyncio.run(coroutine)

    def stop_processes(self) -> None:
        self.__stop_task_runner_processes()
        self.__stop_metrics_provider_process()
        logger.info("Stopped worker processes")
        self.queue.put(None)
        self.logger_process.terminate()

    def start_processes(self) -> None:
        logger.info("Starting worker processes")
        freeze_support()
        self.__start_task_runner_processes()
        self.__start_metrics_provider_process()
        logger.info("Started task_runner and metrics_provider processes")

    def join_processes(self) -> None:
        try:
            self.__join_task_runner_processes()
            self.__join_metrics_provider_process()
            logger.info("Joined task_runner and metrics_provider processes")
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt: Stopping all processes")
            self.stop_processes()

    def __create_metrics_provider_process(
        self, metrics_settings: MetricsSettings
    ) -> None:
        if metrics_settings is None:
            self.metrics_provider_process = None
            return
        self.metrics_provider_process = Process(
            target=self.coroutine_as_process_target,
            args=(AsyncMetricsCollector.provide_metrics, metrics_settings),
        )
        logger.info(
            "Created MetricsProvider process pid: %s", self.metrics_provider_process.pid
        )

    def __create_task_runner_processes(
        self,
        workers: List[WorkerInterface],
        configuration: Configuration,
        metrics_settings: MetricsSettings,
    ) -> None:
        self.task_runner_processes = []
        for worker in workers:
            self.__create_task_runner_process(worker, configuration, metrics_settings)

    def __create_task_runner_process(
        self,
        worker: WorkerInterface,
        configuration: Configuration,
        metrics_settings: MetricsSettings,
    ) -> None:
        task_runner = AsyncTaskRunner(worker, configuration, metrics_settings)
        process = Process(
            target=self.coroutine_as_process_target, args=(task_runner.run,)
        )
        self.task_runner_processes.append(process)

    def __start_metrics_provider_process(self):
        if self.metrics_provider_process is None:
            return
        self.metrics_provider_process.start()
        logger.info(
            "Started MetricsProvider process with pid: %s",
            self.metrics_provider_process.pid,
        )

    def __start_task_runner_processes(self):
        for task_runner_process in self.task_runner_processes:
            task_runner_process.start()
            logger.debug(
                "Started TaskRunner process with pid: %s", task_runner_process.pid
            )
        logger.info("Started %s TaskRunner processes", len(self.task_runner_processes))

    def __join_metrics_provider_process(self):
        if self.metrics_provider_process is None:
            return
        self.metrics_provider_process.join()
        logger.info(
            "Joined MetricsProvider process with pid: %s",
            self.metrics_provider_process.pid,
        )

    def __join_task_runner_processes(self):
        for task_runner_process in self.task_runner_processes:
            task_runner_process.join()
        logger.info("Joined %s TaskRunner processes", len(self.task_runner_processes))

    def __stop_metrics_provider_process(self):
        self.__stop_process(self.metrics_provider_process)
        logger.info(
            "Stopped MetricsProvider process",
        )

    def __stop_task_runner_processes(self):
        for task_runner_process in self.task_runner_processes:
            self.__stop_process(task_runner_process)
        logger.info("Stopped %s TaskRunner processes", len(self.task_runner_processes))

    def __stop_process(self, process: Process):
        if process is None:
            return
        try:
            logger.debug("Terminating process: %s", process.pid)
            process.terminate()
        except Exception as e:
            logger.error("Failed to terminate process: %s, reason: %s", process.pid, e)
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
    c_logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))

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
