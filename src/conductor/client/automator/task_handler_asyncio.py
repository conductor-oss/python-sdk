from __future__ import annotations
import asyncio
import importlib
import logging
from typing import List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_interface import WorkerInterface

# Import decorator registry from existing module
from conductor.client.automator.task_handler import (
    _decorated_functions,
    register_decorated_fn
)

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(__name__)
)


class TaskHandlerAsyncIO:
    """
    AsyncIO-based task handler that manages worker coroutines instead of processes.

    Advantages over multiprocessing TaskHandler:
    - Lower memory footprint (single process, ~60-90% less memory for 10+ workers)
    - Efficient for I/O-bound tasks (HTTP calls, DB queries)
    - Simpler debugging and profiling (single process)
    - Native Python concurrency primitives (async/await)
    - Lower CPU overhead for context switching
    - Better for high-concurrency scenarios (100s-1000s of workers)

    Disadvantages:
    - CPU-bound tasks still limited by Python GIL
    - Less fault isolation (exception in one coroutine can affect others)
    - Shared memory requires careful state management
    - Requires asyncio-compatible libraries (httpx instead of requests)

    When to Use:
    - I/O-bound tasks (HTTP API calls, database queries, file I/O)
    - High worker count (10+)
    - Memory-constrained environments
    - Simple debugging requirements
    - Comfortable with async/await syntax

    When to Use Multiprocessing Instead:
    - CPU-bound tasks (image processing, ML inference)
    - Absolute fault isolation required
    - Complex shared state
    - Battle-tested stability needed

    Usage Example:
        # Basic usage
        handler = TaskHandlerAsyncIO(configuration=config)
        await handler.start()
        # ... application runs ...
        await handler.stop()

        # Context manager (recommended)
        async with TaskHandlerAsyncIO(configuration=config) as handler:
            # Workers automatically started
            await handler.wait()  # Block until stopped
            # Workers automatically stopped

        # With custom workers
        workers = [
            Worker(task_definition_name='task1', execute_function=my_func1),
            Worker(task_definition_name='task2', execute_function=my_func2),
        ]
        handler = TaskHandlerAsyncIO(workers=workers, configuration=config)
    """

    def __init__(
        self,
        workers: Optional[List[WorkerInterface]] = None,
        configuration: Optional[Configuration] = None,
        metrics_settings: Optional[MetricsSettings] = None,
        scan_for_annotated_workers: bool = True,
        import_modules: Optional[List[str]] = None,
        use_v2_api: bool = True
    ):
        if httpx is None:
            raise ImportError(
                "httpx is required for AsyncIO task handler. "
                "Install with: pip install httpx"
            )

        self.configuration = configuration or Configuration()
        self.metrics_settings = metrics_settings
        self.use_v2_api = use_v2_api

        # Shared HTTP client for all workers (connection pooling)
        self.http_client = httpx.AsyncClient(
            base_url=self.configuration.host,
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )

        # Discover workers
        workers = workers or []

        # Import modules to trigger decorators
        importlib.import_module("conductor.client.http.models.task")
        importlib.import_module("conductor.client.worker.worker_task")

        if import_modules is not None:
            for module in import_modules:
                logger.info("Loading module %s", module)
                importlib.import_module(module)

        elif not isinstance(workers, list):
            workers = [workers]

        # Scan decorated functions
        if scan_for_annotated_workers:
            for (task_def_name, domain), record in _decorated_functions.items():
                fn = record["func"]
                worker_id = record["worker_id"]
                poll_interval = record["poll_interval"]
                thread_count = record.get("thread_count", 1)
                register_task_def = record.get("register_task_def", False)
                poll_timeout = record.get("poll_timeout", 100)
                lease_extend_enabled = record.get("lease_extend_enabled", True)

                worker = Worker(
                    task_definition_name=task_def_name,
                    execute_function=fn,
                    worker_id=worker_id,
                    domain=domain,
                    poll_interval=poll_interval,
                    thread_count=thread_count,
                    register_task_def=register_task_def,
                    poll_timeout=poll_timeout,
                    lease_extend_enabled=lease_extend_enabled
                )
                logger.info("Created worker with name=%s and domain=%s", task_def_name, domain)
                workers.append(worker)

        # Create task runners
        self.task_runners = []
        for worker in workers:
            task_runner = TaskRunnerAsyncIO(
                worker=worker,
                configuration=self.configuration,
                metrics_settings=self.metrics_settings,
                http_client=self.http_client,
                use_v2_api=self.use_v2_api
            )
            self.task_runners.append(task_runner)

        # Coroutine tasks
        self._worker_tasks: List[asyncio.Task] = []
        self._metrics_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("TaskHandlerAsyncIO initialized with %d workers", len(self.task_runners))

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Async context manager exit"""
        await self.stop()

    async def start(self) -> None:
        """
        Start all worker coroutines.

        This creates an asyncio.Task for each worker and starts them concurrently.
        Workers will poll for tasks, execute them, and update results in an infinite loop.
        """
        if self._running:
            logger.warning("TaskHandlerAsyncIO already running")
            return

        self._running = True
        logger.info("Starting AsyncIO workers...")

        # Start worker coroutines
        for task_runner in self.task_runners:
            task = asyncio.create_task(
                task_runner.run(),
                name=f"worker-{task_runner.worker.get_task_definition_name()}"
            )
            self._worker_tasks.append(task)

        # Start metrics coroutine (if configured)
        if self.metrics_settings is not None:
            self._metrics_task = asyncio.create_task(
                self._provide_metrics(),
                name="metrics-provider"
            )

        logger.info("Started %d AsyncIO worker tasks", len(self._worker_tasks))

    async def stop(self) -> None:
        """
        Stop all worker coroutines gracefully.

        This signals all workers to stop polling, cancels their tasks,
        and waits for them to complete any in-flight work.
        """
        if not self._running:
            return

        self._running = False
        logger.info("Stopping AsyncIO workers...")

        # Signal workers to stop
        for task_runner in self.task_runners:
            await task_runner.stop()

        # Cancel all tasks
        for task in self._worker_tasks:
            task.cancel()

        if self._metrics_task is not None:
            self._metrics_task.cancel()

        # Wait for cancellation to complete (with exceptions suppressed)
        all_tasks = self._worker_tasks.copy()
        if self._metrics_task is not None:
            all_tasks.append(self._metrics_task)

        # Add shutdown timeout to guarantee completion within 30 seconds
        try:
            await asyncio.wait_for(
                asyncio.gather(*all_tasks, return_exceptions=True),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning("Shutdown timeout - tasks did not complete within 30 seconds")

        # Close HTTP client
        await self.http_client.aclose()

        logger.info("Stopped all AsyncIO workers")

    async def wait(self) -> None:
        """
        Wait for all workers to complete.

        This blocks until stop() is called or an exception occurs in any worker.
        Typically used in the main loop to keep the application running.

        Example:
            async with TaskHandlerAsyncIO(config) as handler:
                try:
                    await handler.wait()  # Blocks here
                except KeyboardInterrupt:
                    print("Shutting down...")
        """
        try:
            tasks = self._worker_tasks.copy()
            if self._metrics_task is not None:
                tasks.append(self._metrics_task)

            # Wait for all tasks (will block until stopped or exception)
            await asyncio.gather(*tasks)

        except asyncio.CancelledError:
            logger.info("Worker tasks cancelled")

        except Exception as e:
            logger.error("Error in worker tasks: %s", e)
            raise

    async def join_tasks(self) -> None:
        """
        Alias for wait() to match multiprocessing API.

        This provides compatibility with the multiprocessing TaskHandler interface.
        """
        await self.wait()

    async def _provide_metrics(self) -> None:
        """
        Coroutine to periodically write Prometheus metrics.

        Runs in a separate task and writes metrics to a file at regular intervals.
        """
        if self.metrics_settings is None:
            return

        import os
        from prometheus_client import CollectorRegistry, write_to_textfile
        from prometheus_client.multiprocess import MultiProcessCollector

        OUTPUT_FILE_PATH = os.path.join(
            self.metrics_settings.directory,
            self.metrics_settings.file_name
        )

        registry = CollectorRegistry()
        MultiProcessCollector(registry)

        try:
            while self._running:
                # Run file I/O in executor to prevent blocking event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,  # Use default thread pool for file I/O
                    write_to_textfile,
                    OUTPUT_FILE_PATH,
                    registry
                )
                await asyncio.sleep(self.metrics_settings.update_interval)

        except asyncio.CancelledError:
            logger.info("Metrics provider cancelled")

        except Exception as e:
            logger.error("Error in metrics provider: %s", e)


# Convenience function for running workers in asyncio
async def run_workers_async(
    configuration: Optional[Configuration] = None,
    import_modules: Optional[List[str]] = None,
    stop_after_seconds: Optional[int] = None
) -> None:
    """
    Convenience function to run workers with asyncio.

    Args:
        configuration: Conductor configuration
        import_modules: List of modules to import (for worker discovery)
        stop_after_seconds: Optional timeout (for testing)

    Example:
        # Run forever
        asyncio.run(run_workers_async(config))

        # Run for 60 seconds
        asyncio.run(run_workers_async(config, stop_after_seconds=60))
    """
    async with TaskHandlerAsyncIO(
        configuration=configuration,
        import_modules=import_modules
    ) as handler:
        try:
            if stop_after_seconds is not None:
                # Run with timeout
                await asyncio.wait_for(
                    handler.wait(),
                    timeout=stop_after_seconds
                )
            else:
                # Run indefinitely
                await handler.wait()

        except asyncio.TimeoutError:
            logger.info("Worker timeout reached, shutting down")

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt, shutting down")
