from __future__ import annotations
import asyncio
import atexit
import dataclasses
import inspect
import logging
import threading
import time
import traceback
from copy import deepcopy
from typing import Any, Callable, Union, Optional

from typing_extensions import Self

from conductor.client.automator import utils
from conductor.client.automator.utils import convert_from_dict_or_list
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models import TaskExecLog
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.exception import NonRetryableException
from conductor.client.worker.worker_interface import WorkerInterface, DEFAULT_POLLING_INTERVAL

ExecuteTaskFunction = Callable[
    [
        Union[Task, object]
    ],
    Union[TaskResult, object]
]

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


class BackgroundEventLoop:
    """Manages a persistent asyncio event loop running in a background thread.

    This avoids the expensive overhead of starting/stopping an event loop
    for each async task execution.

    Thread-safe singleton implementation that works across threads and
    handles edge cases like multiprocessing, exceptions, and cleanup.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Thread-safe initialization check
        with self._lock:
            if self._initialized:
                return

            self._loop = None
            self._thread = None
            self._loop_ready = threading.Event()
            self._shutdown = False
            self._loop_started = False
            self._initialized = True

        # Register cleanup on exit - only register once
        atexit.register(self._cleanup)

    def _start_loop(self):
        """Start the background event loop in a daemon thread."""
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="BackgroundEventLoop"
        )
        self._thread.start()

        # Wait for loop to actually start (with timeout)
        if not self._loop_ready.wait(timeout=5.0):
            logger.error("Background event loop failed to start within 5 seconds")
            raise RuntimeError("Failed to start background event loop")

        logger.debug("Background event loop started")

    def _run_loop(self):
        """Run the event loop in the background thread."""
        asyncio.set_event_loop(self._loop)
        try:
            # Signal that loop is ready
            self._loop_ready.set()
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"Background event loop encountered error: {e}")
        finally:
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()

                # Run loop briefly to process cancellations
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                logger.warning(f"Error cancelling pending tasks: {e}")
            finally:
                self._loop.close()

    def run_coroutine(self, coro):
        """Run a coroutine in the background event loop and wait for the result.

        Args:
            coro: The coroutine to run

        Returns:
            The result of the coroutine

        Raises:
            Exception: Any exception raised by the coroutine
            TimeoutError: If coroutine execution exceeds 300 seconds
        """
        # Lazy initialization: start the loop only when first coroutine is submitted
        if not self._loop_started:
            with self._lock:
                # Double-check pattern to avoid race condition
                if not self._loop_started:
                    if self._shutdown:
                        logger.warning("Background loop is shut down, falling back to asyncio.run()")
                        try:
                            return asyncio.run(coro)
                        except RuntimeError as e:
                            logger.error(f"Cannot run coroutine: {e}")
                            coro.close()
                            raise
                    self._start_loop()
                    self._loop_started = True

        # Check if we're shutting down or loop is not available
        if self._shutdown or not self._loop or self._loop.is_closed():
            logger.warning("Background loop not available, falling back to asyncio.run()")
            # Close the coroutine to avoid "coroutine was never awaited" warning
            try:
                return asyncio.run(coro)
            except RuntimeError as e:
                # If we're already in an event loop, we can't use asyncio.run()
                logger.error(f"Cannot run coroutine: {e}")
                coro.close()
                raise

        if not self._loop.is_running():
            logger.warning("Background loop not running, falling back to asyncio.run()")
            try:
                return asyncio.run(coro)
            except RuntimeError as e:
                logger.error(f"Cannot run coroutine: {e}")
                coro.close()
                raise

        try:
            # Submit the coroutine to the background loop and wait for result
            # Use timeout to prevent indefinite blocking
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            # 300 second timeout (5 minutes) - tasks should complete faster
            return future.result(timeout=300)
        except TimeoutError:
            logger.error("Coroutine execution timed out after 300 seconds")
            future.cancel()
            raise
        except Exception as e:
            # Propagate exceptions from the coroutine
            logger.debug(f"Exception in coroutine: {type(e).__name__}: {e}")
            raise

    def _cleanup(self):
        """Stop the background event loop.

        Called automatically on program exit via atexit.
        Thread-safe and idempotent.
        """
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True

        # Only cleanup if loop was actually started
        if not self._loop_started:
            return

        if self._loop and self._loop.is_running():
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception as e:
                logger.warning(f"Error stopping loop: {e}")

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                logger.warning("Background event loop thread did not terminate within 5 seconds")

        logger.debug("Background event loop stopped")


def is_callable_input_parameter_a_task(callable: ExecuteTaskFunction, object_type: Any) -> bool:
    parameters = inspect.signature(callable).parameters
    if len(parameters) != 1:
        return False
    parameter = parameters[next(iter(parameters.keys()))]
    return parameter.annotation == object_type or parameter.annotation == parameter.empty or parameter.annotation is object  # noqa: PLR1714


def is_callable_return_value_of_type(callable: ExecuteTaskFunction, object_type: Any) -> bool:
    return_annotation = inspect.signature(callable).return_annotation
    return return_annotation == object_type


class Worker(WorkerInterface):
    def __init__(self,
                 task_definition_name: str,
                 execute_function: ExecuteTaskFunction,
                 poll_interval: Optional[float] = None,
                 domain: Optional[str] = None,
                 worker_id: Optional[str] = None,
                 thread_count: int = 1,
                 register_task_def: bool = False,
                 poll_timeout: int = 100,
                 lease_extend_enabled: bool = True
                 ) -> Self:
        super().__init__(task_definition_name)
        self.api_client = ApiClient()
        if poll_interval is None:
            self.poll_interval = DEFAULT_POLLING_INTERVAL
        else:
            self.poll_interval = deepcopy(poll_interval)
        self.domain = deepcopy(domain)
        if worker_id is None:
            self.worker_id = deepcopy(super().get_identity())
        else:
            self.worker_id = deepcopy(worker_id)
        self.execute_function = deepcopy(execute_function)
        self.thread_count = thread_count
        self.register_task_def = register_task_def
        self.poll_timeout = poll_timeout
        self.lease_extend_enabled = lease_extend_enabled

        # Initialize background event loop for async workers
        self._background_loop = None

    def execute(self, task: Task) -> TaskResult:
        task_input = {}
        task_output = None
        task_result: TaskResult = self.get_task_result_from_task(task)

        try:

            if self._is_execute_function_input_parameter_a_task:
                task_output = self.execute_function(task)
            else:
                params = inspect.signature(self.execute_function).parameters
                for input_name in params:
                    typ = params[input_name].annotation
                    default_value = params[input_name].default
                    if input_name in task.input_data:
                        if typ in utils.simple_types:
                            task_input[input_name] = task.input_data[input_name]
                        else:
                            task_input[input_name] = convert_from_dict_or_list(typ, task.input_data[input_name])
                    elif default_value is not inspect.Parameter.empty:
                        task_input[input_name] = default_value
                    else:
                        task_input[input_name] = None
                task_output = self.execute_function(**task_input)

            # If the function is async (coroutine), run it in the background event loop
            # This avoids the expensive overhead of starting/stopping an event loop per call
            if inspect.iscoroutine(task_output):
                # Lazy-initialize the background loop only when needed
                if self._background_loop is None:
                    self._background_loop = BackgroundEventLoop()
                task_output = self._background_loop.run_coroutine(task_output)

            if isinstance(task_output, TaskResult):
                task_output.task_id = task.task_id
                task_output.workflow_instance_id = task.workflow_instance_id
                return task_output
            # Import here to avoid circular dependency
            from conductor.client.context.task_context import TaskInProgress
            if isinstance(task_output, TaskInProgress):
                # Return TaskInProgress as-is for TaskRunner to handle
                return task_output
            else:
                task_result.status = TaskResultStatus.COMPLETED
                task_result.output_data = task_output

        except NonRetryableException as ne:
            task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

        except Exception as ne:
            logger.error(
                "Error executing task %s with id %s. error = %s",
                task.task_def_name,
                task.task_id,
                traceback.format_exc()
            )

            task_result.logs = [TaskExecLog(
                traceback.format_exc(), task_result.task_id, int(time.time()))]
            task_result.status = TaskResultStatus.FAILED
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

        if dataclasses.is_dataclass(type(task_result.output_data)):
            task_output = dataclasses.asdict(task_result.output_data)
            task_result.output_data = task_output
            return task_result
        if not isinstance(task_result.output_data, dict):
            task_output = task_result.output_data
            try:
                task_result.output_data = self.api_client.sanitize_for_serialization(task_output)
                if not isinstance(task_result.output_data, dict):
                    task_result.output_data = {"result": task_result.output_data}
            except (RecursionError, TypeError, AttributeError) as e:
                # Object cannot be serialized (e.g., httpx.Response, requests.Response)
                # Convert to string representation with helpful error message
                logger.warning(
                    "Task output of type %s could not be serialized: %s. "
                    "Converting to string. Consider returning serializable data "
                    "(e.g., response.json() instead of response object).",
                    type(task_output).__name__,
                    str(e)[:100]
                )
                task_result.output_data = {
                    "result": str(task_output),
                    "type": type(task_output).__name__,
                    "error": "Object could not be serialized. Please return JSON-serializable data."
                }

        return task_result

    def get_identity(self) -> str:
        return self.worker_id

    @property
    def execute_function(self) -> ExecuteTaskFunction:
        return self._execute_function

    @execute_function.setter
    def execute_function(self, execute_function: ExecuteTaskFunction) -> None:
        self._execute_function = execute_function
        self._is_execute_function_input_parameter_a_task = is_callable_input_parameter_a_task(
            callable=execute_function,
            object_type=Task,
        )
        self._is_execute_function_return_value_a_task_result = is_callable_return_value_of_type(
            callable=execute_function,
            object_type=TaskResult,
        )
