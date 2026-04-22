import inspect
import json
import logging
import os
import sys
import time
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import List, Optional, Any

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context.task_context import _set_task_context, _clear_task_context, TaskInProgress
from conductor.client.event.task_runner_events import (
    TaskRunnerEvent, PollStarted, PollCompleted, PollFailure,
    TaskExecutionStarted, TaskExecutionCompleted, TaskExecutionFailure,
    TaskUpdateFailure
)
from conductor.client.event.sync_event_dispatcher import SyncEventDispatcher
from conductor.client.event.sync_listener_register import register_task_runner_listener
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.http.models.schema_def import SchemaDef, SchemaType
from conductor.client.http.rest import AuthorizationException, ApiException
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_schema_client import OrkesSchemaClient
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.worker.worker import ASYNC_TASK_RUNNING
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.worker.worker_config import resolve_worker_config, get_worker_config_oneline
from conductor.client.worker.exception import NonRetryableException
from conductor.client.automator.json_schema_generator import generate_json_schema_from_function
from conductor.client.automator.lease_tracker import LeaseManager

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


def _task_result_size_bytes(task_result) -> int:
    """Return the serialized JSON byte length of a TaskResult.

    We report the same bytes we'd send on the wire so output_size_bytes
    matches what the server receives, rather than the in-memory object
    footprint reported by sys.getsizeof.
    """
    if task_result is None:
        return 0
    try:
        if hasattr(task_result, "to_dict"):
            payload = task_result.to_dict()
        else:
            payload = task_result
        return len(json.dumps(payload, default=str).encode("utf-8"))
    except Exception:
        return 0


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
                configuration=self.configuration,
                metrics_collector=self.metrics_collector
            )
        )

        # Auth failure backoff tracking to prevent retry storms.
        # `_auth_failures` is capped at `_max_auth_failure_exp` so that
        # 2**N cannot overflow on a long-lived worker whose auth is broken.
        # The resulting sleep is further clamped to `_auth_backoff_cap_seconds`.
        self._auth_failures = 0
        self._last_auth_failure = 0
        self._auth_backoff_cap_seconds = 60
        self._max_auth_failure_exp = 6  # 2**6 = 64s, sleep clamped to cap

        # Generic poll-failure backoff. This is distinct from the empty-poll
        # adaptive delay (`_consecutive_empty_polls`) and from the auth-error
        # backoff above. It kicks in when batch_poll raises an exception
        # (server 5xx, NGINX 502/504 under load, DNS hiccup, a closed httpx
        # client that couldn't heal, etc.) so we don't hot-loop the log with
        # stack traces while waiting for the server to recover.
        self._poll_failures = 0
        self._last_poll_failure = 0
        self._poll_backoff_cap_seconds = 120  # max 2 minutes between retries
        self._max_poll_failure_exp = 7  # 2**7 = 128s, sleep clamped to cap

        # Thread pool for concurrent task execution
        # thread_count from worker configuration controls concurrency
        max_workers = getattr(worker, 'thread_count', 1)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"worker-{worker.get_task_definition_name()}")
        self._running_tasks = set()  # Track futures of running tasks
        self._max_workers = max_workers
        self._last_poll_time = 0  # Track last poll to avoid excessive polling when queue is empty
        self._consecutive_empty_polls = 0  # Track empty polls to implement backoff
        self._shutdown = False  # Flag to indicate graceful shutdown
        self._use_update_v2 = True  # Will be set to False if server doesn't support v2 endpoint
        self._lease_manager = LeaseManager.get_instance()
        self._tracked_task_ids = set()  # Local set for cleanup on shutdown
        self._tracked_task_ids_lock = threading.Lock()

    def run(self) -> None:
        if self.configuration is not None:
            self.configuration.apply_logging_config()
        else:
            logger.setLevel(logging.DEBUG)

        self.__install_uncaught_exception_hook()

        # Log worker configuration with correct PID (after fork)
        task_name = self.worker.get_task_definition_name()
        config_summary = get_worker_config_oneline(task_name, self._resolved_config)
        logger.info(config_summary)

        # Register task definition if configured
        if self.worker.register_task_def:
            self.__register_task_definition()

        task_names = ",".join(self.worker.task_definition_names)
        logger.debug(
            "Polling task %s with domain %s with polling interval %s",
            task_names,
            self.worker.get_domain(),
            self.worker.get_polling_interval_in_seconds()
        )

        try:
            while not self._shutdown:
                self.run_once()
        finally:
            # Cleanup resources on exit
            self._cleanup()

    def stop(self) -> None:
        """Signal the runner to stop gracefully."""
        self._shutdown = True

    def _cleanup(self) -> None:
        """Clean up resources - called on exit."""
        logger.debug("Cleaning up TaskRunner resources...")

        # Untrack all tasks this runner was tracking from the shared LeaseManager
        with self._tracked_task_ids_lock:
            task_ids = list(self._tracked_task_ids)
            self._tracked_task_ids.clear()
        for task_id in task_ids:
            self._lease_manager.untrack(task_id)

        # Shutdown ThreadPoolExecutor (EAFP style - more Pythonic)
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
            logger.debug("ThreadPoolExecutor shut down successfully")
        except AttributeError:
            pass  # No executor to shutdown
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Error shutting down executor: {e}")

        # Close HTTP client (EAFP style)
        try:
            rest_client = self.task_client.api_client.rest_client
            rest_client.close()
            logger.debug("HTTP client closed successfully")
        except AttributeError:
            pass  # No client to close or no close method
        except (IOError, OSError) as e:
            logger.warning(f"Error closing HTTP client: {e}")

        # Clear event listeners
        self.event_dispatcher = None

        logger.debug("TaskRunner cleanup completed")

    def __enter__(self):
        """Context manager entry - returns self for 'with' statement usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup even if exception occurs."""
        self._cleanup()
        return False  # Don't suppress exceptions

    def __register_task_definition(self) -> None:
        """
        Register task definition with Conductor server (if register_task_def=True).

        Automatically creates/updates:
        1. Task definition with basic metadata or provided TaskDef configuration
        2. JSON Schema for inputs (if type hints available)
        3. JSON Schema for outputs (if return type hint available)

        Schemas are named: {task_name}_input and {task_name}_output

        Note: Always registers/updates - will overwrite existing definitions and schemas.
        This ensures the server has the latest configuration from code.
        """
        task_name = self.worker.get_task_definition_name()

        logger.debug("=" * 80)
        logger.debug(f"Registering task definition: {task_name}")
        logger.debug("=" * 80)

        try:
            # Create metadata client
            logger.debug(f"Creating metadata client for task registration...")
            metadata_client = OrkesMetadataClient(self.configuration)

            # Generate JSON schemas from function signature (if worker has execute_function)
            input_schema_name = None
            output_schema_name = None
            schema_registry_available = True

            # Check if schema registration is enabled for this worker
            register_schema = getattr(self.worker, 'register_schema', False)
            # Also check global Configuration default
            if hasattr(self.configuration, 'register_schema') and self.configuration.register_schema is not None:
                # Worker-level setting takes precedence if explicitly set (not default)
                if not hasattr(self.worker, 'register_schema'):
                    register_schema = self.configuration.register_schema

            if not register_schema:
                logger.debug(f"Schema registration disabled for {task_name} (register_schema=False)")

            if register_schema and hasattr(self.worker, 'execute_function'):
                logger.debug(f"Generating JSON schemas from function signature...")
                # Pass strict_schema flag to control additionalProperties
                strict_mode = getattr(self.worker, 'strict_schema', False)
                logger.debug(f"  strict_schema mode: {strict_mode}")
                schemas = generate_json_schema_from_function(self.worker.execute_function, task_name, strict_schema=strict_mode)

                if schemas:
                    has_input_schema = schemas.get('input') is not None
                    has_output_schema = schemas.get('output') is not None

                    if has_input_schema or has_output_schema:
                        logger.debug(f"  ✓ Generated schemas: input={'Yes' if has_input_schema else 'No'}, output={'Yes' if has_output_schema else 'No'}")
                    else:
                        logger.debug(f"  ⚠ No schemas generated (type hints not fully supported)")

                    # Register schemas with schema client
                    try:
                        logger.debug(f"Creating schema client...")
                        schema_client = OrkesSchemaClient(self.configuration)
                    except Exception as e:
                        # Schema client not available (server doesn't support schemas)
                        logger.debug(f"⚠ Schema registry not available on server - task will be registered without schemas")
                        logger.debug(f"  Error: {e}")
                        schema_registry_available = False
                        schema_client = None

                    if schema_registry_available and schema_client:
                        logger.debug(f"Registering JSON schemas...")
                        try:
                            # Register input schema
                            if schemas.get('input'):
                                input_schema_name = f"{task_name}_input"
                                try:
                                    # Register schema (overwrite if exists)
                                    input_schema_def = SchemaDef(
                                        name=input_schema_name,
                                        version=1,
                                        type=SchemaType.JSON,
                                        data=schemas['input']
                                    )
                                    schema_client.register_schema(input_schema_def)
                                    logger.debug(f"  ✓ Registered input schema: {input_schema_name} (v1)")

                                except Exception as e:
                                    # Check if this is a 404 (API endpoint doesn't exist on server)
                                    if hasattr(e, 'status') and e.status == 404:
                                        logger.debug(f"⚠ Schema registry API not available on server (404) - task will be registered without schemas")
                                        schema_registry_available = False
                                        input_schema_name = None
                                    else:
                                        # Other error - log and continue without this schema
                                        logger.warning(f"⚠ Could not register input schema '{input_schema_name}': {e}")
                                        input_schema_name = None

                            # Register output schema (only if schema registry is available)
                            if schema_registry_available and schemas.get('output'):
                                output_schema_name = f"{task_name}_output"
                                try:
                                    # Register schema (overwrite if exists)
                                    output_schema_def = SchemaDef(
                                        name=output_schema_name,
                                        version=1,
                                        type=SchemaType.JSON,
                                        data=schemas['output']
                                    )
                                    schema_client.register_schema(output_schema_def)
                                    logger.debug(f"  ✓ Registered output schema: {output_schema_name} (v1)")

                                except Exception as e:
                                    # Check if this is a 404 (API endpoint doesn't exist on server)
                                    if hasattr(e, 'status') and e.status == 404:
                                        logger.debug(f"⚠ Schema registry API not available on server (404)")
                                        schema_registry_available = False
                                    else:
                                        # Other error - log and continue without this schema
                                        logger.warning(f"⚠ Could not register output schema '{output_schema_name}': {e}")
                                    output_schema_name = None

                        except Exception as e:
                            logger.debug(f"Could not register schemas for {task_name}: {e}")
                else:
                    logger.debug(f"  ⚠ No schemas generated (unable to analyze function signature)")
            elif not register_schema:
                pass  # Already logged above
            else:
                logger.debug(f"  ⚠ Class-based worker (no execute_function) - registering task without schemas")

            # Create task definition
            logger.debug(f"Creating task definition for '{task_name}'...")

            # Check if task_def_template is provided
            logger.debug(f"  task_def_template present: {hasattr(self.worker, 'task_def_template')}")
            if hasattr(self.worker, 'task_def_template'):
                logger.debug(f"  task_def_template value: {self.worker.task_def_template}")

            # Use provided task_def template if available, otherwise create minimal TaskDef
            if hasattr(self.worker, 'task_def_template') and self.worker.task_def_template:
                logger.debug(f"  Using provided TaskDef configuration:")

                # Create a copy to avoid mutating the original
                import copy
                task_def = copy.deepcopy(self.worker.task_def_template)

                # Override name to ensure consistency
                task_def.name = task_name

                # Log configuration being applied
                if task_def.retry_count:
                    logger.debug(f"    - retry_count: {task_def.retry_count}")
                if task_def.retry_logic:
                    logger.debug(f"    - retry_logic: {task_def.retry_logic}")
                if task_def.timeout_seconds:
                    logger.debug(f"    - timeout_seconds: {task_def.timeout_seconds}")
                if task_def.timeout_policy:
                    logger.debug(f"    - timeout_policy: {task_def.timeout_policy}")
                if task_def.response_timeout_seconds:
                    logger.debug(f"    - response_timeout_seconds: {task_def.response_timeout_seconds}")
                if task_def.concurrent_exec_limit:
                    logger.debug(f"    - concurrent_exec_limit: {task_def.concurrent_exec_limit}")
                if task_def.rate_limit_per_frequency:
                    logger.debug(f"    - rate_limit: {task_def.rate_limit_per_frequency}/{task_def.rate_limit_frequency_in_seconds}s")
            else:
                # Create minimal task definition
                logger.debug(f"  Creating minimal TaskDef (no custom configuration)")
                task_def = TaskDef(name=task_name)

            # Link schemas if they were generated (overrides any schemas in task_def_template)
            if input_schema_name:
                task_def.input_schema = {"name": input_schema_name, "version": 1}
                logger.debug(f"  Linked input schema: {input_schema_name}")
            if output_schema_name:
                task_def.output_schema = {"name": output_schema_name, "version": 1}
                logger.debug(f"  Linked output schema: {output_schema_name}")

            # Register/update task definition
            # Behavior depends on overwrite_task_def flag
            overwrite = getattr(self.worker, 'overwrite_task_def', True)
            logger.debug(f"  overwrite_task_def: {overwrite}")

            try:
                # Debug: Log the TaskDef being sent
                logger.debug(f"  Sending TaskDef to server:")
                logger.debug(f"    Name: {task_def.name}")
                logger.debug(f"    retry_count: {task_def.retry_count}")
                logger.debug(f"    retry_logic: {task_def.retry_logic}")
                logger.debug(f"    timeout_policy: {task_def.timeout_policy}")
                logger.debug(f"    Full to_dict(): {task_def.to_dict()}")

                if overwrite:
                    # Use update_task_def to overwrite existing definitions
                    logger.debug(f"  Using update_task_def (overwrite=True)")
                    metadata_client.update_task_def(task_def=task_def)
                else:
                    # Check if task exists, only create if it doesn't
                    logger.debug(f"  Checking if task exists before creating (overwrite=False)")
                    try:
                        existing = metadata_client.get_task_def(task_name)
                        if existing:
                            logger.info(f"✓ Task definition '{task_name}' already exists - skipping (overwrite=False)")
                            logger.debug(f"  View at: {self.configuration.ui_host}/taskDef/{task_name}")
                            return
                    except Exception:
                        # Task doesn't exist, proceed to register
                        pass
                    metadata_client.register_task_def(task_def=task_def)

                # Print success message with link
                task_def_url = f"{self.configuration.ui_host}/taskDef/{task_name}"
                logger.debug(f"✓ Registered/Updated task definition: {task_name} with {task_def.to_dict()}")
                logger.debug(f"  View at: {task_def_url}")

                if input_schema_name or output_schema_name:
                    schema_count = sum([1 for s in [input_schema_name, output_schema_name] if s])
                    logger.info(f"  With {schema_count} JSON schema(s): {', '.join(filter(None, [input_schema_name, output_schema_name]))}")

            except Exception as e:
                # If update fails (task doesn't exist), try register
                try:
                    metadata_client.register_task_def(task_def=task_def)

                    task_def_url = f"{self.configuration.ui_host}/taskDef/{task_name}"
                    logger.info(f"✓ Registered task definition: {task_name}")
                    logger.debug(f"  View at: {task_def_url}")

                    if input_schema_name or output_schema_name:
                        schema_count = sum([1 for s in [input_schema_name, output_schema_name] if s])
                        logger.info(f"  With {schema_count} JSON schema(s): {', '.join(filter(None, [input_schema_name, output_schema_name]))}")

                except Exception as register_error:
                    logger.warning(f"⚠ Could not register/update task definition '{task_name}': {register_error}")

        except Exception as e:
            # Don't crash worker if registration fails - just log warning
            logger.warning(f"Failed to register task definition for {task_name}: {e}")

    def run_once(self) -> None:
        try:
            # Check completed async tasks first (non-blocking)
            self.__check_completed_async_tasks()

            # Cleanup completed tasks immediately - this is critical for detecting available slots
            self.__cleanup_completed_tasks()

            # Check if we can accept more tasks (based on thread_count)
            # Account for pending async tasks in capacity calculation (thread-safe)
            pending_async_count = 0
            if hasattr(self.worker, '_pending_tasks_lock') and hasattr(self.worker, '_pending_async_tasks'):
                with self.worker._pending_tasks_lock:
                    pending_async_count = len(self.worker._pending_async_tasks)
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
        """Remove completed task futures from tracking set (thread-safe)"""
        # Avoid recreating the set - modify in place to prevent race conditions
        completed = [f for f in self._running_tasks if f.done()]
        for f in completed:
            self._running_tasks.discard(f)

    def __check_completed_async_tasks(self) -> None:
        """Check for completed async tasks and update Conductor"""
        if not hasattr(self.worker, 'check_completed_async_tasks'):
            return

        completed = self.worker.check_completed_async_tasks()
        if completed:
            logger.debug(f"Found {len(completed)} completed async tasks")

        for task_id, task_result, submit_time, task in completed:
            try:
                # Async task finished — stop heartbeating for it
                self._untrack_lease(task_id)

                # Calculate actual execution time (from submission to completion)
                finish_time = time.time()
                time_spent = finish_time - submit_time

                logger.debug(
                    "Async task completed: %s (task_id=%s, execution_time=%.3fs, status=%s, output_data=%s)",
                    task.task_def_name,
                    task_id,
                    time_spent,
                    task_result.status,
                    task_result.output_data
                )

                # Publish TaskExecutionCompleted event with actual execution time
                output_size = _task_result_size_bytes(task_result)
                self.event_dispatcher.publish(TaskExecutionCompleted(
                    task_type=task.task_def_name,
                    task_id=task_id,
                    worker_id=self.worker.get_identity(),
                    workflow_instance_id=task.workflow_instance_id,
                    duration_ms=time_spent * 1000,
                    output_size_bytes=output_size
                ))

                next_task = self.__update_task(task_result)
                logger.debug("Successfully updated async task %s with output %s, next_task: %s", task_id, task_result.output_data, next_task.task_id if next_task else None)

                # If v2 returned a next task, submit it to the executor
                if next_task is not None and next_task.task_id:
                    future = self._executor.submit(self.__execute_and_update_task, next_task)
                    self._running_tasks.add(future)
            except Exception as e:
                logger.error(
                    "Error updating completed async task %s: %s",
                    task_id,
                    traceback.format_exc()
                )

    def __execute_and_update_task(self, task: Task) -> None:
        """Execute task and update result in a tight loop (runs in thread pool).

        Uses the v2 update endpoint which returns the next task to process.
        Loops: execute -> update_v2 (get next task) -> execute -> ...
        The loop breaks when no next task is available, the task is async/in-progress,
        or shutdown is requested.
        """
        self._track_lease(task)
        async_running = False  # True when task is running async in background
        try:
            while task is not None and not self._shutdown:
                task_result = self.__execute_task(task)
                # If task returned None, it's an async task running in background.
                # Keep the lease tracked — __check_completed_async_tasks will untrack
                # when the async task finishes.
                if task_result is None:
                    logger.debug("Task %s is running async, will update when complete", task.task_id)
                    async_running = True
                    return
                self._untrack_lease(task.task_id)
                # Update task and get next task from v2 response
                task = self.__update_task(task_result)
                # v2 returns the next task; if v1 was used (returns None), immediately
                # poll for the next task to preserve tight-loop behaviour on older servers
                if task is None and not self._use_update_v2 and not self._shutdown:
                    tasks = self.__batch_poll_tasks(1)
                    task = tasks[0] if tasks else None
                if task is not None:
                    self._track_lease(task)
        except Exception as e:
            logger.error(
                "Error executing/updating task %s: %s",
                task.task_id if task else "unknown",
                traceback.format_exc()
            )
        finally:
            # Don't untrack if the task is still running async in the background —
            # the lease must stay active until __check_completed_async_tasks handles it.
            if task is not None and not async_running:
                self._untrack_lease(task.task_id)

    def __batch_poll_tasks(self, count: int) -> list:
        """Poll for multiple tasks at once (more efficient than polling one at a time)"""
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused:
            logger.debug("Stop polling task for: %s", task_definition_name)
            return []

        # Apply exponential backoff if we have recent auth failures.
        if self._auth_failures > 0:
            now = time.time()
            backoff_seconds = min(
                2 ** min(self._auth_failures, self._max_auth_failure_exp),
                self._auth_backoff_cap_seconds,
            )
            time_since_last_failure = now - self._last_auth_failure
            if time_since_last_failure < backoff_seconds:
                time.sleep(0.1)
                return []

        # Apply exponential backoff for generic poll failures (5xx, network
        # errors, closed-client runtime errors that couldn't self-heal, etc.).
        # Bounded at `_poll_backoff_cap_seconds` (2 min) to avoid log floods
        # without giving up on recovery.
        if self._poll_failures > 0:
            now = time.time()
            backoff_seconds = min(
                2 ** min(self._poll_failures, self._max_poll_failure_exp),
                self._poll_backoff_cap_seconds,
            )
            time_since_last_failure = now - self._last_poll_failure
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
            # Only add domain if it's not None and not empty string
            if domain is not None and domain != "":
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

            # Success - reset both failure counters (any successful HTTP
            # response means auth and connectivity are working).
            self._auth_failures = 0
            self._poll_failures = 0

            return tasks if tasks else []

        except AuthorizationException as auth_exception:
            self._auth_failures += 1
            self._last_auth_failure = time.time()
            backoff_seconds = min(
                2 ** min(self._auth_failures, self._max_auth_failure_exp),
                self._auth_backoff_cap_seconds,
            )

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

            # Bump the poll-failure counter so the next poll waits with
            # exponential backoff instead of hot-looping on a broken server
            # or connection.
            self._poll_failures += 1
            self._last_poll_failure = time.time()
            backoff_seconds = min(
                2 ** min(self._poll_failures, self._max_poll_failure_exp),
                self._poll_backoff_cap_seconds,
            )

            # Belt-and-suspenders: if the underlying httpx client got closed
            # and rest.request() couldn't heal it (e.g. because the error
            # arrived as a non-RuntimeError), nudge it here. Pass the current
            # connection as `expected` so concurrent threads racing to heal
            # can't cause a reset storm: only the first caller per client
            # generation actually replaces it.
            try:
                rest_client = getattr(
                    getattr(self.task_client, "api_client", None),
                    "rest_client",
                    None,
                )
                if rest_client is not None and getattr(rest_client, "_is_client_closed", lambda: False)():
                    current_conn = getattr(rest_client, "connection", None)
                    reset = rest_client._reset_connection(expected=current_conn)
                    if reset:
                        logger.warning(
                            "rest_client was closed after poll failure; reset"
                        )
            except Exception:
                # Healing is best-effort; never let it mask the original error.
                pass

            # Log a single-line warning at a modest level to avoid drowning
            # ops in tracebacks when the server is flapping. Full traceback
            # goes to debug for when operators need it.
            logger.warning(
                "Failed to batch poll task for: %s (failure #%d). Will retry with exponential backoff (%ss). Reason: %s: %s",
                task_definition_name,
                self._poll_failures,
                backoff_seconds,
                type(e).__name__,
                e,
            )
            logger.debug(
                "batch poll failure traceback for %s:\n%s",
                task_definition_name,
                traceback.format_exc(),
            )
            return []

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

            # If worker returned ASYNC_TASK_RUNNING sentinel, it's an async task running in background
            # Don't create TaskResult or publish events - will be handled when task completes
            # Note: This allows async tasks to legitimately return None as their result
            if task_output is ASYNC_TASK_RUNNING:
                _clear_task_context()
                return None

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
            output_size = _task_result_size_bytes(task_result)
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
        except NonRetryableException as ne:
            # Non-retryable exception - task fails with terminal error (no retries)
            finish_time = time.time()
            time_spent = finish_time - start_time

            # Publish TaskExecutionFailure event
            self.event_dispatcher.publish(TaskExecutionFailure(
                task_type=task_definition_name,
                task_id=task.task_id,
                worker_id=self.worker.get_identity(),
                workflow_instance_id=task.workflow_instance_id,
                cause=ne,
                duration_ms=time_spent * 1000
            ))

            task_result = TaskResult(
                task_id=task.task_id,
                workflow_instance_id=task.workflow_instance_id,
                worker_id=self.worker.get_identity()
            )
            task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
            task_result.reason_for_incompletion = str(ne) if str(ne) else "NonRetryableException"
            task_result.logs = [TaskExecLog(
                traceback.format_exc(), task_result.task_id, int(time.time()))]

            logger.error(
                "Task failed with terminal error (no retry), id: %s, workflow_instance_id: %s, "
                "task_definition_name: %s, reason: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name,
                str(ne)
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
        """Update task result using v2 endpoint. Returns the next Task to process, or None."""
        if not isinstance(task_result, TaskResult):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        logger.debug(
            "Updating task, id: %s, workflow_instance_id: %s, task_definition_name: %s, status: %s, output_data: %s",
            task_result.task_id,
            task_result.workflow_instance_id,
            task_definition_name,
            task_result.status,
            task_result.output_data
        )

        last_exception = None
        retry_count = 4

        for attempt in range(retry_count):
            if attempt > 0:
                # Exponential backoff: [10s, 20s, 30s] before retry
                time.sleep(attempt * 10)
            update_start = time.time()
            try:
                if self._use_update_v2:
                    next_task = self.task_client.update_task_v2(body=task_result)
                    logger.debug(
                        "Updated task (v2), id: %s, workflow_instance_id: %s, task_definition_name: %s, next_task: %s",
                        task_result.task_id,
                        task_result.workflow_instance_id,
                        task_definition_name,
                        next_task.task_id if next_task else None
                    )
                    if self.metrics_collector is not None:
                        self.metrics_collector.record_task_update_time_histogram(
                            task_definition_name, time.time() - update_start, status="SUCCESS"
                        )
                    return next_task
                else:
                    self.task_client.update_task(body=task_result)
                    logger.debug(
                        "Updated task (v1), id: %s, workflow_instance_id: %s, task_definition_name: %s",
                        task_result.task_id,
                        task_result.workflow_instance_id,
                        task_definition_name,
                    )
                    if self.metrics_collector is not None:
                        self.metrics_collector.record_task_update_time_histogram(
                            task_definition_name, time.time() - update_start, status="SUCCESS"
                        )
                    return None
            except ApiException as e:
                if e.status in (404, 405) and self._use_update_v2:
                    logger.warning(
                        "Server does not support update-task-v2 endpoint (HTTP %d). "
                        "Falling back to v1 update endpoint. "
                        "Upgrade your Orkes instance to v5+ to enable the v2 endpoint.",
                        e.status,
                    )
                    self._use_update_v2 = False
                    # Retry immediately with v1
                    try:
                        self.task_client.update_task(body=task_result)
                        if self.metrics_collector is not None:
                            self.metrics_collector.record_task_update_time_histogram(
                                task_definition_name, time.time() - update_start, status="SUCCESS"
                            )
                        return None
                    except Exception as fallback_e:
                        last_exception = fallback_e
                        if self.metrics_collector is not None:
                            self.metrics_collector.record_task_update_time_histogram(
                                task_definition_name, time.time() - update_start, status="FAILURE"
                            )
                        continue
                last_exception = e
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_update_error(
                        task_definition_name, type(e)
                    )
                    self.metrics_collector.record_task_update_time_histogram(
                        task_definition_name, time.time() - update_start, status="FAILURE"
                    )
                is_last_attempt = (attempt + 1) >= retry_count
                # Known recoverable transport hiccups (stale keep-alive,
                # HTTP/2 GOAWAY race, client closed mid-request) are flagged
                # `transient=True` by the REST layer after it self-heals. For
                # those, skip the stack trace until the final attempt — the
                # retry normally succeeds immediately and a full traceback per
                # in-flight task just spams the log.
                if getattr(e, "transient", False) and not is_last_attempt:
                    logger.warning(
                        "Transient transport error updating task; will retry (attempt %d/%d), id: %s, workflow_instance_id: %s, task_definition_name: %s, reason: %s",
                        attempt + 1,
                        retry_count,
                        task_result.task_id,
                        task_result.workflow_instance_id,
                        task_definition_name,
                        getattr(e, "reason", None) or str(e),
                    )
                else:
                    logger.error(
                        "Failed to update task (attempt %d/%d), id: %s, workflow_instance_id: %s, task_definition_name: %s, reason: %s",
                        attempt + 1,
                        retry_count,
                        task_result.task_id,
                        task_result.workflow_instance_id,
                        task_definition_name,
                        traceback.format_exc()
                    )
                continue
            except Exception as e:
                last_exception = e
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_update_error(
                        task_definition_name, type(e)
                    )
                    self.metrics_collector.record_task_update_time_histogram(
                        task_definition_name, time.time() - update_start, status="FAILURE"
                    )
                logger.error(
                    "Failed to update task (attempt %d/%d), id: %s, workflow_instance_id: %s, task_definition_name: %s, reason: %s",
                    attempt + 1,
                    retry_count,
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    traceback.format_exc()
                )

        # All retries exhausted - publish critical failure event
        logger.critical(
            "Task update failed after %d attempts. Task result LOST for task_id: %s, workflow: %s",
            retry_count,
            task_result.task_id,
            task_result.workflow_instance_id
        )

        # Publish TaskUpdateFailure event for external handling
        self.event_dispatcher.publish(TaskUpdateFailure(
            task_type=task_definition_name,
            task_id=task_result.task_id,
            worker_id=self.worker.get_identity(),
            workflow_instance_id=task_result.workflow_instance_id,
            cause=last_exception,
            retry_count=retry_count,
            task_result=task_result
        ))

        return None

    # -- Lease extension (heartbeat) delegation to LeaseManager ----------------

    def _track_lease(self, task: Task) -> None:
        """Start tracking a task for lease extension via the shared LeaseManager."""
        if not getattr(self.worker, 'lease_extend_enabled', False):
            return
        timeout = getattr(task, 'response_timeout_seconds', None) or 0
        if timeout <= 0:
            return
        self._lease_manager.track(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            response_timeout_seconds=timeout,
            task_client=self.task_client,
        )
        with self._tracked_task_ids_lock:
            self._tracked_task_ids.add(task.task_id)

    def _untrack_lease(self, task_id: str) -> None:
        """Stop tracking a task for lease extension."""
        self._lease_manager.untrack(task_id)
        with self._tracked_task_ids_lock:
            self._tracked_task_ids.discard(task_id)

    # --------------------------------------------------------------------------

    def __wait_for_polling_interval(self) -> None:
        polling_interval = self.worker.get_polling_interval_in_seconds()
        time.sleep(polling_interval)

    def __install_uncaught_exception_hook(self) -> None:
        """
        Install a ``threading.excepthook`` so that uncaught exceptions in
        any thread within this worker subprocess are reflected into the
        canonical ``thread_uncaught_exceptions_total`` counter (bounded
        ``exception`` label = class name), mirroring Java / Go.

        We chain to the previously-installed hook to preserve default
        logging behaviour.
        """
        if self.metrics_collector is None:
            return

        try:
            previous_hook = threading.excepthook

            def _conductor_thread_excepthook(args: "threading.ExceptHookArgs") -> None:  # type: ignore[name-defined]
                try:
                    self.metrics_collector.increment_uncaught_exception(args.exc_value)
                except Exception:
                    pass
                try:
                    if previous_hook is not None:
                        previous_hook(args)
                except Exception:
                    pass

            threading.excepthook = _conductor_thread_excepthook
        except Exception as e:
            logger.debug("Failed to install threading.excepthook: %s", e)

    def __set_worker_properties(self) -> None:
        """
        Resolve worker configuration using hierarchical override (env vars > code defaults).
        Note: Logging is done in run() to capture the correct PID (after fork).
        """
        task_name = self.worker.get_task_definition_name()

        # Resolve configuration with hierarchical override
        # Use getattr with defaults to handle workers that don't have all attributes
        resolved_config = resolve_worker_config(
            worker_name=task_name,
            poll_interval=getattr(self.worker, 'poll_interval', None),
            domain=getattr(self.worker, 'domain', None),
            worker_id=getattr(self.worker, 'worker_id', None),
            thread_count=getattr(self.worker, 'thread_count', 1),
            register_task_def=getattr(self.worker, 'register_task_def', False),
            poll_timeout=getattr(self.worker, 'poll_timeout', 100),
            lease_extend_enabled=getattr(self.worker, 'lease_extend_enabled', False),
            paused=getattr(self.worker, 'paused', False),
            overwrite_task_def=getattr(self.worker, 'overwrite_task_def', True),
            strict_schema=getattr(self.worker, 'strict_schema', False)
        )

        # Apply resolved configuration to worker
        # Only set attributes if they have non-None values
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
        if resolved_config.get('overwrite_task_def') is not None:
            self.worker.overwrite_task_def = resolved_config['overwrite_task_def']
        if resolved_config.get('strict_schema') is not None:
            self.worker.strict_schema = resolved_config['strict_schema']

        # Store resolved config for logging in run() (after fork)
        self._resolved_config = resolved_config

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
