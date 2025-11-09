from __future__ import annotations
import asyncio
import dataclasses
import inspect
import logging
import os
import random
import sys
import time
import traceback
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict

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

# Lease extension constants (matching Java SDK)
LEASE_EXTEND_DURATION_FACTOR = 0.8  # Schedule at 80% of timeout
LEASE_EXTEND_RETRY_COUNT = 3


class TaskRunnerAsyncIO:
    """
    AsyncIO-based task runner implementing Java SDK architecture.

    Key features matching Java SDK:
    - Semaphore-based dynamic batch polling (batch size = available threads)
    - Zero-polling when all threads busy
    - In-memory queue for V2 API chained tasks
    - Automatic lease extension at 80% of task timeout
    - Adaptive batch sizing based on thread availability

    Architecture:
    - One coroutine per worker type for polling
    - Thread pool (size = worker.thread_count) for task execution
    - Semaphore with thread_count permits controls concurrency
    - In-memory queue drains before server polling

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
        use_v2_api: bool = True
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

        # Get thread count from worker (default = 1)
        thread_count = getattr(worker, 'thread_count', 1)

        # Semaphore with thread_count permits (Java SDK architecture)
        # Each permit represents one available execution thread
        self._semaphore = asyncio.Semaphore(thread_count)

        # In-memory queue for V2 API chained tasks (Java SDK: tasksTobeExecuted)
        self._task_queue: asyncio.Queue[Task] = asyncio.Queue()

        # AsyncIO HTTP client (shared across requests)
        self.http_client = http_client or httpx.AsyncClient(
            base_url=self.configuration.host,
            timeout=httpx.Timeout(
                connect=5.0,
                read=float(worker.poll_timeout) / 1000.0 + 5.0,  # poll_timeout + buffer
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
            max_workers=thread_count,
            thread_name_prefix=f"worker-{worker.get_task_definition_name()}"
        )

        # Track background tasks for proper cleanup
        self._background_tasks: set[asyncio.Task] = set()

        # Track active lease extension tasks
        self._lease_extensions: Dict[str, asyncio.Task] = {}

        # Auth failure backoff tracking to prevent retry storms
        self._auth_failures = 0
        self._last_auth_failure = 0

        # V2 API support - can be overridden by env var
        env_v2_api = os.getenv('taskUpdateV2', None)
        if env_v2_api is not None:
            self._use_v2_api = env_v2_api.lower() == 'true'
        else:
            self._use_v2_api = use_v2_api

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
            "Starting AsyncIO worker for task %s with domain %s, thread_count=%d, poll_timeout=%dms",
            task_names,
            self.worker.get_domain(),
            getattr(self.worker, 'thread_count', 1),
            self.worker.poll_timeout
        )

        try:
            while self._running:
                await self.run_once()
        except asyncio.CancelledError:
            logger.info("Worker task cancelled")
            raise
        finally:
            # Cancel all lease extensions
            for task_id, lease_task in list(self._lease_extensions.items()):
                lease_task.cancel()

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
        Single poll cycle with dynamic batch polling.

        Java SDK algorithm:
        1. Try to acquire all available semaphore permits (non-blocking)
        2. If pollCount == 0, skip polling (all threads busy)
        3. Poll batch from server (or drain in-memory queue first)
        4. If fewer tasks returned, release excess permits
        5. Submit each task for execution (holding one permit)
        6. Release permit after task completes

        THREAD SAFETY: Permits are tracked and released in finally block
        to prevent leaks on exceptions.
        """
        poll_count = 0
        tasks = []

        try:
            # Step 1: Calculate batch size by acquiring all available permits
            poll_count = await self._acquire_available_permits()

            # Step 2: Zero-polling optimization (Java SDK)
            if poll_count == 0:
                # All threads busy, skip polling
                await asyncio.sleep(0.1)  # Small sleep to prevent tight loop
                return

            # Step 3: Poll tasks (in-memory queue first, then server)
            tasks = await self._poll_tasks(poll_count)

            # Step 4: Release excess permits if fewer tasks returned
            if len(tasks) < poll_count:
                excess_permits = poll_count - len(tasks)
                for _ in range(excess_permits):
                    self._semaphore.release()
                # Update poll_count to reflect actual tasks
                poll_count = len(tasks)

            # Step 5: Submit tasks for execution (each holds one permit)
            for task in tasks:
                # Add to tracking set BEFORE creating task to avoid race
                # where task completes before we add it
                background_task = asyncio.create_task(
                    self._execute_and_update_task(task)
                )
                self._background_tasks.add(background_task)
                background_task.add_done_callback(self._background_tasks.discard)

            # Step 6: Wait for polling interval (only if no tasks polled)
            if len(tasks) == 0:
                await self._wait_for_polling_interval()

            # Clear task definition name cache
            self.worker.clear_task_definition_name_cache()

        except Exception as e:
            logger.error(
                "Error in run_once: %s",
                traceback.format_exc()
            )
            # CRITICAL: Release any permits that weren't used due to exception
            # This prevents permit leaks that cause deadlock
            tasks_submitted = len(tasks) if tasks else 0
            if poll_count > tasks_submitted:
                leaked_permits = poll_count - tasks_submitted
                for _ in range(leaked_permits):
                    self._semaphore.release()
                logger.warning(
                    "Released %d leaked permits due to exception in run_once",
                    leaked_permits
                )

    async def _acquire_available_permits(self) -> int:
        """
        Acquire all available semaphore permits (non-blocking).
        Returns the number of permits acquired (= available threads).

        This is the core of the Java SDK dynamic batch sizing algorithm.

        THREAD SAFETY: Uses try-except on acquire directly to avoid
        race condition between checking _value and acquiring.
        """
        poll_count = 0

        # Try to acquire all available permits without blocking
        while True:
            try:
                # Try non-blocking acquire
                # Don't check _value first - it's racy!
                await asyncio.wait_for(
                    self._semaphore.acquire(),
                    timeout=0.0001  # Almost immediate (~100 microseconds)
                )
                poll_count += 1
            except asyncio.TimeoutError:
                # No more permits available
                break

        return poll_count

    async def _poll_tasks(self, poll_count: int) -> List[Task]:
        """
        Poll tasks from in-memory queue first, then from server.

        Java SDK logic:
        1. Drain in-memory queue first (V2 API chained tasks)
        2. If queue empty, call server batch_poll
        3. Return up to poll_count tasks
        """
        tasks = []

        # Step 1: Drain in-memory queue first (V2 API support)
        while len(tasks) < poll_count and not self._task_queue.empty():
            try:
                task = self._task_queue.get_nowait()
                tasks.append(task)
            except asyncio.QueueEmpty:
                break

        # Step 2: If we still need tasks, poll from server
        if len(tasks) < poll_count:
            remaining_count = poll_count - len(tasks)
            server_tasks = await self._poll_tasks_from_server(remaining_count)
            tasks.extend(server_tasks)

        return tasks

    async def _poll_tasks_from_server(self, count: int) -> List[Task]:
        """
        Poll batch of tasks from Conductor server using batch_poll API.
        """
        task_definition_name = self.worker.get_task_definition_name()

        if self.worker.paused():
            logger.debug("Worker paused for: %s", task_definition_name)
            return []

        # Apply exponential backoff if we have recent auth failures
        if self._auth_failures > 0:
            now = time.time()
            backoff_seconds = min(2 ** self._auth_failures, 60)
            time_since_last_failure = now - self._last_auth_failure

            if time_since_last_failure < backoff_seconds:
                await asyncio.sleep(0.1)
                return []

        if self.metrics_collector is not None:
            self.metrics_collector.increment_task_poll(task_definition_name)

        try:
            start_time = time.time()

            # Build request parameters for batch_poll
            params = {
                "workerid": self.worker.get_identity(),
                "count": count,
                "timeout": self.worker.poll_timeout  # milliseconds
            }
            domain = self.worker.get_domain()
            if domain is not None:
                params["domain"] = domain

            # Get authentication headers
            headers = self._get_auth_headers()

            # Async HTTP request for batch poll
            response = await self.http_client.get(
                f"/tasks/poll/batch/{task_definition_name}",
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
                self._auth_failures = 0  # Reset on successful poll
                return []

            response.raise_for_status()
            tasks_data = response.json()

            # Convert to Task objects using cached ApiClient
            tasks = []
            if isinstance(tasks_data, list):
                for task_data in tasks_data:
                    if task_data:
                        task = self._api_client.deserialize_class(task_data, Task)
                        if task:
                            tasks.append(task)

            # Success - reset auth failure counter
            self._auth_failures = 0

            if tasks:
                logger.debug(
                    "Polled %d tasks for: %s, worker_id: %s, domain: %s",
                    len(tasks),
                    task_definition_name,
                    self.worker.get_identity(),
                    self.worker.get_domain()
                )

            return tasks

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
                        # Retry the poll request with new token once
                        try:
                            headers = self._get_auth_headers()
                            response = await self.http_client.get(
                                f"/tasks/poll/batch/{task_definition_name}",
                                params=params,
                                headers=headers if headers else None
                            )

                            if response.status_code == 204:
                                return []

                            response.raise_for_status()
                            tasks_data = response.json()

                            tasks = []
                            if isinstance(tasks_data, list):
                                for task_data in tasks_data:
                                    if task_data:
                                        task = self._api_client.deserialize_class(task_data, Task)
                                        if task:
                                            tasks.append(task)

                            self._auth_failures = 0
                            return tasks
                        except Exception as retry_error:
                            logger.error(
                                "Failed to poll tasks for %s after token renewal: %s",
                                task_definition_name,
                                retry_error
                            )
                            return []
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

            return []

        except Exception as e:
            if self.metrics_collector is not None:
                self.metrics_collector.increment_task_poll_error(
                    task_definition_name, type(e)
                )
            logger.error(
                "Failed to poll tasks for: %s, reason: %s",
                task_definition_name,
                traceback.format_exc()
            )
            return []

    async def _execute_and_update_task(self, task: Task) -> None:
        """
        Execute task and update result (runs in background).
        Holds one semaphore permit for the entire duration.

        Java SDK: processTask() method

        THREAD SAFETY: Permit is ALWAYS released in finally block,
        even if exceptions occur. Lease extension is always cancelled.
        """
        lease_task = None

        try:
            # Execute task
            task_result = await self._execute_task(task)

            # Start lease extension if configured
            if self.worker.lease_extend_enabled and task.response_timeout_seconds and task.response_timeout_seconds > 0:
                lease_task = asyncio.create_task(
                    self._lease_extend_loop(task, task_result)
                )
                self._lease_extensions[task.task_id] = lease_task

            # Update result
            await self._update_task(task_result)

        except Exception as e:
            logger.exception("Error in background task execution for task_id: %s", task.task_id)

        finally:
            # CRITICAL: Always cancel lease extension and release permit
            # Even if update failed or exception occurred
            if lease_task:
                lease_task.cancel()
                # Clean up from tracking dict
                if task.task_id in self._lease_extensions:
                    del self._lease_extensions[task.task_id]

            # Always release semaphore permit (Java SDK: finally block in processTask)
            # This MUST happen to prevent deadlock
            self._semaphore.release()

    async def _lease_extend_loop(self, task: Task, task_result: TaskResult) -> None:
        """
        Periodically extend task lease at 80% of response timeout.

        Java SDK: scheduleLeaseExtend() method
        """
        try:
            # Calculate lease extension interval (80% of timeout)
            timeout_seconds = task.response_timeout_seconds
            extend_interval = timeout_seconds * LEASE_EXTEND_DURATION_FACTOR

            logger.debug(
                "Starting lease extension for task %s, interval: %.1fs",
                task.task_id,
                extend_interval
            )

            while True:
                await asyncio.sleep(extend_interval)

                # Send lease extension update
                for attempt in range(LEASE_EXTEND_RETRY_COUNT):
                    try:
                        # Create a copy with just the lease extension flag
                        extend_result = TaskResult(
                            task_id=task.task_id,
                            workflow_instance_id=task.workflow_instance_id,
                            worker_id=self.worker.get_identity()
                        )
                        extend_result.extend_lease = True

                        await self._update_task(extend_result, is_lease_extension=True)
                        logger.debug("Lease extended for task %s", task.task_id)
                        break
                    except Exception as e:
                        if attempt < LEASE_EXTEND_RETRY_COUNT - 1:
                            logger.warning(
                                "Failed to extend lease for task %s (attempt %d/%d): %s",
                                task.task_id,
                                attempt + 1,
                                LEASE_EXTEND_RETRY_COUNT,
                                e
                            )
                            await asyncio.sleep(1)
                        else:
                            logger.error(
                                "Failed to extend lease for task %s after %d attempts",
                                task.task_id,
                                LEASE_EXTEND_RETRY_COUNT
                            )

        except asyncio.CancelledError:
            logger.debug("Lease extension cancelled for task %s", task.task_id)
        except Exception as e:
            logger.error(
                "Error in lease extension loop for task %s: %s",
                task.task_id,
                e
            )

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

        except NonRetryableException as e:
            # Non-retryable errors (business logic errors)
            logger.error(
                "Non-retryable error executing task, id: %s, error: %s",
                task.task_id,
                str(e)
            )

            if self.metrics_collector is not None:
                self.metrics_collector.increment_task_execution_error(
                    task_definition_name, type(e)
                )

            task_result = TaskResult(
                task_id=task.task_id,
                workflow_instance_id=task.workflow_instance_id,
                worker_id=self.worker.get_identity()
            )
            task_result.status = "FAILED_WITH_TERMINAL_ERROR"
            task_result.reason_for_incompletion = str(e)
            task_result.logs = [TaskExecLog(
                traceback.format_exc(), task_result.task_id, int(time.time()))]
            return task_result

        except Exception as e:
            # Generic execution errors
            if self.metrics_collector is not None:
                self.metrics_collector.increment_task_execution_error(
                    task_definition_name, type(e)
                )

            task_result = TaskResult(
                task_id=task.task_id,
                workflow_instance_id=task.workflow_instance_id,
                worker_id=self.worker.get_identity()
            )
            task_result.status = "FAILED"
            task_result.reason_for_incompletion = str(e)
            task_result.logs = [TaskExecLog(
                traceback.format_exc(), task_result.task_id, int(time.time()))]
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

        This method handles both sync and async worker functions:
        - Async functions: await directly
        - Sync functions: run in thread pool executor
        """
        execute_func = self.worker._execute_function if hasattr(self.worker, '_execute_function') else self.worker.execute_function

        # Check if function accepts Task object or individual parameters
        is_task_param = self._is_execute_function_input_parameter_a_task()

        if is_task_param:
            # Function accepts Task object directly
            if asyncio.iscoroutinefunction(execute_func):
                # Async function - await it with timeout
                result = await asyncio.wait_for(execute_func(task), timeout=timeout)
            else:
                # Sync function - run in executor
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, execute_func, task),
                    timeout=timeout
                )
            return result
        else:
            # Function accepts individual parameters
            params = inspect.signature(execute_func).parameters
            task_input = {}

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

            # Call function with unpacked parameters
            if asyncio.iscoroutinefunction(execute_func):
                # Async function - await it with timeout
                result = await asyncio.wait_for(
                    execute_func(**task_input),
                    timeout=timeout
                )
            else:
                # Sync function - run in executor
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._executor,
                        lambda: execute_func(**task_input)
                    ),
                    timeout=timeout
                )

            return result

    def _is_execute_function_input_parameter_a_task(self) -> bool:
        """Check if execute function accepts Task object or individual parameters."""
        execute_func = self.worker._execute_function if hasattr(self.worker, '_execute_function') else self.worker.execute_function

        if hasattr(self.worker, '_is_execute_function_input_parameter_a_task'):
            return self.worker._is_execute_function_input_parameter_a_task

        # Check signature
        sig = inspect.signature(execute_func)
        params = list(sig.parameters.values())

        if len(params) == 1:
            param_type = params[0].annotation
            if param_type == Task or param_type == 'Task':
                return True

        return False

    def _create_task_result(self, task: Task, task_output) -> TaskResult:
        """
        Create TaskResult from task output.
        Handles various output types (TaskResult, dict, primitive, etc.)
        """
        if isinstance(task_output, TaskResult):
            # Already a TaskResult
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

        # Handle output serialization based on type
        # - dict/object: Use as-is (valid JSON document)
        # - primitives/arrays: Wrap in {"result": ...}
        #
        # IMPORTANT: Must sanitize first to handle dataclasses/objects,
        # then check if result is dict
        try:
            sanitized_output = self._api_client.sanitize_for_serialization(task_output)

            if isinstance(sanitized_output, dict):
                # Dict (or object that serialized to dict) - use as-is
                task_result.output_data = sanitized_output
            else:
                # Primitive or array - wrap in {"result": ...}
                task_result.output_data = {"result": sanitized_output}

        except Exception as e:
            logger.warning(
                "Failed to serialize task output for task %s: %s. Using string representation.",
                task.task_id,
                e
            )
            task_result.output_data = {"result": str(task_output)}

        return task_result

    async def _update_task(self, task_result: TaskResult, is_lease_extension: bool = False) -> Optional[str]:
        """
        Update task result on Conductor server with retry logic.

        For V2 API, server may return next task to execute (chained tasks).
        """
        if not isinstance(task_result, TaskResult):
            return None

        task_definition_name = self.worker.get_task_definition_name()

        if not is_lease_extension:
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

                # Choose API endpoint based on V2 flag
                endpoint = "/tasks/update-v2" if self._use_v2_api else "/tasks"

                response = await self.http_client.post(
                    endpoint,
                    json=task_result_dict,
                    headers=headers if headers else None
                )

                response.raise_for_status()
                result = response.text

                if not is_lease_extension:
                    logger.debug(
                        "Updated task, id: %s, workflow_instance_id: %s, "
                        "task_definition_name: %s, response: %s",
                        task_result.task_id,
                        task_result.workflow_instance_id,
                        task_definition_name,
                        result
                    )

                # V2 API: Check if server returned next task (same task type)
                # Optimization: Try immediate execution if permit available,
                # otherwise queue for later polling
                if self._use_v2_api and response.status_code == 200 and not is_lease_extension:
                    try:
                        # Response can be:
                        # - Empty string (no next task)
                        # - Task object (next task of same type)
                        response_text = response.text
                        if response_text and response_text.strip():
                            response_data = response.json()
                            if response_data and isinstance(response_data, dict) and 'taskId' in response_data:
                                next_task = self._api_client.deserialize_class(response_data, Task)
                                if next_task and next_task.task_id:
                                    # Try immediate execution if permit available
                                    await self._try_immediate_execution(next_task)
                    except Exception as e:
                        logger.warning("Failed to parse V2 response for next task: %s", e)

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
                                    endpoint,
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

                if not is_lease_extension:
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

                if not is_lease_extension:
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
        """Wait for polling interval before next poll (only when no tasks found)."""
        polling_interval = self.worker.get_polling_interval_in_seconds()
        await asyncio.sleep(polling_interval)

    async def _try_immediate_execution(self, task: Task) -> None:
        """
        Try to execute task immediately if semaphore permit available.
        If no permit available, add to queue as fallback.

        This optimization eliminates the latency of waiting for the next
        run_once() iteration to poll the queue.

        Args:
            task: The task to execute
        """
        try:
            # Try non-blocking permit acquisition
            acquired = False
            try:
                await asyncio.wait_for(
                    self._semaphore.acquire(),
                    timeout=0.0001  # Essentially non-blocking
                )
                acquired = True
            except asyncio.TimeoutError:
                # No permit available - will queue instead
                pass

            if acquired:
                # SUCCESS: Permit acquired, execute immediately
                logger.info(
                    "V2 API: Immediately executing next task %s (type: %s)",
                    task.task_id,
                    task.task_def_name
                )

                # Create background task (holds the permit)
                # The permit will be released in _execute_and_update_task's finally block
                background_task = asyncio.create_task(
                    self._execute_and_update_task(task)
                )
                self._background_tasks.add(background_task)
                background_task.add_done_callback(self._background_tasks.discard)

                # Track metrics
                if self.metrics_collector:
                    self.metrics_collector.increment_task_execution_queue_full(
                        task.task_def_name
                    )
            else:
                # FAILURE: No permits available, add to queue for later polling
                logger.info(
                    "V2 API: No permits available, queueing task %s (type: %s)",
                    task.task_id,
                    task.task_def_name
                )
                await self._task_queue.put(task)

        except Exception as e:
            # On any error, queue the task as fallback
            logger.warning(
                "Error in immediate execution attempt for task %s: %s - queueing",
                task.task_id if task else "unknown",
                e
            )
            try:
                await self._task_queue.put(task)
            except Exception as queue_error:
                logger.error(
                    "Failed to queue task after immediate execution error: %s",
                    queue_error
                )

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info("Stopping worker...")
        self._running = False
