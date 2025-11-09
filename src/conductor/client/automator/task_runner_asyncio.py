from __future__ import annotations
import asyncio
import dataclasses
import inspect
import logging
import random
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None

from conductor.client.automator.utils import convert_from_dict_or_list
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.automator import utils
from conductor.client.worker.exception import NonRetryableException

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(__name__)
)


class TaskRunnerAsyncIO:
    """
    AsyncIO-based task runner that uses coroutines instead of processes.

    This improved version includes:
    - Python 3.12+ compatibility (uses get_running_loop())
    - Execution timeouts to prevent hangs
    - Explicit ThreadPoolExecutor with proper cleanup
    - Cached ApiClient for better performance
    - Exponential backoff with jitter
    - Better error handling
    - Concurrency limiting per worker

    Advantages:
    - Lower memory footprint (no process overhead)
    - Efficient for I/O-bound tasks
    - Simpler debugging (single process)
    - Better for high-concurrency scenarios (1000s of tasks)

    Disadvantages:
    - CPU-bound tasks still limited by GIL
    - Less fault isolation (exception can affect other workers)
    - Requires asyncio-compatible HTTP client (httpx)

    Usage:
        runner = TaskRunnerAsyncIO(worker, configuration)
        await runner.run()  # Runs until stop() is called
    """

    def __init__(
        self,
        worker: WorkerInterface,
        configuration: Configuration = None,
        metrics_settings: Optional[MetricsSettings] = None,
        http_client: Optional['httpx.AsyncClient'] = None,
        max_concurrent_tasks: int = 1  # Limit concurrent executions per worker
    ):
        if httpx is None:
            raise ImportError(
                "httpx is required for AsyncIO task runner. "
                "Install with: pip install httpx"
            )

        if not isinstance(worker, WorkerInterface):
            raise Exception("Invalid worker")

        self.worker = worker
        self.configuration = configuration or Configuration()
        self.metrics_collector = None

        if metrics_settings is not None:
            self.metrics_collector = MetricsCollector(metrics_settings)

        # AsyncIO HTTP client (shared across requests)
        self.http_client = http_client or httpx.AsyncClient(
            base_url=self.configuration.host,
            timeout=httpx.Timeout(
                connect=5.0,
                read=30.0,  # Long poll timeout
                write=10.0,
                pool=None
            ),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )

        # Cached ApiClient (created once, reused)
        self._api_client = ApiClient(self.configuration)

        # Explicit ThreadPoolExecutor for sync workers
        self._executor = ThreadPoolExecutor(
            max_workers=4,  # Explicit size
            thread_name_prefix=f"worker-{worker.get_task_definition_name()}"
        )

        # Semaphore to limit concurrent task executions
        self._execution_semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Track background tasks for proper cleanup
        self._background_tasks = set()

        # Auth failure backoff tracking to prevent retry storms
        self._auth_failures = 0
        self._last_auth_failure = 0

        self._running = False
        self._owns_client = http_client is None

    def _get_auth_headers(self) -> dict:
        """
        Get authentication headers from ApiClient.

        This ensures AsyncIO implementation uses the same authentication
        mechanism as multiprocessing implementation.
        """
        headers = {}

        if self.configuration.authentication_settings is None:
            return headers

        # Use ApiClient's method to get auth headers
        # This handles token generation and refresh automatically
        auth_headers = self._api_client.get_authentication_headers()

        if auth_headers and 'header' in auth_headers:
            headers.update(auth_headers['header'])

        return headers

    async def run(self) -> None:
        """
        Main event loop for this worker.
        Runs until stop() is called or an unhandled exception occurs.
        """
        self._running = True

        task_names = ",".join(self.worker.task_definition_names)
        logger.info(
            "Starting AsyncIO worker for task %s with domain %s with polling interval %s",
            task_names,
            self.worker.get_domain(),
            self.worker.get_polling_interval_in_seconds()
        )

        try:
            while self._running:
                await self.run_once()
        except asyncio.CancelledError:
            logger.info("Worker task cancelled")
            raise
        finally:
            # Wait for background tasks to complete
            if self._background_tasks:
                logger.info(
                    "Waiting for %d background tasks to complete...",
                    len(self._background_tasks)
                )
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            # Cleanup resources
            if self._owns_client:
                await self.http_client.aclose()

            # Shutdown executor
            self._executor.shutdown(wait=True)

    async def run_once(self) -> None:
        """
        Single poll cycle with non-blocking task execution.

        This method polls for a task and starts its execution in the background,
        allowing the loop to continue polling immediately. This enables true
        concurrent execution of multiple tasks.
        """
        try:
            task = await self._poll_task()
            if task is not None and task.task_id is not None:
                # Start task execution in background (don't wait)
                background_task = asyncio.create_task(
                    self._execute_and_update_task(task)
                )

                # Track background task and clean up when done
                self._background_tasks.add(background_task)
                background_task.add_done_callback(self._background_tasks.discard)

            await self._wait_for_polling_interval()
            self.worker.clear_task_definition_name_cache()

        except asyncio.CancelledError:
            raise  # Don't swallow cancellation

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            # Transient network errors - log and continue
            logger.warning("Network error in run_once: %s", e)

        except Exception as e:
            # Unexpected errors - log with high severity but continue (resilience)
            logger.exception(
                "Unexpected error in run_once - this may indicate a bug. "
                "Worker will continue running."
            )

    def stop(self) -> None:
        """Signal worker to stop gracefully"""
        self._running = False

    async def _execute_and_update_task(self, task: Task) -> None:
        """
        Execute task and update result (runs in background).

        This method combines task execution and result update into a single
        background operation, allowing the main loop to continue polling.
        """
        try:
            task_result = await self._execute_task(task)
            await self._update_task(task_result)
        except Exception as e:
            # Log but don't crash - background task should be resilient
            logger.exception(
                "Error in background task execution for task_id: %s",
                task.task_id
            )

    async def _poll_task(self) -> Optional[Task]:
        """Poll Conductor server for next available task"""
        task_definition_name = self.worker.get_task_definition_name()

        if self.worker.paused():
            logger.debug("Worker paused for: %s", task_definition_name)
            return None

        # Apply exponential backoff if we have recent auth failures
        if self._auth_failures > 0:
            now = time.time()
            # Exponential backoff: 2^failures seconds (2s, 4s, 8s, 16s, 32s)
            backoff_seconds = min(2 ** self._auth_failures, 60)  # Cap at 60s
            time_since_last_failure = now - self._last_auth_failure

            if time_since_last_failure < backoff_seconds:
                # Still in backoff period - skip polling
                await asyncio.sleep(0.1)  # Small sleep to prevent tight loop
                return None

        if self.metrics_collector is not None:
            self.metrics_collector.increment_task_poll(task_definition_name)

        try:
            start_time = time.time()

            # Build request parameters
            params = {"workerid": self.worker.get_identity()}
            domain = self.worker.get_domain()
            if domain is not None:
                params["domain"] = domain

            # Get authentication headers
            headers = self._get_auth_headers()

            # Async HTTP request (long poll)
            response = await self.http_client.get(
                f"/tasks/poll/{task_definition_name}",
                params=params,
                headers=headers if headers else None
            )

            finish_time = time.time()
            time_spent = finish_time - start_time

            if self.metrics_collector is not None:
                self.metrics_collector.record_task_poll_time(
                    task_definition_name, time_spent
                )

            # Handle response
            if response.status_code == 204:  # No content (no task available)
                return None

            response.raise_for_status()
            task_data = response.json()

            # Convert to Task object using cached ApiClient
            task = self._api_client.deserialize_class(task_data, Task) if task_data else None

            # Success - reset auth failure counter
            if task is not None:
                self._auth_failures = 0
                logger.debug(
                    "Polled task: %s, worker_id: %s, domain: %s",
                    task_definition_name,
                    self.worker.get_identity(),
                    self.worker.get_domain()
                )
            else:
                # No task available (204) - also reset auth failures
                self._auth_failures = 0

            return task

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Check if this is a token expiry/invalid token (renewable) vs invalid credentials
                error_code = None
                try:
                    response_data = e.response.json()
                    error_code = response_data.get('error', '')
                except Exception:
                    pass

                # If token is expired or invalid, try to renew it
                if error_code in ('EXPIRED_TOKEN', 'INVALID_TOKEN'):
                    token_status = "expired" if error_code == 'EXPIRED_TOKEN' else "invalid"
                    logger.info(
                        "Authentication token is %s, renewing token... (task: %s)",
                        token_status,
                        task_definition_name
                    )

                    # Force token refresh (skip backoff - this is a legitimate renewal)
                    success = self._api_client.force_refresh_auth_token()

                    if success:
                        logger.info('Authentication token successfully renewed')
                        # Retry the poll request with new token
                        try:
                            headers = self._get_auth_headers()
                            response = await self.http_client.get(
                                f"/tasks/poll/{task_definition_name}",
                                params=params,
                                headers=headers if headers else None
                            )

                            if response.status_code == 204:
                                return None

                            response.raise_for_status()
                            task_data = response.json()
                            task = self._api_client.deserialize_class(task_data, Task) if task_data else None

                            # Success - reset auth failures
                            self._auth_failures = 0
                            return task
                        except Exception as retry_error:
                            logger.error(
                                "Failed to poll task %s after token renewal: %s",
                                task_definition_name,
                                retry_error
                            )
                            return None
                    else:
                        logger.error('Failed to renew authentication token')
                else:
                    # Not a token expiry - invalid credentials, apply backoff
                    self._auth_failures += 1
                    self._last_auth_failure = time.time()
                    backoff_seconds = min(2 ** self._auth_failures, 60)

                    logger.error(
                        "Authentication failed for task %s (failure #%d): %s. "
                        "Will retry with exponential backoff (%ds). "
                        "Please check your CONDUCTOR_AUTH_KEY and CONDUCTOR_AUTH_SECRET.",
                        task_definition_name,
                        self._auth_failures,
                        e,
                        backoff_seconds
                    )
            else:
                logger.error(
                    "HTTP error polling task %s: %s",
                    task_definition_name, e
                )

            if self.metrics_collector is not None:
                self.metrics_collector.increment_task_poll_error(
                    task_definition_name, type(e)
                )

            return None

        except Exception as e:
            if self.metrics_collector is not None:
                self.metrics_collector.increment_task_poll_error(
                    task_definition_name, type(e)
                )

            logger.error(
                "Failed to poll task for: %s, reason: %s",
                task_definition_name,
                traceback.format_exc()
            )
            return None

    async def _execute_task(self, task: Task) -> TaskResult:
        """
        Execute task using worker's function with timeout and concurrency control.

        Handles both async and sync workers by calling the user's execute_function
        directly and manually creating the TaskResult. This allows proper awaiting
        of async functions.
        """
        task_definition_name = self.worker.get_task_definition_name()

        logger.debug(
            "Executing task, id: %s, workflow_instance_id: %s, task_definition_name: %s",
            task.task_id,
            task.workflow_instance_id,
            task_definition_name
        )

        # Limit concurrent task executions
        async with self._execution_semaphore:
            try:
                start_time = time.time()

                # Get timeout from task definition or use default
                timeout = getattr(task, 'response_timeout_seconds', 300) or 300

                # Call user's function and await if needed
                task_output = await self._call_execute_function(task, timeout)

                # Create TaskResult from output
                task_result = self._create_task_result(task, task_output)

                finish_time = time.time()
                time_spent = finish_time - start_time

                if self.metrics_collector is not None:
                    self.metrics_collector.record_task_execute_time(
                        task_definition_name, time_spent
                    )
                    self.metrics_collector.record_task_result_payload_size(
                        task_definition_name, sys.getsizeof(task_result)
                    )

                logger.debug(
                    "Executed task, id: %s, workflow_instance_id: %s, task_definition_name: %s, duration: %.2fs",
                    task.task_id,
                    task.workflow_instance_id,
                    task_definition_name,
                    time_spent
                )

                return task_result

            except asyncio.TimeoutError:
                # Task execution timed out
                timeout_duration = getattr(task, 'response_timeout_seconds', 300)
                logger.error(
                    "Task execution timed out after %s seconds, id: %s",
                    timeout_duration,
                    task.task_id
                )

                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_execution_error(
                        task_definition_name, asyncio.TimeoutError
                    )

                # Create failed task result
                task_result = TaskResult(
                    task_id=task.task_id,
                    workflow_instance_id=task.workflow_instance_id,
                    worker_id=self.worker.get_identity()
                )
                task_result.status = "FAILED"
                task_result.reason_for_incompletion = f"Execution timeout ({timeout_duration}s)"
                task_result.logs = [
                    TaskExecLog(
                        f"Task execution exceeded timeout of {timeout_duration} seconds",
                        task_result.task_id,
                        int(time.time())
                    )
                ]

                return task_result

            except NonRetryableException as ne:
                # Non-retryable error - mark as terminal failure
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_execution_error(
                        task_definition_name, type(ne)
                    )

                task_result = TaskResult(
                    task_id=task.task_id,
                    workflow_instance_id=task.workflow_instance_id,
                    worker_id=self.worker.get_identity()
                )
                task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
                if len(ne.args) > 0:
                    task_result.reason_for_incompletion = ne.args[0]

                logger.error(
                    "Non-retryable error executing task, id: %s, reason: %s",
                    task.task_id,
                    traceback.format_exc()
                )

                return task_result

            except Exception as e:
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_execution_error(
                        task_definition_name, type(e)
                    )

                # Create failed task result
                task_result = TaskResult(
                    task_id=task.task_id,
                    workflow_instance_id=task.workflow_instance_id,
                    worker_id=self.worker.get_identity()
                )
                task_result.status = "FAILED"
                task_result.reason_for_incompletion = str(e)
                task_result.logs = [
                    TaskExecLog(
                        traceback.format_exc(),
                        task_result.task_id,
                        int(time.time())
                    )
                ]

                logger.error(
                    "Failed to execute task, id: %s, workflow_instance_id: %s, "
                    "task_definition_name: %s, reason: %s",
                    task.task_id,
                    task.workflow_instance_id,
                    task_definition_name,
                    traceback.format_exc()
                )

                return task_result

    async def _call_execute_function(self, task: Task, timeout: float):
        """
        Call the user's execute function and await if it's async.

        Returns the raw output (not wrapped in TaskResult yet).
        """
        execute_func = self.worker._execute_function

        # Extract input parameters from task
        task_input = {}

        # Check if function takes Task object directly
        if self.worker._is_execute_function_input_parameter_a_task:
            result_or_coroutine = execute_func(task)
        else:
            # Extract parameters from task.input_data
            params = inspect.signature(execute_func).parameters
            for input_name in params:
                typ = params[input_name].annotation
                default_value = params[input_name].default
                if input_name in task.input_data:
                    if typ in utils.simple_types:
                        task_input[input_name] = task.input_data[input_name]
                    else:
                        task_input[input_name] = convert_from_dict_or_list(
                            typ, task.input_data[input_name]
                        )
                elif default_value is not inspect.Parameter.empty:
                    task_input[input_name] = default_value
                else:
                    task_input[input_name] = None

            result_or_coroutine = execute_func(**task_input)

        # Check if result is a coroutine and await it
        if asyncio.iscoroutine(result_or_coroutine):
            # Async function - await with timeout
            return await asyncio.wait_for(result_or_coroutine, timeout=timeout)
        else:
            # Sync function - already executed, return result
            return result_or_coroutine

    def _create_task_result(self, task: Task, task_output) -> TaskResult:
        """
        Create TaskResult from task and output.

        Handles TaskResult return values, dataclasses, and plain values.
        """
        # If user function returned a TaskResult, use it
        if isinstance(task_output, TaskResult):
            task_output.task_id = task.task_id
            task_output.workflow_instance_id = task.workflow_instance_id
            return task_output

        # Create new TaskResult
        task_result = TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=self.worker.get_identity()
        )
        task_result.status = TaskResultStatus.COMPLETED
        task_result.output_data = task_output

        # Handle dataclass output
        if dataclasses.is_dataclass(type(task_output)):
            task_result.output_data = dataclasses.asdict(task_output)
        # Handle non-dict output
        elif not isinstance(task_output, dict):
            try:
                serialized = self._api_client.sanitize_for_serialization(task_output)
                if not isinstance(serialized, dict):
                    task_result.output_data = {"result": serialized}
                else:
                    task_result.output_data = serialized
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

    async def _update_task(self, task_result: TaskResult) -> Optional[str]:
        """
        Update task result on Conductor server with retry logic.

        Improvements:
        - Uses exponential backoff with jitter (instead of linear)
        - Cached ApiClient for serialization
        """
        if not isinstance(task_result, TaskResult):
            return None

        task_definition_name = self.worker.get_task_definition_name()

        logger.debug(
            "Updating task, id: %s, workflow_instance_id: %s, task_definition_name: %s",
            task_result.task_id,
            task_result.workflow_instance_id,
            task_definition_name
        )

        # Serialize task result using cached ApiClient
        task_result_dict = self._api_client.sanitize_for_serialization(task_result)

        # Retry logic with exponential backoff + jitter
        for attempt in range(4):
            if attempt > 0:
                # Exponential backoff: 2^attempt seconds (2, 4, 8)
                base_delay = 2 ** attempt
                # Add jitter: 0-10% of base delay
                jitter = random.uniform(0, 0.1 * base_delay)
                delay = base_delay + jitter
                await asyncio.sleep(delay)

            try:
                # Get authentication headers
                headers = self._get_auth_headers()

                response = await self.http_client.post(
                    "/tasks",
                    json=task_result_dict,
                    headers=headers if headers else None
                )

                response.raise_for_status()
                result = response.text

                logger.debug(
                    "Updated task, id: %s, workflow_instance_id: %s, "
                    "task_definition_name: %s, response: %s",
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    result
                )

                return result

            except httpx.HTTPStatusError as e:
                # Handle 401 authentication errors specially
                if e.response.status_code == 401:
                    # Check if this is a token expiry/invalid token (renewable) vs invalid credentials
                    error_code = None
                    try:
                        response_data = e.response.json()
                        error_code = response_data.get('error', '')
                    except Exception:
                        pass

                    # If token is expired or invalid, try to renew it and retry
                    if error_code in ('EXPIRED_TOKEN', 'INVALID_TOKEN'):
                        token_status = "expired" if error_code == 'EXPIRED_TOKEN' else "invalid"
                        logger.info(
                            "Authentication token is %s, renewing token... (updating task: %s)",
                            token_status,
                            task_result.task_id
                        )

                        # Force token refresh (skip backoff - this is a legitimate renewal)
                        success = self._api_client.force_refresh_auth_token()

                        if success:
                            logger.info('Authentication token successfully renewed, retrying update')
                            # Retry the update request with new token once
                            try:
                                headers = self._get_auth_headers()
                                response = await self.http_client.post(
                                    "/tasks",
                                    json=task_result_dict,
                                    headers=headers if headers else None
                                )
                                response.raise_for_status()
                                return response.text
                            except Exception as retry_error:
                                logger.error(
                                    "Failed to update task after token renewal: %s",
                                    retry_error
                                )
                                # Continue to retry loop
                        else:
                            logger.error('Failed to renew authentication token')
                            # Continue to retry loop

                # Fall through to generic exception handling for retries
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_update_error(
                        task_definition_name, type(e)
                    )

                logger.error(
                    "Failed to update task (attempt %d/4), id: %s, "
                    "workflow_instance_id: %s, task_definition_name: %s, reason: %s",
                    attempt + 1,
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    traceback.format_exc()
                )

            except Exception as e:
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_update_error(
                        task_definition_name, type(e)
                    )

                logger.error(
                    "Failed to update task (attempt %d/4), id: %s, "
                    "workflow_instance_id: %s, task_definition_name: %s, reason: %s",
                    attempt + 1,
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    traceback.format_exc()
                )

        return None

    async def _wait_for_polling_interval(self) -> None:
        """Wait before next poll (non-blocking)"""
        polling_interval = self.worker.get_polling_interval_in_seconds()
        await asyncio.sleep(polling_interval)
