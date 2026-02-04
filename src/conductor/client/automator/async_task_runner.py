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
    TaskExecutionStarted, TaskExecutionCompleted, TaskExecutionFailure,
    TaskUpdateFailure
)
from conductor.client.event.sync_event_dispatcher import SyncEventDispatcher
from conductor.client.event.sync_listener_register import register_task_runner_listener
from conductor.client.http.api.async_task_resource_api import AsyncTaskResourceApi
from conductor.client.http.async_api_client import AsyncApiClient
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
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.worker.worker_config import resolve_worker_config, get_worker_config_oneline
from conductor.client.worker.exception import NonRetryableException
from conductor.client.automator.json_schema_generator import generate_json_schema_from_function

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

        # Don't create async HTTP clients here - will be created in subprocess
        # httpx.AsyncClient is not picklable, so we defer creation until after fork
        self.async_task_clients = []  # One per server (multi-homed)
        
        # Track which server each task came from: {task_id: server_index}
        self._task_server_map = {}

        # Auth failure backoff tracking per server (multi-homed)
        self._auth_failures = [0] * len(self.configurations)
        self._last_auth_failure = [0] * len(self.configurations)
        
        # Circuit breaker per server (for multi-homed resilience)
        self._server_failures = [0] * len(self.configurations)
        self._circuit_open_until = [0.0] * len(self.configurations)
        self._CIRCUIT_FAILURE_THRESHOLD = 3  # failures before opening circuit
        self._CIRCUIT_RESET_SECONDS = 30  # seconds before half-open retry
        self._POLL_TIMEOUT_SECONDS = 5  # max time to wait for any server poll

        # Polling state tracking (same as TaskRunner)
        self._max_workers = getattr(worker, 'thread_count', 1)  # Max concurrent tasks
        self._running_tasks = set()  # Track running asyncio tasks
        self._last_poll_time = 0
        self._consecutive_empty_polls = 0

        # Semaphore will be created in run() within the event loop
        self._semaphore = None
        self._shutdown = False  # Flag to indicate graceful shutdown

    async def run(self) -> None:
        """Main async loop - runs continuously in single event loop."""
        # Apply logging config from primary configuration
        if self.configurations:
            self.configurations[0].apply_logging_config()
        else:
            logger.setLevel(logging.DEBUG)

        # Create async HTTP clients for all servers after fork (multi-homed support)
        # httpx.AsyncClient is not picklable, so we must create them here
        self.async_task_clients = []
        for cfg in self.configurations:
            async_api_client = AsyncApiClient(
                configuration=cfg,
                metrics_collector=self.metrics_collector
            )
            async_task_client = AsyncTaskResourceApi(
                api_client=async_api_client
            )
            self.async_task_clients.append(async_task_client)

        # Create semaphore in the event loop (must be created within the loop)
        self._semaphore = asyncio.Semaphore(self._max_workers)

        # Log worker configuration with correct PID (after fork)
        task_name = self.worker.get_task_definition_name()
        config_summary = get_worker_config_oneline(task_name, self._resolved_config)
        logger.info(config_summary)

        # Register task definition if configured
        if self.worker.register_task_def:
            await self.__async_register_task_definition()

        task_names = ",".join(self.worker.task_definition_names)
        logger.debug(
            "Async polling task %s with domain %s with polling interval %s",
            task_names,
            self.worker.get_domain(),
            self.worker.get_polling_interval_in_seconds()
        )

        try:
            while not self._shutdown:
                await self.run_once()
        finally:
            # Cleanup resources on exit
            await self._cleanup()

    async def stop(self) -> None:
        """Signal the runner to stop gracefully."""
        self._shutdown = True

    async def _cleanup(self) -> None:
        """Clean up async resources."""
        logger.debug("Cleaning up AsyncTaskRunner resources...")

        # Cancel any running tasks (EAFP style)
        try:
            for task in list(self._running_tasks):
                if not task.done():
                    task.cancel()
        except AttributeError:
            pass  # No tasks to cancel

        # Close async HTTP clients for all servers (multi-homed support)
        for i, task_client in enumerate(self.async_task_clients):
            try:
                await task_client.api_client.close()
                logger.debug(f"Async API client {i + 1} closed successfully")
            except (IOError, OSError) as e:
                logger.warning(f"Error closing async client {i + 1}: {e}")
            except AttributeError:
                pass  # No client to close

        # Clear event listeners
        self.event_dispatcher = None

        logger.debug("AsyncTaskRunner cleanup completed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self._cleanup()
        return False  # Don't suppress exceptions

    async def __async_register_task_definition(self) -> None:
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
        This is the async version - uses sync clients since they work in async context.
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

        # Link schemas if generated
        if input_schema_name:
            task_def.input_schema = {"name": input_schema_name, "version": 1}
        if output_schema_name:
            task_def.output_schema = {"name": output_schema_name, "version": 1}

        overwrite = getattr(self.worker, 'overwrite_task_def', True)

        # Register to each server
        for server_idx, config in enumerate(self.configurations):
            server_label = f"server {server_idx + 1}/{len(self.configurations)}"
            try:
                logger.info(f"Registering to {server_label}: {config.host}")
                metadata_client = OrkesMetadataClient(config)

                # Register schemas if available
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
                            logger.debug(f"  ✓ Registered input schema on {server_label}")
                        if schemas.get('output'):
                            output_schema_def = SchemaDef(
                                name=output_schema_name,
                                version=1,
                                type=SchemaType.JSON,
                                data=schemas['output']
                            )
                            schema_client.register_schema(output_schema_def)
                            logger.debug(f"  ✓ Registered output schema on {server_label}")
                    except Exception as e:
                        logger.warning(f"⚠ Could not register schemas on {server_label}: {e}")

                # Register task definition
                try:
                    if overwrite:
                        metadata_client.update_task_def(task_def=task_def)
                    else:
                        try:
                            existing = metadata_client.get_task_def(task_name)
                            if existing:
                                logger.info(f"  ✓ Task already exists on {server_label} - skipping (overwrite=False)")
                                continue
                        except Exception:
                            pass
                        metadata_client.register_task_def(task_def=task_def)

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

    async def run_once(self) -> None:
        """Execute one iteration of the polling loop (async version)."""
        try:
            # No need for manual cleanup - tasks remove themselves via add_done_callback
            # Just check capacity directly
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

    async def __async_batch_poll(self, count: int) -> list:
        """Async batch poll for multiple tasks from all servers in parallel (multi-homed support)."""
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused:
            logger.debug("Stop polling task for: %s", task_definition_name)
            return []

        # Divide capacity across servers evenly
        # e.g., count=10, clients=3 -> [4, 3, 3]
        total_servers = len(self.async_task_clients)
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

        async def poll_single_server(server_idx: int, task_client) -> tuple:
            """Poll a single server and return (server_idx, tasks, error)."""
            now = time.time()
            
            # Calculate specific count for this server
            # Distribute remainder to first N servers
            server_count = base_count + (1 if server_idx < remainder else 0)
            
            # Don't poll if count is 0
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

                tasks = await task_client.batch_poll(tasktype=task_definition_name, **params)
                
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

        # Single server: poll directly
        if len(self.async_task_clients) == 1:
            server_idx, tasks, error = await poll_single_server(0, self.async_task_clients[0])
            for task in tasks:
                if task and task.task_id:
                    self._task_server_map[task.task_id] = server_idx
                    all_tasks.append(task)
        else:
            # Multi-homed: poll all servers in parallel with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*[
                        poll_single_server(idx, client)
                        for idx, client in enumerate(self.async_task_clients)
                    ], return_exceptions=True),
                    timeout=self._POLL_TIMEOUT_SECONDS
                )
                
                # Merge results and track task-to-server mapping
                for result in results:
                    if isinstance(result, Exception):
                        logger.debug(f"Poll exception: {result}")
                        continue
                    server_idx, tasks, error = result
                    for task in tasks:
                        if task and task.task_id:
                            self._task_server_map[task.task_id] = server_idx
                            all_tasks.append(task)
                            
            except asyncio.TimeoutError:
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

        if len(self.async_task_clients) > 1 and all_tasks:
            logger.debug(
                f"Polled {len(all_tasks)} tasks from {len(self.async_task_clients)} servers for {task_definition_name}"
            )

        return all_tasks

    async def __async_execute_and_update_task(self, task: Task) -> None:
        """Execute task and update result (async version - runs in event loop, not thread pool)."""
        # Acquire semaphore for entire task lifecycle (execution + update)
        # This ensures we never exceed thread_count tasks in any stage of processing
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
                "Async task failed with terminal error (no retry), id: %s, workflow_instance_id: %s, "
                "task_definition_name: %s, reason: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name,
                str(ne)
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
        """Async update task result to the correct server (multi-homed support)."""
        if not isinstance(task_result, TaskResult):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        
        # Get the correct server for this task (multi-homed support)
        server_idx = self._task_server_map.pop(task_result.task_id, 0)
        task_client = self.async_task_clients[server_idx]
        
        logger.debug(
            "Updating async task, id: %s, workflow_instance_id: %s, task_definition_name: %s, status: %s, server: %d",
            task_result.task_id,
            task_result.workflow_instance_id,
            task_definition_name,
            task_result.status,
            server_idx
        )

        last_exception = None
        retry_count = 4

        # Retry logic with exponential backoff
        for attempt in range(retry_count):
            if attempt > 0:
                # Exponential backoff: [10s, 20s, 30s] before retry
                await asyncio.sleep(attempt * 10)
            try:
                response = await task_client.update_task(body=task_result)
                logger.debug(
                    "Updated async task, id: %s, workflow_instance_id: %s, task_definition_name: %s, response: %s",
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
                    "Failed to update async task (attempt %d/%d), id: %s, workflow_instance_id: %s, task_definition_name: %s, server: %d, reason: %s",
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
            "Async task update failed after %d attempts. Task result LOST for task_id: %s, workflow: %s",
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
            paused=getattr(self.worker, 'paused', False),
            overwrite_task_def=getattr(self.worker, 'overwrite_task_def', True),
            strict_schema=getattr(self.worker, 'strict_schema', False)
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
        if resolved_config.get('overwrite_task_def') is not None:
            self.worker.overwrite_task_def = resolved_config['overwrite_task_def']
        if resolved_config.get('strict_schema') is not None:
            self.worker.strict_schema = resolved_config['strict_schema']

        # Store resolved config for logging in run() (after fork)
        self._resolved_config = resolved_config
