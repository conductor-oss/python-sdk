"""
AsyncIO Workers Example - Java SDK Architecture

This example demonstrates the AsyncIO task runner with Java SDK architecture features:
- Semaphore-based dynamic batch polling
- Per-worker thread count configuration
- Automatic lease extension
- In-memory queue for V2 API chained tasks
- Zero-polling optimization

Key Features (matching Java SDK):
- Dynamic batch sizing (batch = available threads)
- No server calls when all threads busy
- Adaptive concurrency control
- Optimal resource utilization

Requirements:
    pip install httpx  # AsyncIO HTTP client

Configuration:
    Set environment variables or create conductor_config.py:
    - CONDUCTOR_SERVER_URL: e.g., https://play.orkes.io/api
    - CONDUCTOR_AUTH_KEY: API key
    - CONDUCTOR_AUTH_SECRET: API secret

Run:
    python examples/asyncio_workers.py
"""

import asyncio
import json
import signal
from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task

from dataclasses import dataclass


@dataclass
class Geo:
    lat: str
    lng: str


@dataclass
class Address:
    street: str
    suite: str
    city: str
    zipcode: str
    geo: Geo


@dataclass
class Company:
    name: str
    catchPhrase: str
    bs: str


@dataclass
class User:
    id: int
    name: str
    username: str
    email: str
    address: Address
    phone: str
    website: str
    company: Company


# Example 1: Simple synchronous worker (runs in thread pool)
@worker_task(
    task_definition_name='greet',
    thread_count=101,              # Low concurrency for simple tasks
    poll_timeout=100,            # Default poll timeout (ms)
    lease_extend_enabled=False   # Fast tasks don't need lease extension
)
def greet(name: str) -> str:
    """
    Synchronous worker - automatically runs in thread pool to avoid blocking.
    Good for legacy code or simple CPU-bound tasks.
    """
    return f'Hello {name}'


# Example 2: Simple async worker (runs natively in event loop)
@worker_task(
    task_definition_name='greet_async',
    thread_count=10,             # Higher concurrency for async I/O
    poll_timeout=100,
    lease_extend_enabled=False
)
async def greet_async(name: str) -> str:
    """
    Async worker - runs natively in the event loop.
    Perfect for I/O-bound tasks like HTTP calls, DB queries, etc.
    """
    # Simulate async I/O operation
    await asyncio.sleep(0.1)
    return f'Hello {name} (from async function)'


# Example 3: High-throughput HTTP worker with batch polling
@worker_task(
    poll_interval_millis=10,
    task_definition_name='fetch_user',
    thread_count=20,             # High concurrency for I/O-bound tasks
    poll_timeout=20,            # Longer timeout for efficient long-polling
    lease_extend_enabled=False   # Fast HTTP calls don't need lease extension
)
async def fetch_user(user_id: str) -> dict:
    """
    Example of making async HTTP calls using httpx.
    With thread_count=20, the system will:
    - Batch poll up to 20 tasks when all threads available
    - Skip polling when all 20 threads busy (zero-polling)
    - Dynamically adjust batch size based on availability
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://jsonplaceholder.typicode.com/users/{user_id}',
                timeout=10.0
            )
            return response.json()

    except Exception as e:
        return {"error": str(e)}


# Example 4: Dataclass-based worker (type-safe input)
@worker_task(
    task_definition_name='process_user',
    thread_count=15,
    poll_timeout=150,
    lease_extend_enabled=False
)
async def process_user(user: User) -> dict:
    """
    Worker that accepts User dataclass - SDK automatically converts from dict.
    Demonstrates type-safe worker functions.

    The fetch_user task returns a dict, which is chained to this task.
    Since dict outputs are used as-is (not wrapped in "result"),
    the User dataclass can be properly constructed.
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://jsonplaceholder.typicode.com/users/{user.id + 3}',
                timeout=10.0
            )
            return response.json()

    except Exception as e:
        return {"error": str(e)}


# Example 5: Worker with dict input (flexible alternative)
@worker_task(
    task_definition_name='process_user_dict',
    thread_count=10,
    poll_timeout=150,
    lease_extend_enabled=False
)
async def process_user_dict(user: dict) -> dict:
    """
    Worker that accepts dict input directly - more flexible.
    Use this when you don't need strict type checking.

    Accepts any dict with an 'id' field.
    """
    try:
        import httpx
        user_id = user.get('id', 1)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://jsonplaceholder.typicode.com/users/{user_id + 1}',
                timeout=10.0
            )
            return response.json()

    except Exception as e:
        return {"error": str(e)}


# Example 6: CPU-bound work in thread pool (lower concurrency)
@worker_task(
    task_definition_name='calculate',
    thread_count=4,              # Lower concurrency for CPU-bound tasks
    poll_timeout=100,
    lease_extend_enabled=False
)
def calculate_fibonacci(n: int) -> int:
    """
    CPU-bound work automatically runs in thread pool.
    For heavy CPU work, consider using multiprocessing TaskHandler instead.

    Note: thread_count=4 limits concurrent CPU-intensive tasks to avoid
    overwhelming the system (GIL contention).
    """
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


# Example 7: Mixed I/O and CPU work with controlled concurrency
@worker_task(
    task_definition_name='process_data',
    thread_count=12,             # Moderate concurrency for mixed workload
    poll_timeout=200,
    lease_extend_enabled=True,   # Enable lease extension for longer tasks
    register_task_def=False      # Don't auto-register task definition
)
async def process_data(data_url: str) -> dict:
    """
    Demonstrates mixing async I/O with CPU-bound work.
    I/O runs in event loop, CPU work runs in thread pool.

    With thread_count=12:
    - System can batch poll up to 12 tasks when all threads free
    - Zero-polling kicks in when all 12 threads busy
    - Dynamically adjusts batch size as threads complete
    """
    import httpx

    # I/O-bound: Fetch data asynchronously
    async with httpx.AsyncClient() as client:
        response = await client.get(data_url, timeout=10.0)
        data = response.json()

    # CPU-bound: Process in thread pool
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,  # Default thread pool
        _process_data_sync,
        data
    )

    return result


def _process_data_sync(data: dict) -> dict:
    """Helper function for CPU-bound processing"""
    # Simulated CPU-intensive work
    import time
    time.sleep(0.1)
    return {"processed": True, "count": len(data)}


# Example 8: Long-running task with automatic lease extension
@worker_task(
    task_definition_name='long_task',
    thread_count=2,              # Low concurrency for expensive tasks
    poll_timeout=500,
    lease_extend_enabled=True    # Automatically extends lease at 80% of timeout
)
async def long_running_task(duration: int) -> dict:
    """
    Demonstrates automatic lease extension for long-running tasks.

    If task.response_timeout_seconds = 300 (5 minutes):
    - Lease extension sent at 240s (80%)
    - Repeats every 240s until task completes
    - Retries up to 3 times per extension
    - Automatically cancelled when task completes

    This keeps the task alive in Conductor during long processing.
    """
    # Simulate long-running operation
    await asyncio.sleep(duration)
    return {"duration": duration, "completed": True}


async def main():
    """
    Main entry point demonstrating AsyncIO task handler with Java SDK architecture.
    """

    # Configuration - defaults to reading from environment variables:
    # - CONDUCTOR_SERVER_URL: e.g., https://play.orkes.io/api
    # - CONDUCTOR_AUTH_KEY: API key
    # - CONDUCTOR_AUTH_SECRET: API secret
    api_config = Configuration()

    print("=" * 60)
    print("Conductor AsyncIO Workers - Java SDK Architecture")
    print("=" * 60)
    print(f"Server: {api_config.host}")
    print()
    print("Workers with dynamic batch polling:")
    print("  • greet (thread_count=1)")
    print("  • greet_async (thread_count=10)")
    print("  • fetch_user (thread_count=20) - High throughput")
    print("  • process_user (thread_count=15) - Type-safe dataclass")
    print("  • process_user_dict (thread_count=10) - Flexible dict input")
    print("  • calculate (thread_count=4) - CPU-bound")
    print("  • process_data (thread_count=12) - Mixed I/O+CPU")
    print("  • long_task (thread_count=2) - With lease extension")
    print()
    print("Features:")
    print("  ✓ Dynamic batch polling (batch size = available threads)")
    print("  ✓ Zero-polling optimization (skip when all threads busy)")
    print("  ✓ Automatic lease extension at 80% of timeout")
    print("  ✓ In-memory queue for V2 API chained tasks")
    print("  ✓ Per-worker concurrency control")
    print("=" * 60)
    print("\nStarting workers... Press Ctrl+C to stop\n")

    # Option 1: Using async context manager (recommended)
    try:
        async with TaskHandlerAsyncIO(configuration=api_config) as task_handler:
            # Set up graceful shutdown on SIGTERM
            loop = asyncio.get_running_loop()

            def signal_handler():
                print("\n\nReceived shutdown signal, stopping workers...")
                loop.create_task(task_handler.stop())

            # Register signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, signal_handler)

            # Wait for workers to complete (blocks until stopped)
            await task_handler.wait()

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")

    except Exception as e:
        print(f"\n\nError: {e}")
        raise

    # Option 2: Manual start/stop (alternative)
    # task_handler = TaskHandlerAsyncIO(configuration=api_config)
    # await task_handler.start()
    # try:
    #     await asyncio.sleep(60)  # Run for 60 seconds
    # finally:
    #     await task_handler.stop()

    # Option 3: Run with timeout (for testing)
    # from conductor.client.automator.task_handler_asyncio import run_workers_async
    # await run_workers_async(
    #     configuration=api_config,
    #     stop_after_seconds=60  # Auto-stop after 60 seconds
    # )

    print("\nWorkers stopped. Goodbye!")


async def demo_v2_api():
    """
    Example of V2 API support with in-memory queue.

    When enabled (export taskUpdateV2=true), the server can return
    the next task to execute in the update response, which is added
    to the in-memory queue to avoid redundant polling.
    """
    import os
    os.environ['taskUpdateV2'] = 'true'

    api_config = Configuration()

    @worker_task(
        task_definition_name='chained_task',
        thread_count=10
    )
    async def chained_task(data: dict) -> dict:
        """Task that may be part of a chained workflow"""
        await asyncio.sleep(0.5)
        return {"result": "processed", "data": data}

    async with TaskHandlerAsyncIO(configuration=api_config) as handler:
        # Server may return next task in workflow
        # → Added to in-memory queue
        # → Drained before next server poll
        # → Reduces server calls by ~30% for chained workflows
        await handler.wait()


async def demo_zero_polling():
    """
    Example demonstrating zero-polling optimization.

    When all threads are busy:
    - poll_count = 0 (no available permits)
    - Skip server call (zero-polling)
    - Sleep briefly and retry
    - Saves server resources during high load
    """

    @worker_task(
        task_definition_name='busy_task',
        thread_count=5  # Only 5 concurrent tasks allowed
    )
    async def busy_task(duration: int) -> dict:
        """Simulates a task that takes 'duration' seconds"""
        await asyncio.sleep(duration)
        return {"completed": True}

    api_config = Configuration()

    async with TaskHandlerAsyncIO(configuration=api_config) as handler:
        # Scenario: 10 tasks queued on server
        #
        # Poll #1: 5 permits available → batch poll 5 tasks → all threads busy
        # Poll #2: 0 permits available → zero-polling (skip server call)
        # Poll #3: 0 permits available → zero-polling (skip server call)
        # ...
        # Poll #N: 2 tasks complete → 2 permits available → batch poll 2 tasks
        #
        # Result: Saved (N-2) server calls during high load
        await handler.wait()


if __name__ == '__main__':
    """
    Run the async main function.

    Python 3.7+: asyncio.run(main())
    Python 3.6: asyncio.get_event_loop().run_until_complete(main())
    """
    try:
        # Run main demo
        asyncio.run(main())

        # Uncomment to run other demos:
        # asyncio.run(demo_v2_api())
        # asyncio.run(demo_zero_polling())

    except KeyboardInterrupt:
        pass
