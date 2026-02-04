import inspect
import logging
import os
import sys
import threading
import time
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
from conductor.client.http.rest import AuthorizationException
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_schema_client import OrkesSchemaClient
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.worker.worker import ASYNC_TASK_RUNNING
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.worker.worker_config import resolve_worker_config, get_worker_config_oneline
from conductor.client.worker.exception import NonRetryableException
from conductor.client.automator.json_schema_generator import generate_json_schema_from_function

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


class TaskRunner:
    def __init__(
            self,
            worker: WorkerInterface,
            configuration: Configuration = None,  # Accepts single or list for multi-homed
            metrics_settings: MetricsSettings = None,
            event_listeners: list = None
    ):
        if not isinstance(worker, WorkerInterface):
            raise Exception("Invalid worker")
        self.worker = worker
        self.__set_worker_properties()
        
        # Normalize configuration to list (multi-homed support)
        # Accepts: None, single Configuration, or List[Configuration]
        if configuration is None:
            self.configurations = [Configuration()]
        elif isinstance(configuration, list):
            self.configurations = configuration
        else:
            self.configurations = [configuration]

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

        # Create one task client per server (multi-homed support)
        self.task_clients = []
        for cfg in self.configurations:
            task_client = TaskResourceApi(
                ApiClient(
                    configuration=cfg,
                    metrics_collector=self.metrics_collector
                )
            )
            self.task_clients.append(task_client)
        
        # Track which server each task came from: {task_id: server_index}
        # Thread-safe: accessed from poll thread and executor threads
        self._task_server_map = {}
        self._task_server_map_lock = threading.Lock()

        # Auth failure backoff tracking per server
        self._auth_failures = [0] * len(self.configurations)
        self._last_auth_failure = [0] * len(self.configurations)
        
        # Circuit breaker per server (for multi-homed resilience)
        self._server_failures = [0] * len(self.configurations)
        self._circuit_open_until = [0.0] * len(self.configurations)
        self._CIRCUIT_FAILURE_THRESHOLD = 3  # failures before opening circuit
        self._CIRCUIT_RESET_SECONDS = 30  # seconds before half-open retry
        self._POLL_TIMEOUT_SECONDS = 5  # max time to wait for any server poll

        # Thread pool for concurrent task execution
        # thread_count from worker configuration controls concurrency
        max_workers = getattr(worker, 'thread_count', 1)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"worker-{worker.get_task_definition_name()}")
        self._running_tasks = set()  # Track futures of running tasks
        self._max_workers = max_workers
        self._last_poll_time = 0  # Track last poll to avoid excessive polling when queue is empty
        self._consecutive_empty_polls = 0  # Track empty polls to implement backoff
        self._shutdown = False  # Flag to indicate graceful shutdown
        
        # Reusable poll executor for multi-homed parallel polling
        if len(self.configurations) > 1:
            self._poll_executor = ThreadPoolExecutor(
                max_workers=len(self.configurations),
                thread_name_prefix=f"poll-{worker.get_task_definition_name()}"
            )
        else:
            self._poll_executor = None

    def run(self) -> None:
        # Apply logging config from primary configuration
        if self.configurations:
            self.configurations[0].apply_logging_config()
        else:
            logger.setLevel(logging.DEBUG)

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

        # Shutdown ThreadPoolExecutor (EAFP style - more Pythonic)
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
            logger.debug("ThreadPoolExecutor shut down successfully")
        except AttributeError:
            pass  # No executor to shutdown
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Error shutting down executor: {e}")
        
        # Shutdown poll executor if exists (multi-homed mode)
        if self._poll_executor is not None:
            try:
                self._poll_executor.shutdown(wait=False, cancel_futures=True)
                logger.debug("Poll executor shut down successfully")
            except (RuntimeError, ValueError) as e:
                logger.warning(f"Error shutting down poll executor: {e}")

        # Close HTTP clients for all servers (multi-homed support)
        for i, task_client in enumerate(self.task_clients):
            try:
                rest_client = task_client.api_client.rest_client
                rest_client.close()
                logger.debug(f"HTTP client {i + 1} closed successfully")
            except AttributeError:
                pass  # No client to close or no close method
            except (IOError, OSError) as e:
                logger.warning(f"Error closing HTTP client {i + 1}: {e}")

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
        Register task definition with Conductor server(s) (if register_task_def=True).

        In multi-homed mode, registers to ALL configured servers.

        Automatically creates/updates:
        1. Task definition with basic metadata or provided TaskDef configuration
        2. JSON Schema for inputs (if type hints available)
        3. JSON Schema for outputs (if return type hint available)

        Schemas are named: {task_name}_input and {task_name}_output

        Note: Always registers/updates - will overwrite existing definitions and schemas.
        This ensures the server has the latest configuration from code.
        """
        task_name = self.worker.get_task_definition_name()

        logger.info("=" * 80)
        logger.info(f"Registering task definition: {task_name} to {len(self.configurations)} server(s)")
        logger.info("=" * 80)

        # Generate JSON schemas once (same for all servers)
        input_schema_name = None
        output_schema_name = None
        schemas = None

        if hasattr(self.worker, 'execute_function'):
            logger.info(f"Generating JSON schemas from function signature...")
            strict_mode = getattr(self.worker, 'strict_schema', False)
            logger.debug(f"  strict_schema mode: {strict_mode}")
            schemas = generate_json_schema_from_function(self.worker.execute_function, task_name, strict_schema=strict_mode)

            if schemas:
                has_input_schema = schemas.get('input') is not None
                has_output_schema = schemas.get('output') is not None
                if has_input_schema or has_output_schema:
                    logger.info(f"  ✓ Generated schemas: input={'Yes' if has_input_schema else 'No'}, output={'Yes' if has_output_schema else 'No'}")
                    input_schema_name = f"{task_name}_input" if has_input_schema else None
                    output_schema_name = f"{task_name}_output" if has_output_schema else None

        # Build task definition once (same for all servers)
        if hasattr(self.worker, 'task_def_template') and self.worker.task_def_template:
            import copy
            task_def = copy.deepcopy(self.worker.task_def_template)
            task_def.name = task_name
        else:
            task_def = TaskDef(name=task_name)



        overwrite = getattr(self.worker, 'overwrite_task_def', True)

        # Register to each server
        for server_idx, config in enumerate(self.configurations):
            server_label = f"server {server_idx + 1}/{len(self.configurations)}"
            try:
                logger.info(f"Registering to {server_label}: {config.host}")
                metadata_client = OrkesMetadataClient(config)

                # Register schemas if available
                input_schema_registered = False
                output_schema_registered = False
                if schemas and (schemas.get('input') or schemas.get('output')):
                    try:
                        schema_client = OrkesSchemaClient(config)
                        if schemas.get('input'):
                            input_schema_def = SchemaDef(
                                name=input_schema_name,
                                version=1,
                                type=SchemaType.JSON,
                                data=schemas['input']
                            )
                            schema_client.register_schema(input_schema_def)
                            input_schema_registered = True
                            logger.debug(f"  ✓ Registered input schema on {server_label}")
                        if schemas.get('output'):
                            output_schema_def = SchemaDef(
                                name=output_schema_name,
                                version=1,
                                type=SchemaType.JSON,
                                data=schemas['output']
                            )
                            schema_client.register_schema(output_schema_def)
                            output_schema_registered = True
                            logger.debug(f"  ✓ Registered output schema on {server_label}")
                    except Exception as e:
                        logger.warning(f"⚠ Could not register schemas on {server_label}: {e}")

                # Register task definition
                try:
                    # For single server, modify usage of task_def directly to preserve object identity (helps tests)
                    # For multi-server, clone to ensure isolation
                    if len(self.configurations) == 1:
                        server_task_def = task_def
                    else:
                        import copy
                        server_task_def = copy.deepcopy(task_def)
                    
                    # Link schemas ONLY if successfully registered on THIS server
                    if input_schema_registered and input_schema_name:
                         server_task_def.input_schema = {"name": input_schema_name, "version": 1}
                    if output_schema_registered and output_schema_name:
                         server_task_def.output_schema = {"name": output_schema_name, "version": 1}

                    if overwrite:
                        metadata_client.update_task_def(task_def=server_task_def)
                    else:
                        try:
                            existing = metadata_client.get_task_def(task_name)
                            if existing:
                                logger.info(f"  ✓ Task already exists on {server_label} - skipping (overwrite=False)")
                                continue
                        except Exception:
                            pass
                        metadata_client.register_task_def(task_def=server_task_def)
                    
                    logger.info(f"  ✓ Registered task definition on {server_label}")

                except Exception as e:
                    # Try register if update fails
                    try:
                        metadata_client.register_task_def(task_def=task_def)
                        logger.info(f"  ✓ Registered task definition on {server_label}")
                    except Exception as register_error:
                        logger.warning(f"⚠ Could not register task on {server_label}: {register_error}")

            except Exception as e:
                logger.warning(f"Failed to register task definition on {server_label}: {e}")

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
                output_size = sys.getsizeof(task_result) if task_result else 0
                self.event_dispatcher.publish(TaskExecutionCompleted(
                    task_type=task.task_def_name,
                    task_id=task_id,
                    worker_id=self.worker.get_identity(),
                    workflow_instance_id=task.workflow_instance_id,
                    duration_ms=time_spent * 1000,
                    output_size_bytes=output_size
                ))

                update_response = self.__update_task(task_result)
                logger.debug("Successfully updated async task %s with output %s, response: %s", task_id, task_result.output_data, update_response)
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
            # If task returned None, it's an async task running in background - don't update yet
            # (Note: __execute_task returns None for async tasks, regardless of their actual return value)
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
        """Poll for multiple tasks from all servers in parallel (multi-homed support)."""
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused:
            logger.debug("Stop polling task for: %s", task_definition_name)
            return []

        if not self.task_clients:
            return []

        # Divide capacity across servers evenly
        # e.g., count=10, clients=3 -> [4, 3, 3]
        total_servers = len(self.task_clients)
        base_count = count // total_servers
        remainder = count % total_servers

        # Publish PollStarted event
        self.event_dispatcher.publish(PollStarted(
            task_type=task_definition_name,
            worker_id=self.worker.get_identity(),
            poll_count=count
        ))

        start_time = time.time()
        all_tasks = []
        domain = self.worker.get_domain()

        def poll_single_server(server_idx: int, task_client: TaskResourceApi) -> tuple:
            """Poll a single server and return (server_idx, tasks, error)."""
            now = time.time()
            
            # Calculate specific count for this server
            # Distribute remainder to first N servers
            server_count = base_count + (1 if server_idx < remainder else 0)
            
            # Don't poll if count is 0 (unless we have plenty of thread capacity, but let's be strict)
            if server_count <= 0:
                return (server_idx, [], None)
            
            # Circuit breaker: skip if circuit is open
            if self._circuit_open_until[server_idx] > now:
                # Circuit is open, skip this server
                return (server_idx, [], None)
            
            # Check per-server auth backoff
            if self._auth_failures[server_idx] > 0:
                backoff_seconds = min(2 ** self._auth_failures[server_idx], 60)
                time_since_failure = now - self._last_auth_failure[server_idx]
                if time_since_failure < backoff_seconds:
                    return (server_idx, [], None)

            try:
                params = {
                    "workerid": self.worker.get_identity(),
                    "count": server_count,
                    "timeout": 100  # ms
                }
                if domain is not None and domain != "":
                    params["domain"] = domain

                tasks = task_client.batch_poll(tasktype=task_definition_name, **params)
                
                # Reset failures on success
                if tasks:
                    self._auth_failures[server_idx] = 0
                    self._server_failures[server_idx] = 0
                
                return (server_idx, tasks or [], None)

            except AuthorizationException as auth_exception:
                self._auth_failures[server_idx] += 1
                self._last_auth_failure[server_idx] = time.time()
                backoff = min(2 ** self._auth_failures[server_idx], 60)
                logger.error(
                    f"Auth failure polling server {server_idx} for {task_definition_name}: "
                    f"{auth_exception.error_code} (backoff: {backoff}s)"
                )
                return (server_idx, [], auth_exception)

            except Exception as e:
                # Increment failure count for circuit breaker
                self._server_failures[server_idx] += 1
                if self._server_failures[server_idx] >= self._CIRCUIT_FAILURE_THRESHOLD:
                    self._circuit_open_until[server_idx] = time.time() + self._CIRCUIT_RESET_SECONDS
                    logger.warning(
                        f"Circuit breaker OPEN for server {server_idx} after {self._server_failures[server_idx]} failures. "
                        f"Will retry in {self._CIRCUIT_RESET_SECONDS}s"
                    )
                else:
                    logger.error(
                        f"Failed to poll server {server_idx} for {task_definition_name}: {e} "
                        f"(failure {self._server_failures[server_idx]}/{self._CIRCUIT_FAILURE_THRESHOLD})"
                    )
                return (server_idx, [], e)

        # Single server: poll directly without executor overhead
        if len(self.task_clients) == 1:
            server_idx, tasks, error = poll_single_server(0, self.task_clients[0])
            for task in tasks:
                if task and task.task_id:
                    with self._task_server_map_lock:
                        self._task_server_map[task.task_id] = server_idx
                    all_tasks.append(task)
        else:
            # Multi-homed: poll all servers in parallel with timeout
            futures = {
                self._poll_executor.submit(poll_single_server, idx, client): idx
                for idx, client in enumerate(self.task_clients)
            }

            try:
                # Use timeout to avoid slow server blocking all polling
                for future in as_completed(futures, timeout=self._POLL_TIMEOUT_SECONDS):
                    try:
                        server_idx, tasks, error = future.result(timeout=0)
                        
                        if error:
                            self.event_dispatcher.publish(PollFailure(
                                task_type=task_definition_name,
                                cause=error,
                                duration_ms=int((time.time() - start_time) * 1000)
                            ))

                        for task in tasks:
                            if task and task.task_id:
                                # Track which server this task came from (thread-safe)
                                with self._task_server_map_lock:
                                    self._task_server_map[task.task_id] = server_idx
                                all_tasks.append(task)
                    except Exception as e:
                        logger.debug(f"Error getting poll result: {e}")
            except TimeoutError:
                # Some servers didn't respond in time - continue with tasks we have
                logger.debug(
                    f"Poll timeout after {self._POLL_TIMEOUT_SECONDS}s - some servers did not respond"
                )

        finish_time = time.time()
        time_spent = finish_time - start_time

        # Publish PollCompleted event
        self.event_dispatcher.publish(PollCompleted(
            task_type=task_definition_name,
            duration_ms=time_spent * 1000,
            tasks_received=len(all_tasks)
        ))

        if len(self.task_clients) > 1 and all_tasks:
            logger.debug(
                f"Polled {len(all_tasks)} tasks from {len(self.task_clients)} servers for {task_definition_name}"
            )

        return all_tasks

    def __poll_task(self) -> Task:
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused:
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
            # Only add domain if it's not None and not empty string
            if domain is not None and domain != "":
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
        if not isinstance(task_result, TaskResult):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        
        # Get the correct server for this task (thread-safe, multi-homed support)
        with self._task_server_map_lock:
            server_idx = self._task_server_map.pop(task_result.task_id, 0)
        task_client = self.task_clients[server_idx]
        
        logger.debug(
            "Updating task, id: %s, workflow_instance_id: %s, task_definition_name: %s, status: %s, server: %d",
            task_result.task_id,
            task_result.workflow_instance_id,
            task_definition_name,
            task_result.status,
            server_idx
        )

        last_exception = None
        retry_count = 4

        for attempt in range(retry_count):
            if attempt > 0:
                # Exponential backoff: [10s, 20s, 30s] before retry
                time.sleep(attempt * 10)
            try:
                response = task_client.update_task(body=task_result)
                logger.debug(
                    "Updated task, id: %s, workflow_instance_id: %s, task_definition_name: %s, response: %s",
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    response
                )
                return response
            except Exception as e:
                last_exception = e
                if self.metrics_collector is not None:
                    self.metrics_collector.increment_task_update_error(
                        task_definition_name, type(e)
                    )
                logger.error(
                    "Failed to update task (attempt %d/%d), id: %s, workflow_instance_id: %s, task_definition_name: %s, server: %d, reason: %s",
                    attempt + 1,
                    retry_count,
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    server_idx,
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

    def __wait_for_polling_interval(self) -> None:
        polling_interval = self.worker.get_polling_interval_in_seconds()
        time.sleep(polling_interval)

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
