from __future__ import annotations
import functools
from typing import Optional
from conductor.client.automator.task_handler import register_decorated_fn
from conductor.client.workflow.task.simple_task import SimpleTask


def WorkerTask(task_definition_name: str, poll_interval: int = 100, domain: Optional[str] = None, worker_id: Optional[str] = None,
               poll_interval_seconds: int = 0, thread_count: int = 1, register_task_def: bool = False,
               poll_timeout: int = 100, lease_extend_enabled: bool = False):
    """
    Decorator to register a function as a Conductor worker task (legacy CamelCase name).

    Note: This is the legacy name. Use worker_task() instead for consistency with Python naming conventions.

    Args:
        task_definition_name: Name of the task definition in Conductor. This must match the task name in your workflow.

        poll_interval: How often to poll the Conductor server for new tasks (milliseconds).
            - Default: 100ms
            - Alias for poll_interval_millis in worker_task()
            - Use poll_interval_seconds for second-based intervals

        poll_interval_seconds: Alternative to poll_interval using seconds instead of milliseconds.
            - Default: 0 (disabled, uses poll_interval instead)
            - When > 0: Overrides poll_interval (converted to milliseconds)

        domain: Optional task domain for multi-tenancy. Tasks are isolated by domain.
            - Default: None (no domain isolation)

        worker_id: Optional unique identifier for this worker instance.
            - Default: None (auto-generated)

        thread_count: Maximum concurrent tasks this worker can execute.
            - Default: 1
            - Controls thread pool size for concurrent task execution
            - Choose based on workload:
              * CPU-bound: 1-4 (limited by GIL)
              * I/O-bound: 10-50 (network calls, database queries, etc.)
              * Mixed: 5-20

        register_task_def: Whether to automatically register/update the task definition in Conductor.
            - Default: False

        poll_timeout: Server-side long polling timeout (milliseconds).
            - Default: 100ms

        lease_extend_enabled: Whether to automatically extend task lease for long-running tasks.
            - Default: False
            - Disable for fast tasks (<1s) to reduce API calls
            - Enable for long tasks (>30s) to prevent timeout

    Returns:
        Decorated function that can be called normally or used as a workflow task
    """
    poll_interval_millis = poll_interval
    if poll_interval_seconds > 0:
        poll_interval_millis = 1000 * poll_interval_seconds

    def worker_task_func(func):

        register_decorated_fn(name=task_definition_name, poll_interval=poll_interval_millis, domain=domain,
                              worker_id=worker_id, thread_count=thread_count, register_task_def=register_task_def,
                              poll_timeout=poll_timeout, lease_extend_enabled=lease_extend_enabled,
                              func=func)

        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            if "task_ref_name" in kwargs:
                task = SimpleTask(task_def_name=task_definition_name, task_reference_name=kwargs["task_ref_name"])
                kwargs.pop("task_ref_name")
                task.input_parameters.update(kwargs)
                return task
            return func(*args, **kwargs)

        return wrapper_func

    return worker_task_func


def worker_task(task_definition_name: str, poll_interval_millis: int = 100, domain: Optional[str] = None, worker_id: Optional[str] = None,
                thread_count: int = 1, register_task_def: bool = False, poll_timeout: int = 100, lease_extend_enabled: bool = False):
    """
    Decorator to register a function as a Conductor worker task.

    Args:
        task_definition_name: Name of the task definition in Conductor. This must match the task name in your workflow.

        poll_interval_millis: How often to poll the Conductor server for new tasks (milliseconds).
            - Default: 100ms
            - Lower values = more responsive but higher server load
            - Higher values = less server load but slower task pickup
            - Recommended: 100-500ms for most use cases

        domain: Optional task domain for multi-tenancy. Tasks are isolated by domain.
            - Default: None (no domain isolation)
            - Use when you need to partition tasks across different environments/tenants

        worker_id: Optional unique identifier for this worker instance.
            - Default: None (auto-generated)
            - Useful for debugging and tracking which worker executed which task

        thread_count: Maximum concurrent tasks this worker can execute.
            - Default: 1
            - Controls thread pool size for concurrent task execution
            - Higher values allow more concurrent task execution
            - Choose based on workload:
              * CPU-bound: 1-4 (limited by GIL)
              * I/O-bound: 10-50 (network calls, database queries, etc.)
              * Mixed: 5-20

        register_task_def: Whether to automatically register/update the task definition in Conductor.
            - Default: False
            - When True: Task definition is created/updated on worker startup
            - When False: Task definition must exist in Conductor already
            - Recommended: False for production (manage task definitions separately)

        poll_timeout: Server-side long polling timeout (milliseconds).
            - Default: 100ms
            - How long the server will wait for a task before returning empty response
            - Higher values reduce polling frequency when no tasks available
            - Recommended: 100-500ms

        lease_extend_enabled: Whether to automatically extend task lease for long-running tasks.
            - Default: False
            - When True: Lease is automatically extended at 80% of responseTimeoutSeconds
            - When False: Task must complete within responseTimeoutSeconds or will timeout
            - Disable for fast tasks (<1s) to reduce unnecessary API calls
            - Enable for long tasks (>30s) to prevent premature timeout

    Returns:
        Decorated function that can be called normally or used as a workflow task

    Note:
        The 'paused' property is not available as a decorator parameter. It can only be
        controlled via environment variables:
        - conductor.worker.all.paused=true (pause all workers)
        - conductor.worker.<task_name>.paused=true (pause specific worker)

    Worker Execution Modes (automatically detected):
        - Sync workers (def): Execute in thread pool (ThreadPoolExecutor)
        - Async workers (async def): Execute concurrently using BackgroundEventLoop
          * Automatically run as non-blocking coroutines
          * 10-100x better concurrency for I/O-bound workloads

    Example (Sync):
        @worker_task(task_definition_name='process_order', thread_count=5)
        def process_order(order_id: str) -> dict:
            # Sync execution in thread pool
            return {'status': 'completed'}

    Example (Async):
        @worker_task(task_definition_name='fetch_data', thread_count=50)
        async def fetch_data(url: str) -> dict:
            # Async execution with high concurrency
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
            return {'data': response.json()}
    """
    def worker_task_func(func):
        register_decorated_fn(name=task_definition_name, poll_interval=poll_interval_millis, domain=domain,
                              worker_id=worker_id, thread_count=thread_count, register_task_def=register_task_def,
                              poll_timeout=poll_timeout, lease_extend_enabled=lease_extend_enabled, func=func)

        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            if "task_ref_name" in kwargs:
                task = SimpleTask(task_def_name=task_definition_name, task_reference_name=kwargs["task_ref_name"])
                kwargs.pop("task_ref_name")
                task.input_parameters.update(kwargs)
                return task
            return func(*args, **kwargs)

        return wrapper_func

    return worker_task_func
