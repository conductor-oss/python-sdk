from __future__ import annotations
import asyncio
import importlib
import inspect
import logging
import os
import threading
import time
from multiprocessing import Process, freeze_support, Queue, set_start_method
from sys import platform
from typing import List, Optional, Any, Dict

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.automator.async_task_runner import AsyncTaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.event.task_runner_events import TaskRunnerEvent
from conductor.client.event.sync_event_dispatcher import SyncEventDispatcher
from conductor.client.event.sync_listener_register import register_task_runner_listener
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.telemetry.model.metric_documentation import MetricDocumentation
from conductor.client.telemetry.model.metric_label import MetricLabel
from conductor.client.telemetry.model.metric_name import MetricName
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

def _run_sync_worker_process(
        worker: WorkerInterface,
        configuration: Optional[Configuration],
        metrics_settings: Optional[MetricsSettings],
        event_listeners: Optional[List[Any]],
) -> None:
    """Process target: construct TaskRunner after fork/spawn and run forever."""
    task_runner = TaskRunner(worker, configuration, metrics_settings, event_listeners)
    task_runner.run()


def _run_async_worker_process(
        worker: WorkerInterface,
        configuration: Optional[Configuration],
        metrics_settings: Optional[MetricsSettings],
        event_listeners: Optional[List[Any]],
) -> None:
    """Process target: construct AsyncTaskRunner after fork/spawn and run forever."""
    async_task_runner = AsyncTaskRunner(worker, configuration, metrics_settings, event_listeners)
    asyncio.run(async_task_runner.run())


def register_decorated_fn(name: str, poll_interval: int, domain: str, worker_id: str, func,
                         thread_count: int = 1, register_task_def: bool = False,
                         poll_timeout: int = 100, lease_extend_enabled: bool = False, task_def: Optional['TaskDef'] = None,
                         overwrite_task_def: bool = True, strict_schema: bool = False):
    logger.debug("decorated %s", name)
    _decorated_functions[(name, domain)] = {
        "func": func,
        "poll_interval": poll_interval,
        "domain": domain,
        "worker_id": worker_id,
        "thread_count": thread_count,
        "register_task_def": register_task_def,
        "poll_timeout": poll_timeout,
        "lease_extend_enabled": lease_extend_enabled,
        "task_def": task_def,
        "overwrite_task_def": overwrite_task_def,
        "strict_schema": strict_schema
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
            thread_count=record.get("thread_count", 1),
            register_task_def=record.get("register_task_def", False),
            poll_timeout=record.get("poll_timeout", 100),
            lease_extend_enabled=record.get("lease_extend_enabled", False),
            paused=False,  # Always default to False, only env vars can set to True
            task_def_template=record.get("task_def"),  # Optional TaskDef configuration
            overwrite_task_def=record.get("overwrite_task_def", True),
            strict_schema=record.get("strict_schema", False)
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
        - Each process continuously polls for tasks
        - Execution mode automatically selected based on function signature

    Sync Workers (def):
        - Use TaskRunner with ThreadPoolExecutor
        - Tasks execute in thread pool (controlled by thread_count parameter)
        - Best for: CPU-bound tasks, blocking I/O

    Async Workers (async def):
        - Use AsyncTaskRunner with pure async/await
        - Tasks execute in single event loop (zero thread overhead)
        - Async polling, execution, and updates (httpx.AsyncClient)
        - 10-100x better concurrency for I/O-bound workloads
        - Automatically detected - no configuration needed

    Usage:
        # Default configuration
        handler = TaskHandler(configuration=config)
        handler.start_processes()
        handler.join_processes()

        # Context manager (recommended)
        with TaskHandler(configuration=config) as handler:
            handler.start_processes()
            handler.join_processes()

    Worker Examples:
        # Async worker (automatically uses AsyncTaskRunner)
        @worker_task(task_definition_name='fetch_data', thread_count=50)
        async def fetch_data(url: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
            return {'data': response.json()}

        # Sync worker (automatically uses TaskRunner)
        @worker_task(task_definition_name='process_data', thread_count=4)
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
            event_listeners: Optional[List] = None,
            monitor_processes: bool = True,
            restart_on_failure: bool = True,
            monitor_interval_seconds: float = 5.0,
            restart_backoff_seconds: float = 1.0,
            restart_backoff_max_seconds: float = 60.0,
            restart_max_attempts: int = 0
    ):
        workers = workers or []
        self.logger_process, self.queue = _setup_logging_queue(configuration)
        self._configuration = configuration
        self._metrics_settings = metrics_settings

        # Set prometheus multiprocess directory BEFORE any worker processes start
        # This must be done before prometheus_client is imported in worker processes
        if metrics_settings is not None:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = metrics_settings.directory
            logger.info(f"Set PROMETHEUS_MULTIPROC_DIR={metrics_settings.directory}")

        # Store event listeners to pass to each worker process
        self.event_listeners = event_listeners or []
        if self.event_listeners:
            for listener in self.event_listeners:
                logger.info(f"Will register event listener in each worker process: {listener.__class__.__name__}")

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
                    'lease_extend_enabled': record.get("lease_extend_enabled", True),
                    'overwrite_task_def': record.get("overwrite_task_def", True),
                    'strict_schema': record.get("strict_schema", False)
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
                    lease_extend_enabled=resolved_config['lease_extend_enabled'],
                    task_def_template=record.get("task_def"),  # Pass TaskDef configuration
                    overwrite_task_def=resolved_config.get('overwrite_task_def', True),
                    strict_schema=resolved_config.get('strict_schema', False))
                logger.debug("created worker with name=%s and domain=%s", task_def_name, resolved_config['domain'])
                workers.append(worker)

        self.__create_task_runner_processes(workers, configuration, metrics_settings)
        self.__create_metrics_provider_process(metrics_settings)

        # Initialize worker restart counter directly using prometheus_client (if metrics enabled).
        # We use prometheus_client directly in the parent process instead of MetricsCollector
        # to avoid registry confusion between parent and worker processes.
        self._worker_restart_counter = None
        if metrics_settings is not None:
            try:
                from prometheus_client import Counter
                self._worker_restart_counter = Counter(
                    name='worker_restart_total',
                    documentation='Number of times TaskHandler restarted a worker subprocess',
                    labelnames=['taskType']
                )
                logger.debug("Initialized worker_restart_total counter in parent process")
            except Exception as e:
                logger.debug("Failed to initialize worker restart counter: %s", e)

        # Optional supervision: monitor worker processes and (optionally) restart on failure.
        self.monitor_processes = monitor_processes
        self.restart_on_failure = restart_on_failure
        self.monitor_interval_seconds = monitor_interval_seconds
        self.restart_backoff_seconds = restart_backoff_seconds
        self.restart_backoff_max_seconds = restart_backoff_max_seconds
        self.restart_max_attempts = restart_max_attempts
        self._monitor_stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._restart_counts: List[int] = [0 for _ in self.workers]
        self._next_restart_at: List[float] = [0.0 for _ in self.workers]
        # Lock to protect process list during concurrent access (monitor thread vs main thread)
        self._process_lock = threading.Lock()
        logger.info("TaskHandler initialized")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_processes()

    def stop_processes(self) -> None:
        self._monitor_stop_event.set()
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        # Lock to prevent race conditions with monitor thread
        with self._process_lock:
            self.__stop_task_runner_processes()
            self.__stop_metrics_provider_process()
        logger.info("Stopped worker processes...")
        self.queue.put(None)
        self.logger_process.terminate()

    def start_processes(self) -> None:
        logger.info("Starting worker processes...")
        freeze_support()
        self._monitor_stop_event.clear()
        self.__start_task_runner_processes()
        self.__start_metrics_provider_process()
        self.__start_monitor_thread()
        logger.info("Started all processes")

    def join_processes(self) -> None:
        self.__join_task_runner_processes()
        self.__join_metrics_provider_process()
        logger.info("Joined all processes")

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
        # Detect if worker function is async
        # For function-based workers (@worker_task), check execute_function
        # For class-based workers, check execute method
        is_async_worker = False
        if hasattr(worker, 'execute_function'):
            # Function-based worker (created with @worker_task decorator)
            is_async_worker = inspect.iscoroutinefunction(worker.execute_function)
        else:
            # Class-based worker (implements WorkerInterface)
            is_async_worker = inspect.iscoroutinefunction(worker.execute)

        if is_async_worker:
            process = Process(
                target=_run_async_worker_process,
                args=(worker, configuration, metrics_settings, self.event_listeners)
            )
            logger.debug(f"Created AsyncTaskRunner process for async worker: {worker.get_task_definition_name()}")
        else:
            process = Process(
                target=_run_sync_worker_process,
                args=(worker, configuration, metrics_settings, self.event_listeners)
            )
            logger.debug(f"Created TaskRunner process for sync worker: {worker.get_task_definition_name()}")

        self.task_runner_processes.append(process)

    def __start_monitor_thread(self) -> None:
        if not self.monitor_processes:
            return
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return
        self._monitor_thread = threading.Thread(target=self.__monitor_loop, name="TaskHandlerMonitor", daemon=True)
        self._monitor_thread.start()
        logger.info(
            "TaskHandler monitor started (restart_on_failure=%s, interval=%ss)",
            self.restart_on_failure,
            self.monitor_interval_seconds
        )

    def __monitor_loop(self) -> None:
        while not self._monitor_stop_event.is_set():
            try:
                self.__check_and_restart_processes()
            except Exception as e:
                logger.debug("TaskHandler monitor loop error: %s", e)
            # Use Event.wait() so stop_processes can wake the thread immediately.
            self._monitor_stop_event.wait(self.monitor_interval_seconds)

    def __check_and_restart_processes(self) -> None:
        if self._monitor_stop_event.is_set():
            return
        # Lock to prevent race conditions with stop_processes
        with self._process_lock:
            for i, process in enumerate(list(self.task_runner_processes)):
                if process is None:
                    continue
                if process.is_alive():
                    continue
                exitcode = process.exitcode
                if exitcode is None:
                    continue
                worker = self.workers[i] if i < len(self.workers) else None
                worker_name = worker.get_task_definition_name() if worker is not None else f"worker[{i}]"
                logger.warning("Worker process exited (worker=%s, pid=%s, exitcode=%s)", worker_name, process.pid, exitcode)
                if not self.restart_on_failure:
                    continue
                self.__restart_worker_process(i)

    def __restart_worker_process(self, index: int) -> None:
        if self._monitor_stop_event.is_set():
            return
        if index >= len(self.workers) or index >= len(self.task_runner_processes):
            return

        # Enforce max attempts if configured (0 = unlimited)
        if self.restart_max_attempts > 0 and self._restart_counts[index] >= self.restart_max_attempts:
            worker = self.workers[index]
            logger.error(
                "Not restarting worker process: max restart attempts reached (worker=%s, attempts=%s)",
                worker.get_task_definition_name(),
                self._restart_counts[index]
            )
            return

        now = time.time()
        if now < self._next_restart_at[index]:
            return

        worker = self.workers[index]
        attempt = self._restart_counts[index] + 1

        # Exponential backoff per-worker to avoid tight crash loops
        backoff = min(self.restart_backoff_seconds * (2 ** self._restart_counts[index]), self.restart_backoff_max_seconds)
        self._next_restart_at[index] = now + backoff

        try:
            # Reap the old process (avoid accumulating zombies on repeated restarts).
            old_process = self.task_runner_processes[index]
            old_pid = getattr(old_process, "pid", None)
            try:
                if old_process is not None and old_process.exitcode is not None:
                    # Give process a bit more time to clean up
                    old_process.join(timeout=0.5)
                    try:
                        old_process.close()
                        logger.debug("Cleaned up old worker process (worker=%s, pid=%s)", worker.get_task_definition_name(), old_pid)
                    except Exception as close_err:
                        logger.debug("Failed to close old worker process (worker=%s, pid=%s): %s",
                                   worker.get_task_definition_name(), old_pid, close_err)
            except Exception as join_err:
                logger.debug("Failed to join old worker process (worker=%s, pid=%s): %s",
                           worker.get_task_definition_name(), old_pid, join_err)

            new_process = self.__build_process_for_worker(worker)
            self.task_runner_processes[index] = new_process
            new_process.start()
            self._restart_counts[index] = attempt
            self.__inc_worker_restart_metric(worker.get_task_definition_name())
            logger.info(
                "Restarted worker process (worker=%s, attempt=%s, old_pid=%s, new_pid=%s, next_backoff=%ss)",
                worker.get_task_definition_name(),
                attempt,
                old_pid,
                new_process.pid,
                backoff
            )
        except Exception as e:
            logger.error("Failed to restart worker process (worker=%s): %s", worker.get_task_definition_name(), e)

    def __inc_worker_restart_metric(self, task_type: str) -> None:
        """Best-effort counter increment for worker subprocess restarts."""
        if self._worker_restart_counter is None:
            return

        try:
            # Increment the prometheus counter directly.
            # This writes to the shared multiprocess metrics directory.
            self._worker_restart_counter.labels(taskType=task_type).inc()
        except Exception as e:
            # Metrics should never break worker supervision.
            logger.debug("Failed to increment worker_restart metric: %s", e)

    def __build_process_for_worker(self, worker: WorkerInterface) -> Process:
        """Create a new worker process for the given worker (used for initial start + restarts)."""
        # Detect if worker function is async
        if hasattr(worker, 'execute_function'):
            is_async_worker = inspect.iscoroutinefunction(worker.execute_function)
        else:
            is_async_worker = inspect.iscoroutinefunction(worker.execute)

        if is_async_worker:
            return Process(
                target=_run_async_worker_process,
                args=(worker, self._configuration, self._metrics_settings, self.event_listeners)
            )
        return Process(
            target=_run_sync_worker_process,
            args=(worker, self._configuration, self._metrics_settings, self.event_listeners)
        )

    def get_worker_process_status(self) -> List[Dict[str, Any]]:
        """Return basic worker process status for health checks / observability."""
        # Lock to ensure consistent snapshot of process state
        with self._process_lock:
            statuses: List[Dict[str, Any]] = []
            for i, worker in enumerate(self.workers):
                process = self.task_runner_processes[i] if i < len(self.task_runner_processes) else None
                statuses.append({
                    "worker": worker.get_task_definition_name(),
                    "pid": getattr(process, "pid", None),
                    "alive": process.is_alive() if process is not None else False,
                    "exitcode": getattr(process, "exitcode", None),
                    "restart_count": self._restart_counts[i] if i < len(self._restart_counts) else 0,
                })
            return statuses

    def is_healthy(self) -> bool:
        """True if all worker processes are alive."""
        return all(p is not None and p.is_alive() for p in self.task_runner_processes)

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
            paused_status = "PAUSED" if getattr(worker, "paused", False) else "ACTIVE"
            logger.info("Started worker '%s' [%s] (pid=%s)", worker.get_task_definition_name(), paused_status, task_runner_process.pid)
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
            # Wait for graceful termination
            process.join(timeout=5.0)
            if process.is_alive():
                logger.warning("Process %s did not terminate within 5 seconds, killing...", process.pid)
                process.kill()
                process.join(timeout=1.0)  # Wait after kill too
                if process.is_alive():
                    logger.error("Process %s could not be killed", process.pid)
        except Exception as e:
            logger.debug("Failed to terminate process: %s, reason: %s", process.pid, e)
            try:
                process.kill()
                process.join(timeout=1.0)
                logger.debug("Killed process: %s", process.pid)
            except Exception as kill_error:
                logger.error("Failed to kill process: %s, reason: %s", process.pid, kill_error)


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
