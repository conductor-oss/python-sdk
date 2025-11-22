import logging
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context.task_context import _set_task_context, _clear_task_context, TaskInProgress
from conductor.client.event.task_runner_events import (
    TaskRunnerEvent, PollStarted, PollCompleted, PollFailure,
    TaskExecutionStarted, TaskExecutionCompleted, TaskExecutionFailure
)
from conductor.client.event.sync_event_dispatcher import SyncEventDispatcher
from conductor.client.event.sync_listener_register import register_task_runner_listener
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.http.rest import AuthorizationException
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.worker.worker_interface import WorkerInterface

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


class TaskRunner:
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

        # Set up event dispatcher and register listeners
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

        self.task_client = TaskResourceApi(
            ApiClient(
                configuration=self.configuration
            )
        )

        # Auth failure backoff tracking to prevent retry storms
        self._auth_failures = 0
        self._last_auth_failure = 0

        # Thread pool for concurrent task execution
        # thread_count from worker configuration controls concurrency
        max_workers = getattr(worker, 'thread_count', 1)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"worker-{worker.get_task_definition_name()}")
        self._running_tasks = set()  # Track futures of running tasks
        self._max_workers = max_workers
        self._last_poll_time = 0  # Track last poll to avoid excessive polling when queue is empty
        self._consecutive_empty_polls = 0  # Track empty polls to implement backoff

    def run(self) -> None:
        if self.configuration is not None:
            self.configuration.apply_logging_config()
        else:
            logger.setLevel(logging.DEBUG)

        task_names = ",".join(self.worker.task_definition_names)
        logger.info(
            "Polling task %s with domain %s with polling interval %s",
            task_names,
            self.worker.get_domain(),
            self.worker.get_polling_interval_in_seconds()
        )

        while True:
            self.run_once()

    def run_once(self) -> None:
        try:
            # Check completed async tasks first (non-blocking)
            self.__check_completed_async_tasks()

            # Cleanup completed tasks immediately - this is critical for detecting available slots
            self.__cleanup_completed_tasks()

            # Check if we can accept more tasks (based on thread_count)
            # Account for pending async tasks in capacity calculation
            pending_async_count = len(getattr(self.worker, '_pending_async_tasks', {}))
            current_capacity = len(self._running_tasks) + pending_async_count
            if current_capacity >= self._max_workers:
                # At capacity - sleep briefly then return to check again
                time.sleep(0.001)  # 1ms - just enough to prevent CPU spinning
                return

            # Calculate how many tasks we can accept
            available_slots = self._max_workers - current_capacity

            # Adaptive backoff: if queue is empty, don't poll too aggressively
            if self._consecutive_empty_polls > 0:
                now = time.time()
                time_since_last_poll = now - self._last_poll_time

                # Exponential backoff for empty polls (1ms, 2ms, 4ms, 8ms, up to poll_interval)
                # Cap exponent at 10 to prevent overflow (2^10 = 1024ms = 1s)
                capped_empty_polls = min(self._consecutive_empty_polls, 10)
                min_poll_delay = min(0.001 * (2 ** capped_empty_polls), self.worker.get_polling_interval_in_seconds())

                if time_since_last_poll < min_poll_delay:
                    # Too soon to poll again - sleep the remaining time
                    time.sleep(min_poll_delay - time_since_last_poll)
                    return

            # Always use batch poll (even for 1 task) for consistency
            tasks = self.__batch_poll_tasks(available_slots)
            self._last_poll_time = time.time()

            if tasks:
                # Got tasks - reset backoff and submit to executor
                self._consecutive_empty_polls = 0
                for task in tasks:
                    if task and task.task_id:
                        future = self._executor.submit(self.__execute_and_update_task, task)
                        self._running_tasks.add(future)
                # Continue immediately - don't sleep!
            else:
                # No tasks available - increment backoff counter
                self._consecutive_empty_polls += 1

            self.worker.clear_task_definition_name_cache()
        except Exception as e:
            logger.error("Error in run_once: %s", traceback.format_exc())

    def __cleanup_completed_tasks(self) -> None:
        """Remove completed task futures from tracking set"""
        # Fast path: use difference_update for better performance
        self._running_tasks = {f for f in self._running_tasks if not f.done()}

    def __check_completed_async_tasks(self) -> None:
        """Check for completed async tasks and update Conductor"""
        if not hasattr(self.worker, 'check_completed_async_tasks'):
            return

        completed = self.worker.check_completed_async_tasks()
        for task_id, task_result in completed:
            try:
                self.__update_task(task_result)
            except Exception as e:
                logger.error(
                    "Error updating completed async task %s: %s",
                    task_id,
                    traceback.format_exc()
                )

    def __execute_and_update_task(self, task: Task) -> None:
        """Execute task and update result (runs in thread pool)"""
        try:
            task_result = self.__execute_task(task)
            # If task returned None, it's running async - don't update yet
            if task_result is None:
                logger.debug("Task %s is running async, will update when complete", task.task_id)
                return
            # If task returned TaskInProgress, it's running async - don't update yet
            if isinstance(task_result, TaskInProgress):
                logger.debug("Task %s is in progress, will update when complete", task.task_id)
                return
            self.__update_task(task_result)
        except Exception as e:
            logger.error(
                "Error executing/updating task %s: %s",
                task.task_id if task else "unknown",
                traceback.format_exc()
            )

    def __batch_poll_tasks(self, count: int) -> list:
        """Poll for multiple tasks at once (more efficient than polling one at a time)"""
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused():
            logger.debug("Stop polling task for: %s", task_definition_name)
            return []

        # Apply exponential backoff if we have recent auth failures
        if self._auth_failures > 0:
            now = time.time()
            backoff_seconds = min(2 ** self._auth_failures, 60)
            time_since_last_failure = now - self._last_auth_failure
            if time_since_last_failure < backoff_seconds:
                time.sleep(0.1)
                return []

        # Publish PollStarted event (metrics collector will handle via event)
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

            tasks = self.task_client.batch_poll(tasktype=task_definition_name, **params)

            finish_time = time.time()
            time_spent = finish_time - start_time

            # Publish PollCompleted event (metrics collector will handle via event)
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

            # Publish PollFailure event (metrics collector will handle via event)
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
            # Publish PollFailure event (metrics collector will handle via event)
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

    def __poll_task(self) -> Task:
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused():
            logger.debug("Stop polling task for: %s", task_definition_name)
            return None

        # Apply exponential backoff if we have recent auth failures
        if self._auth_failures > 0:
            now = time.time()
            # Exponential backoff: 2^failures seconds (2s, 4s, 8s, 16s, 32s)
            backoff_seconds = min(2 ** self._auth_failures, 60)  # Cap at 60s
            time_since_last_failure = now - self._last_auth_failure

            if time_since_last_failure < backoff_seconds:
                # Still in backoff period - skip polling
                time.sleep(0.1)  # Small sleep to prevent tight loop
                return None

        if self.metrics_collector is not None:
            self.metrics_collector.increment_task_poll(
                task_definition_name
            )

        try:
            start_time = time.time()
            domain = self.worker.get_domain()
            params = {"workerid": self.worker.get_identity()}
            if domain is not None:
                params["domain"] = domain
            task = self.task_client.poll(tasktype=task_definition_name, **params)
            finish_time = time.time()
            time_spent = finish_time - start_time
            if self.metrics_collector is not None:
                self.metrics_collector.record_task_poll_time(task_definition_name, time_spent)
        except AuthorizationException as auth_exception:
            # Track auth failure for backoff
            self._auth_failures += 1
            self._last_auth_failure = time.time()
            backoff_seconds = min(2 ** self._auth_failures, 60)

            if self.metrics_collector is not None:
                self.metrics_collector.increment_task_poll_error(task_definition_name, type(auth_exception))

            if auth_exception.invalid_token:
                logger.error(
                    f"Failed to poll task {task_definition_name} due to invalid auth token "
                    f"(failure #{self._auth_failures}). Will retry with exponential backoff ({backoff_seconds}s). "
                    "Please check your CONDUCTOR_AUTH_KEY and CONDUCTOR_AUTH_SECRET."
                )
            else:
                logger.error(
                    f"Failed to poll task {task_definition_name} error: {auth_exception.status} - {auth_exception.error_code} "
                    f"(failure #{self._auth_failures}). Will retry with exponential backoff ({backoff_seconds}s)."
                )
            return None
        except Exception as e:
            if self.metrics_collector is not None:
                self.metrics_collector.increment_task_poll_error(task_definition_name, type(e))
            logger.error(
                "Failed to poll task for: %s, reason: %s",
                task_definition_name,
                traceback.format_exc()
            )
            return None

        # Success - reset auth failure counter
        if task is not None:
            self._auth_failures = 0
            logger.trace(
                "Polled task: %s, worker_id: %s, domain: %s",
                task_definition_name,
                self.worker.get_identity(),
                self.worker.get_domain()
            )
        else:
            # No task available - also reset auth failures since poll succeeded
            self._auth_failures = 0

        return task

    def __execute_task(self, task: Task) -> TaskResult:
        if not isinstance(task, Task):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        logger.trace(
            "Executing task, id: %s, workflow_instance_id: %s, task_definition_name: %s",
            task.task_id,
            task.workflow_instance_id,
            task_definition_name
        )

        # Create initial task result for context
        initial_task_result = TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=self.worker.get_identity()
        )

        # Set task context (similar to AsyncIO implementation)
        _set_task_context(task, initial_task_result)

        # Publish TaskExecutionStarted event
        self.event_dispatcher.publish(TaskExecutionStarted(
            task_type=task_definition_name,
            task_id=task.task_id,
            worker_id=self.worker.get_identity(),
            workflow_instance_id=task.workflow_instance_id
        ))

        try:
            start_time = time.time()

            # Execute worker function - worker.execute() handles both sync and async correctly
            task_output = self.worker.execute(task)

            # Handle different return types
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
                # Regular return value - worker.execute() should have returned TaskResult
                # but if it didn't, treat the output as TaskResult
                if hasattr(task_output, 'status'):
                    task_result = task_output
                else:
                    # Shouldn't happen, but handle gracefully
                    # logger.trace(
                    #     f"Worker returned unexpected type: %s, for task {task.workflow_instance_id} / {task.task_id} wrapping in TaskResult",
                    #     type(task_output)
                    # )
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

            # Merge context modifications (logs, callback_after, etc.)
            self.__merge_context_modifications(task_result, initial_task_result)

            finish_time = time.time()
            time_spent = finish_time - start_time

            # Publish TaskExecutionCompleted event (metrics collector will handle via event)
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
                "Executed task, id: %s, workflow_instance_id: %s, task_definition_name: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name
            )
        except Exception as e:
            finish_time = time.time()
            time_spent = finish_time - start_time

            # Publish TaskExecutionFailure event (metrics collector will handle via event)
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
                "Failed to execute task, id: %s, workflow_instance_id: %s, "
                "task_definition_name: %s, reason: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name,
                traceback.format_exc()
            )
        finally:
            # Always clear task context after execution
            _clear_task_context()

        return task_result

    def __merge_context_modifications(self, task_result: TaskResult, context_result: TaskResult) -> None:
        """
        Merge modifications made via TaskContext into the final task result.

        This allows workers to use TaskContext.add_log(), set_callback_after(), etc.
        and have those modifications reflected in the final result.

        Args:
            task_result: The task result to merge into
            context_result: The context result with modifications
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

    def __update_task(self, task_result: TaskResult):
        if not isinstance(task_result, TaskResult):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        logger.debug(
            "Updating task, id: %s, workflow_instance_id: %s, task_definition_name: %s",
            task_result.task_id,
            task_result.workflow_instance_id,
            task_definition_name
        )
        for attempt in range(4):
            if attempt > 0:
                # Wait for [10s, 20s, 30s] before next attempt
                time.sleep(attempt * 10)
            try:
                response = self.task_client.update_task(body=task_result)
                logger.debug(
                    "Updated task, id: %s, workflow_instance_id: %s, task_definition_name: %s, response: %s",
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
                    "Failed to update task, id: %s, workflow_instance_id: %s, task_definition_name: %s, reason: %s",
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    traceback.format_exc()
                )
        return None

    def __wait_for_polling_interval(self) -> None:
        polling_interval = self.worker.get_polling_interval_in_seconds()
        time.sleep(polling_interval)

    def __set_worker_properties(self) -> None:
        # If multiple tasks are supplied to the same worker, then only first
        # task will be considered for setting worker properties
        task_type = self.worker.get_task_definition_name()

        domain = self.__get_property_value_from_env("domain", task_type)
        if domain:
            self.worker.domain = domain
        else:
            self.worker.domain = self.worker.get_domain()

        polling_interval = self.__get_property_value_from_env("polling_interval", task_type)
        if polling_interval:
            try:
                self.worker.poll_interval = float(polling_interval)
            except Exception:
                logger.error("error reading and parsing the polling interval value %s", polling_interval)
                self.worker.poll_interval = self.worker.get_polling_interval_in_seconds()

        if polling_interval:
            try:
                self.worker.poll_interval = float(polling_interval)
            except Exception as e:
                logger.error("Exception in reading polling interval from environment variable: %s", e)

    def __get_property_value_from_env(self, prop, task_type):
        """
        get the property from the env variable
        e.g. conductor_worker_"prop" or conductor_worker_"task_type"_"prop"
        """
        prefix = "conductor_worker"
        # Look for generic property in both case environment variables
        key = prefix + "_" + prop
        value_all = os.getenv(key, os.getenv(key.upper()))

        # Look for task specific property in both case environment variables
        key_small = prefix + "_" + task_type + "_" + prop
        key_upper = prefix.upper() + "_" + task_type + "_" + prop.upper()
        value = os.getenv(key_small, os.getenv(key_upper, value_all))
        return value
