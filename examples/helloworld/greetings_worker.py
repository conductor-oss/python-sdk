"""
This file contains a Simple Worker that can be used in any workflow.
For detailed information https://github.com/conductor-sdk/conductor-python/blob/main/README.md#step-2-write-worker
"""
import asyncio
import threading
from datetime import datetime

from conductor.client.context import get_task_context
from conductor.client.worker.worker_task import worker_task


@worker_task(task_definition_name='greet')
def greet(name: str) -> str:
    return f'Hello, --> {name}'


@worker_task(
    task_definition_name='greet_sync',
    thread_count=10,  # Low concurrency for simple tasks
    poll_timeout=100,  # Default poll timeout (ms)
    lease_extend_enabled=False  # Fast tasks don't need lease extension
)
def greet(name: str) -> str:
    """
    Synchronous worker - automatically runs in thread pool to avoid blocking.
    Good for legacy code or simple CPU-bound tasks.
    """
    return f'Hello {name}'


@worker_task(
    task_definition_name='greet_async',
    thread_count=13,  # Higher concurrency for async I/O
    poll_timeout=100,
    lease_extend_enabled=False
)
async def greet_async(name: str) -> str:
    """
    Async worker - runs natively in the event loop.
    Perfect for I/O-bound tasks like HTTP calls, DB queries, etc.
    """
    # Simulate async I/O operation
    # Print execution info to verify parallel execution
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # milliseconds
    ctx = get_task_context()
    thread_name = threading.current_thread().name
    task_name = asyncio.current_task().get_name() if asyncio.current_task() else "N/A"
    task_id = ctx.get_task_id()
    print(f"[greet_async] Started: name={name} | Time={timestamp} | Thread={thread_name} | AsyncIO Task={task_name} | "
          f"task_id = {task_id}")

    await asyncio.sleep(1.01)
    return f'Hello {name} (from async function) - id: {task_id}'
