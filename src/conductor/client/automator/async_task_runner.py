import asyncio
import inspect
import logging
import os
import sys
import time
import traceback

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context.task_context import _set_task_context, _clear_task_context, TaskInProgress
from conductor.client.event.task_runner_events import (
    TaskRunnerEvent, PollStarted, PollCompleted, PollFailure,
    TaskExecutionStarted, TaskExecutionCompleted, TaskExecutionFailure
)
from conductor.client.event.sync_event_dispatcher import SyncEventDispatcher
from conductor.client.event.sync_listener_register import register_task_runner_listener
from conductor.client.http.api.async_task_resource_api import AsyncTaskResourceApi
from conductor.client.http.async_api_client import AsyncApiClient
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.http.rest import AuthorizationException
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.worker.worker_config import resolve_worker_config, get_worker_config_oneline

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


class AsyncTaskRunner:
    """
    Pure async/await task runner for async workers.

    Eliminates thread overhead by running everything in a single event loop:
    - Async polling (via AsyncTaskResourceApi)
    - Async task execution (direct await of worker function)
    - Async result updates (via AsyncTaskResourceApi)

    Key differences from TaskRunner:
    - No ThreadPoolExecutor
    - No BackgroundEventLoop
    - No ASYNC_TASK_RUNNING sentinel
    - Direct await of worker functions
    - asyncio.gather() for concurrency

    Preserved features:
    - Same event publishing (PollStarted, PollCompleted, TaskExecutionCompleted, etc.)
    - Same metrics collection (via MetricsCollector as event listener)
    - Same configuration resolution
    - Same adaptive backoff logic
    - Same auth failure handling
    """

    def __init__(
            self,
            worker: WorkerInterface,
            configuration: Configuration = None,
            metrics_settings: MetricsSettings = None,
            event_listeners: list = None
    ):
        if not isinstance(worker, WorkerInterface):
            raise Exception("Invalid worker")
        self.worker = worker
        self.__set_worker_properties()
        if not isinstance(configuration, Configuration):
            configuration = Configuration()
        self.configuration = configuration

        # Set up event dispatcher and register listeners (same as TaskRunner)
        self.event_dispatcher = SyncEventDispatcher[TaskRunnerEvent]()
        if event_listeners:
            for listener in event_listeners:
                register_task_runner_listener(listener, self.event_dispatcher)

        self.metrics_collector = None
        if metrics_settings is not None:
            self.metrics_collector = MetricsCollector(
                metrics_settings
            )
            # Register metrics collector as event listener
            register_task_runner_listener(self.metrics_collector, self.event_dispatcher)

        # Don't create async HTTP client here - will be created in subprocess
        # httpx.AsyncClient is not picklable, so we defer creation until after fork
        self.async_api_client = None
        self.async_task_client = None

        # Auth failure backoff tracking (same as TaskRunner)
        self._auth_failures = 0
        self._last_auth_failure = 0

        # Polling state tracking (same as TaskRunner)
        self._max_workers = getattr(worker, 'thread_count', 1)  # Max concurrent tasks
        self._running_tasks = set()  # Track running asyncio tasks
        self._last_poll_time = 0
        self._consecutive_empty_polls = 0

        # Semaphore will be created in run() within the event loop
        self._semaphore = None

    async def run(self) -> None:
        """Main async loop - runs continuously in single event loop."""
        if self.configuration is not None:
            self.configuration.apply_logging_config()
        else:
            logger.setLevel(logging.DEBUG)

        # Create async HTTP client in subprocess (after fork)
        # This must be done here because httpx.AsyncClient is not picklable
        self.async_api_client = AsyncApiClient(
            configuration=self.configuration,
            metrics_collector=self.metrics_collector
        )

        self.async_task_client = AsyncTaskResourceApi(
            api_client=self.async_api_client
        )

        # Create semaphore in the event loop (must be created within the loop)
        self._semaphore = asyncio.Semaphore(self._max_workers)

        # Log worker configuration with correct PID (after fork)
        task_name = self.worker.get_task_definition_name()
        config_summary = get_worker_config_oneline(task_name, self._resolved_config)
        logger.info(config_summary)

        task_names = ",".join(self.worker.task_definition_names)
        logger.debug(
            "Async polling task %s with domain %s with polling interval %s",
            task_names,
            self.worker.get_domain(),
            self.worker.get_polling_interval_in_seconds()
        )

        try:
            while True:
                await self.run_once()
        finally:
            # Cleanup async client on exit
            if self.async_api_client:
                await self.async_api_client.close()

    async def run_once(self) -> None:
        """Execute one iteration of the polling loop (async version)."""
        try:
            # Cleanup completed tasks
            self.__cleanup_completed_tasks()

            # Check if we can accept more tasks
            current_capacity = len(self._running_tasks)
            if current_capacity >= self._max_workers:
                # At capacity - sleep briefly then return
                await asyncio.sleep(0.001)  # 1ms
                return

            # Calculate how many tasks we can accept
            available_slots = self._max_workers - current_capacity

            # Adaptive backoff: if queue is empty, don't poll too aggressively (same logic as TaskRunner)
            if self._consecutive_empty_polls > 0:
                now = time.time()
                time_since_last_poll = now - self._last_poll_time

                # Exponential backoff for empty polls (1ms, 2ms, 4ms, 8ms, up to poll_interval)
                capped_empty_polls = min(self._consecutive_empty_polls, 10)
                min_poll_delay = min(0.001 * (2 ** capped_empty_polls), self.worker.get_polling_interval_in_seconds())

                if time_since_last_poll < min_poll_delay:
                    # Too soon to poll again - sleep the remaining time
                    await asyncio.sleep(min_poll_delay - time_since_last_poll)
                    return

            # Batch poll for tasks (async)
            tasks = await self.__async_batch_poll(available_slots)
            self._last_poll_time = time.time()

            if tasks:
                # Got tasks - reset backoff and start executing them concurrently
                self._consecutive_empty_polls = 0
                for task in tasks:
                    if task and task.task_id:
                        # Create async task for each polled task
                        asyncio_task = asyncio.create_task(
                            self.__async_execute_and_update_task(task)
                        )
                        self._running_tasks.add(asyncio_task)
                        # Add callback to remove from set when done
                        asyncio_task.add_done_callback(self._running_tasks.discard)
            else:
                # No tasks available - increment backoff counter
                self._consecutive_empty_polls += 1

            self.worker.clear_task_definition_name_cache()
        except Exception as e:
            logger.error("Error in run_once: %s", traceback.format_exc())

    def __cleanup_completed_tasks(self) -> None:
        """Remove completed task futures from tracking set (same as TaskRunner)."""
        self._running_tasks = {f for f in self._running_tasks if not f.done()}

    async def __async_batch_poll(self, count: int) -> list:
        """Async batch poll for multiple tasks (async version of TaskRunner.__batch_poll_tasks)."""
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused:
            logger.debug("Stop polling task for: %s", task_definition_name)
            return []

        # Apply exponential backoff if we have recent auth failures (same as TaskRunner)
        if self._auth_failures > 0:
            now = time.time()
            backoff_seconds = min(2 ** self._auth_failures, 60)
            time_since_last_failure = now - self._last_auth_failure
            if time_since_last_failure < backoff_seconds:
                await asyncio.sleep(0.1)
                return []

        # Publish PollStarted event (same as TaskRunner:245)
        self.event_dispatcher.publish(PollStarted(
            task_type=task_definition_name,
            worker_id=self.worker.get_identity(),
            poll_count=count
        ))

        try:
            start_time = time.time()
            domain = self.worker.get_domain()
            params = {
                "workerid": self.worker.get_identity(),
                "count": count,
                "timeout": 100  # ms
            }
            if domain is not None:
                params["domain"] = domain

            # Async batch poll
            tasks = await self.async_task_client.batch_poll(tasktype=task_definition_name, **params)

            finish_time = time.time()
            time_spent = finish_time - start_time

            # Publish PollCompleted event (same as TaskRunner:268)
            self.event_dispatcher.publish(PollCompleted(
                task_type=task_definition_name,
                duration_ms=time_spent * 1000,
                tasks_received=len(tasks) if tasks else 0
            ))

            # Success - reset auth failure counter
            if tasks:
                self._auth_failures = 0

            return tasks if tasks else []

        except AuthorizationException as auth_exception:
            self._auth_failures += 1
            self._last_auth_failure = time.time()
            backoff_seconds = min(2 ** self._auth_failures, 60)

            # Publish PollFailure event (same as TaskRunner:286)
            self.event_dispatcher.publish(PollFailure(
                task_type=task_definition_name,
                duration_ms=(time.time() - start_time) * 1000,
                cause=auth_exception
            ))

            if auth_exception.invalid_token:
                logger.error(
                    f"Failed to batch poll task {task_definition_name} due to invalid auth token "
                    f"(failure #{self._auth_failures}). Will retry with exponential backoff ({backoff_seconds}s). "
                    "Please check your CONDUCTOR_AUTH_KEY and CONDUCTOR_AUTH_SECRET."
                )
            else:
                logger.error(
                    f"Failed to batch poll task {task_definition_name} error: {auth_exception.status} - {auth_exception.error_code} "
                    f"(failure #{self._auth_failures}). Will retry with exponential backoff ({backoff_seconds}s)."
                )
            return []
        except Exception as e:
            # Publish PollFailure event (same as TaskRunner:306)
            self.event_dispatcher.publish(PollFailure(
                task_type=task_definition_name,
                duration_ms=(time.time() - start_time) * 1000,
                cause=e
            ))
            logger.error(
                "Failed to batch poll task for: %s, reason: %s",
                task_definition_name,
                traceback.format_exc()
            )
            return []

    async def __async_execute_and_update_task(self, task: Task) -> None:
        """Execute task and update result (async version - runs in event loop, not thread pool)."""
        # Acquire semaphore to limit concurrency
        async with self._semaphore:
            try:
                task_result = await self.__async_execute_task(task)
                # If task returned TaskInProgress, don't update yet
                if isinstance(task_result, TaskInProgress):
                    logger.debug("Task %s is in progress, will update when complete", task.task_id)
                    return
                if task_result is not None:
                    await self.__async_update_task(task_result)
            except Exception as e:
                logger.error(
                    "Error executing/updating task %s: %s",
                    task.task_id if task else "unknown",
                    traceback.format_exc()
                )

    async def __async_execute_task(self, task: Task) -> TaskResult:
        """Execute async worker function directly (no threads, no BackgroundEventLoop)."""
        if not isinstance(task, Task):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        logger.trace(
            "Executing async task, id: %s, workflow_instance_id: %s, task_definition_name: %s",
            task.task_id,
            task.workflow_instance_id,
            task_definition_name
        )

        # Create initial task result for context (same as TaskRunner:410)
        initial_task_result = TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=self.worker.get_identity()
        )

        # Set task context (same as TaskRunner:417)
        _set_task_context(task, initial_task_result)

        # Publish TaskExecutionStarted event (same as TaskRunner:420)
        self.event_dispatcher.publish(TaskExecutionStarted(
            task_type=task_definition_name,
            task_id=task.task_id,
            worker_id=self.worker.get_identity(),
            workflow_instance_id=task.workflow_instance_id
        ))

        try:
            start_time = time.time()

            # Get worker function parameters (same as TaskRunner, but for async function)
            params = inspect.signature(self.worker.execute_function).parameters
            task_input = {}
            for input_name in params:
                typ = params[input_name].annotation
                default_value = params[input_name].default
                if input_name in task.input_data:
                    from conductor.client.automator import utils
                    if typ in utils.simple_types:
                        task_input[input_name] = task.input_data[input_name]
                    else:
                        from conductor.client.automator.utils import convert_from_dict_or_list
                        task_input[input_name] = convert_from_dict_or_list(typ, task.input_data[input_name])
                elif default_value is not inspect.Parameter.empty:
                    task_input[input_name] = default_value
                else:
                    task_input[input_name] = None

            # Direct await of async worker function - NO THREADS!
            task_output = await self.worker.execute_function(**task_input)

            # Handle different return types (same as TaskRunner:441-474)
            if isinstance(task_output, TaskResult):
                # Already a TaskResult - use as-is
                task_result = task_output
            elif isinstance(task_output, TaskInProgress):
                # Long-running task - create IN_PROGRESS result
                task_result = TaskResult(
                    task_id=task.task_id,
                    workflow_instance_id=task.workflow_instance_id,
                    worker_id=self.worker.get_identity()
                )
                task_result.status = TaskResultStatus.IN_PROGRESS
                task_result.callback_after_seconds = task_output.callback_after_seconds
                task_result.output_data = task_output.output
            else:
                # Regular return value - create COMPLETED result
                task_result = TaskResult(
                    task_id=task.task_id,
                    workflow_instance_id=task.workflow_instance_id,
                    worker_id=self.worker.get_identity()
                )
                task_result.status = TaskResultStatus.COMPLETED
                if isinstance(task_output, dict):
                    task_result.output_data = task_output
                else:
                    task_result.output_data = {"result": task_output}

            # Merge context modifications (same as TaskRunner:477)
            self.__merge_context_modifications(task_result, initial_task_result)

            finish_time = time.time()
            time_spent = finish_time - start_time

            # Publish TaskExecutionCompleted event (same as TaskRunner:484)
            output_size = sys.getsizeof(task_result) if task_result else 0
            self.event_dispatcher.publish(TaskExecutionCompleted(
                task_type=task_definition_name,
                task_id=task.task_id,
                worker_id=self.worker.get_identity(),
                workflow_instance_id=task.workflow_instance_id,
                duration_ms=time_spent * 1000,
                output_size_bytes=output_size
            ))
            logger.debug(
                "Executed async task, id: %s, workflow_instance_id: %s, task_definition_name: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name
            )
        except Exception as e:
            finish_time = time.time()
            time_spent = finish_time - start_time

            # Publish TaskExecutionFailure event (same as TaskRunner:503)
            self.event_dispatcher.publish(TaskExecutionFailure(
                task_type=task_definition_name,
                task_id=task.task_id,
                worker_id=self.worker.get_identity(),
                workflow_instance_id=task.workflow_instance_id,
                cause=e,
                duration_ms=time_spent * 1000
            ))
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
                "Failed to execute async task, id: %s, workflow_instance_id: %s, "
                "task_definition_name: %s, reason: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name,
                traceback.format_exc()
            )
        finally:
            # Always clear task context after execution (same as TaskRunner:530)
            _clear_task_context()

        return task_result

    def __merge_context_modifications(self, task_result: TaskResult, context_result: TaskResult) -> None:
        """
        Merge modifications made via TaskContext into the final task result (same as TaskRunner).

        This allows workers to use TaskContext.add_log(), set_callback_after(), etc.
        and have those modifications reflected in the final result.
        """
        # Merge logs
        if hasattr(context_result, 'logs') and context_result.logs:
            if not hasattr(task_result, 'logs') or task_result.logs is None:
                task_result.logs = []
            task_result.logs.extend(context_result.logs)

        # Merge callback_after_seconds (context takes precedence if both set)
        if hasattr(context_result, 'callback_after_seconds') and context_result.callback_after_seconds:
            if not task_result.callback_after_seconds:
                task_result.callback_after_seconds = context_result.callback_after_seconds

        # Merge output_data if context set it (shouldn't normally happen, but handle it)
        if (hasattr(context_result, 'output_data') and
            context_result.output_data and
            not isinstance(task_result.output_data, dict)):
            if hasattr(task_result, 'output_data') and task_result.output_data:
                # Merge both dicts (task_result takes precedence)
                merged_output = {**context_result.output_data, **task_result.output_data}
                task_result.output_data = merged_output
            else:
                task_result.output_data = context_result.output_data

    async def __async_update_task(self, task_result: TaskResult):
        """Async update task result (async version of TaskRunner.__update_task)."""
        if not isinstance(task_result, TaskResult):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        logger.debug(
            "Updating async task, id: %s, workflow_instance_id: %s, task_definition_name: %s, status: %s, output_data: %s",
            task_result.task_id,
            task_result.workflow_instance_id,
            task_definition_name,
            task_result.status,
            task_result.output_data
        )
        # Retry logic (same as TaskRunner:579-604)
        for attempt in range(4):
            if attempt > 0:
                # Wait for [10s, 20s, 30s] before next attempt
                await asyncio.sleep(attempt * 10)
            try:
                response = await self.async_task_client.update_task(body=task_result)
                logger.debug(
                    "Updated async task, id: %s, workflow_instance_id: %s, task_definition_name: %s, response: %s",
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    response
                )
                return response
            except Exception as e:
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_update_error(
                        task_definition_name, type(e)
                    )
                logger.error(
                    "Failed to update async task, id: %s, workflow_instance_id: %s, task_definition_name: %s, reason: %s",
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    traceback.format_exc()
                )
        return None

    def __set_worker_properties(self) -> None:
        """
        Resolve worker configuration using hierarchical override (same as TaskRunner).
        Note: Logging is done in run() to capture the correct PID (after fork).
        """
        task_name = self.worker.get_task_definition_name()

        # Resolve configuration with hierarchical override
        resolved_config = resolve_worker_config(
            worker_name=task_name,
            poll_interval=getattr(self.worker, 'poll_interval', None),
            domain=getattr(self.worker, 'domain', None),
            worker_id=getattr(self.worker, 'worker_id', None),
            thread_count=getattr(self.worker, 'thread_count', 1),
            register_task_def=getattr(self.worker, 'register_task_def', False),
            poll_timeout=getattr(self.worker, 'poll_timeout', 100),
            lease_extend_enabled=getattr(self.worker, 'lease_extend_enabled', False),
            paused=getattr(self.worker, 'paused', False)
        )

        # Apply resolved configuration to worker
        if resolved_config.get('poll_interval') is not None:
            self.worker.poll_interval = resolved_config['poll_interval']
        if resolved_config.get('domain') is not None:
            self.worker.domain = resolved_config['domain']
        if resolved_config.get('worker_id') is not None:
            self.worker.worker_id = resolved_config['worker_id']
        if resolved_config.get('thread_count') is not None:
            self.worker.thread_count = resolved_config['thread_count']
        if resolved_config.get('register_task_def') is not None:
            self.worker.register_task_def = resolved_config['register_task_def']
        if resolved_config.get('poll_timeout') is not None:
            self.worker.poll_timeout = resolved_config['poll_timeout']
        if resolved_config.get('lease_extend_enabled') is not None:
            self.worker.lease_extend_enabled = resolved_config['lease_extend_enabled']
        if resolved_config.get('paused') is not None:
            self.worker.paused = resolved_config['paused']

        # Store resolved config for logging in run() (after fork)
        self._resolved_config = resolved_config
