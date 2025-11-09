"""
AsyncIO Workers Example

This example demonstrates how to use the AsyncIO-based TaskHandlerAsyncIO
instead of the multiprocessing-based TaskHandler.

Advantages of AsyncIO:
- Lower memory footprint (single process)
- Better for I/O-bound tasks
- Simpler debugging

Requirements:
    pip install httpx  # AsyncIO HTTP client

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


# Example 1: Synchronous worker (will run in thread pool)
@worker_task(task_definition_name='greet')
def greet(name: str) -> str:
    """
    Synchronous worker - automatically runs in thread pool to avoid blocking.
    Good for legacy code or CPU-bound tasks.
    """
    return f'Hello {name}'


# Example 2: Async worker (runs natively in event loop)
@worker_task(task_definition_name='greet_async')
async def greet_async(name: str) -> str:
    """
    Async worker - runs natively in the event loop.
    Perfect for I/O-bound tasks like HTTP calls, DB queries, etc.
    """
    # Simulate async I/O operation
    await asyncio.sleep(0.1)
    return f'Hello {name} (from async function)'


# Example 3: Async worker with HTTP call
@worker_task(task_definition_name='fetch_user')
async def fetch_user(user_id: str) -> dict:
    """
    Example of making async HTTP calls using httpx.
    This is more efficient than synchronous requests.
    """
    try:
        import httpx
        print(f'fetching user {user_id}')
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://jsonplaceholder.typicode.com/users/{user_id}'
            )
            print(f'response {response.json()}')
            return response.json()

    except Exception as e:
        return {"error": str(e)}


@worker_task(task_definition_name='process_user')
async def process_user(user: User) -> dict:
    """
    Example of making async HTTP calls using httpx.
    This is more efficient than synchronous requests.
    """
    try:
        import httpx
        print(f'fetching user details for {user.id}')
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://jsonplaceholder.typicode.com/users/{user.id + 1}'
            )
            print(f'response {response.json()}')
            return response.json()

    except Exception as e:
        return {"error": str(e)}


# Example 4: CPU-bound work in thread pool
@worker_task(task_definition_name='calculate')
def calculate_fibonacci(n: int) -> int:
    """
    CPU-bound work automatically runs in thread pool.
    For heavy CPU work, consider using multiprocessing TaskHandler instead.
    """
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


# Example 5: Mixed I/O and CPU work
@worker_task(task_definition_name='process_data')
async def process_data(data_url: str) -> dict:
    """
    Demonstrates mixing async I/O with CPU-bound work.
    I/O runs in event loop, CPU work runs in thread pool.
    """
    import httpx

    # I/O-bound: Fetch data asynchronously
    async with httpx.AsyncClient() as client:
        response = await client.get(data_url)
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


async def main():
    """
    Main entry point demonstrating different ways to use TaskHandlerAsyncIO.
    """

    # Configuration - defaults to reading from environment variables:
    # - CONDUCTOR_SERVER_URL: e.g., https://play.orkes.io/api
    # - CONDUCTOR_AUTH_KEY: API key
    # - CONDUCTOR_AUTH_SECRET: API secret
    api_config = Configuration()

    print("=" * 60)
    print("Conductor AsyncIO Workers Example")
    print("=" * 60)
    print(f"Server: {api_config.host}")
    print(f"Workers: greet, greet_async, fetch_user, calculate, process_data")
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


if __name__ == '__main__':
    """
    Run the async main function.

    Python 3.7+: asyncio.run(main())
    Python 3.6: asyncio.get_event_loop().run_until_complete(main())
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
