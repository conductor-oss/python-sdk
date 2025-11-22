"""
Performance Comparison: Sync vs Async Worker Execution

This script demonstrates the differences between sync and async workers
and helps you choose the right one for your workload.

Run:
    python examples/compare_multiprocessing_vs_asyncio.py
"""

import time
import psutil
import os
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task
import asyncio


# Async worker (automatically runs concurrently)
@worker_task(
    task_definition_name='io_task_async',
    thread_count=50
)
async def io_bound_task_async(duration: float) -> str:
    """Simulates I/O-bound work with async (automatic concurrency)"""
    await asyncio.sleep(duration)
    return f"Async task completed in {duration}s"


# Sync worker (sequential execution in thread pool)
@worker_task(
    task_definition_name='io_task_sync',
    thread_count=10
)
def io_bound_task_sync(duration: float) -> str:
    """Simulates I/O-bound work with sync (thread pool)"""
    import time
    time.sleep(duration)
    return f"Sync task completed in {duration}s"


# CPU-bound worker (unaffected by async mode)
@worker_task(task_definition_name='cpu_task', thread_count=4)
def cpu_bound_task(iterations: int) -> str:
    """Simulates CPU-bound work (image processing, calculations, etc.)"""
    result = 0
    for i in range(iterations):
        result += i ** 2
    return f"CPU task completed {iterations} iterations"


def measure_memory():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def test_async_mode(config: Configuration, duration: int = 10):
    """Test async worker execution"""
    print("\n" + "=" * 60)
    print("Testing Async Worker Execution")
    print("=" * 60)

    start_memory = measure_memory()
    print(f"Starting memory: {start_memory:.2f} MB")

    # Count child processes
    parent = psutil.Process(os.getpid())

    start_time = time.time()

    handler = TaskHandler(configuration=config)
    handler.start_processes()

    # Let it run for specified duration
    time.sleep(duration)

    # Count processes
    children = parent.children(recursive=True)
    process_count = len(children) + 1  # +1 for parent

    handler.stop_processes()

    elapsed = time.time() - start_time
    end_memory = measure_memory()

    print(f"\nResults:")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  Ending memory: {end_memory:.2f} MB")
    print(f"  Memory used: {end_memory - start_memory:.2f} MB")
    print(f"  Process count: {process_count}")
    print(f"  Mode: Async (automatic concurrent execution in BackgroundEventLoop)")


def test_sync_mode(config: Configuration, duration: int = 10):
    """Test sync worker execution"""
    print("\n" + "=" * 60)
    print("Testing Sync Worker Execution")
    print("=" * 60)

    start_memory = measure_memory()
    print(f"Starting memory: {start_memory:.2f} MB")

    # Count child processes
    parent = psutil.Process(os.getpid())

    start_time = time.time()

    handler = TaskHandler(configuration=config)
    handler.start_processes()

    # Let it run for specified duration
    time.sleep(duration)

    # Count processes
    children = parent.children(recursive=True)
    process_count = len(children) + 1  # +1 for parent

    handler.stop_processes()

    elapsed = time.time() - start_time
    end_memory = measure_memory()

    print(f"\nResults:")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  Ending memory: {end_memory:.2f} MB")
    print(f"  Memory used: {end_memory - start_memory:.2f} MB")
    print(f"  Process count: {process_count}")
    print(f"  Mode: Sync (ThreadPoolExecutor)")


def print_comparison_table():
    """Print feature comparison table"""
    print("\n" + "=" * 80)
    print("WORKER EXECUTION MODE COMPARISON")
    print("=" * 80)

    comparison = [
        ("Aspect", "Sync (def)", "Async (async def)"),
        ("─" * 30, "─" * 25, "─" * 25),
        ("Architecture", "Multiprocessing", "Multiprocessing"),
        ("Execution", "ThreadPoolExecutor", "BackgroundEventLoop"),
        ("Worker behavior", "Thread pool", "Non-blocking coroutines"),
        ("Concurrency", "Limited by threads", "10-100x higher"),
        ("Memory overhead", "~60 MB per worker", "~60 MB per worker"),
        ("Best for", "CPU-bound, blocking I/O", "I/O-bound async workloads"),
        ("Detection", "Automatic (def)", "Automatic (async def)"),
    ]

    for row in comparison:
        print(f"{row[0]:<30} | {row[1]:<22} | {row[2]:<22}")


def print_recommendations():
    """Print usage recommendations"""
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("\n✅ Use Sync Workers (def):")
    print("   • CPU-bound tasks")
    print("   • Blocking I/O operations")
    print("   • Simple synchronous logic")
    print("   • When thread pool concurrency is sufficient")

    print("\n✅ Use Async Workers (async def):")
    print("   • I/O-bound workloads (HTTP, DB, file operations)")
    print("   • Need high concurrency (100+ concurrent operations)")
    print("   • Long-running async operations")
    print("   • Working with async libraries (httpx, aiohttp, asyncpg)")

    print("\n💡 Key Insight:")
    print("   Execution mode is automatically detected from function signature")
    print("   async def → BackgroundEventLoop (10-100x better concurrency)")
    print("   def → ThreadPoolExecutor (traditional thread pool)")
    print("   Both use multiprocessing (one process per worker)")


def main():
    """Run comparison tests"""
    print("\n" + "=" * 80)
    print("Conductor Python SDK: Sync vs Async Worker Comparison")
    print("=" * 80)

    config = Configuration()

    # Test duration (shorter for demo)
    test_duration = 5

    print(f"\nConfiguration:")
    print(f"  Server: {config.host}")
    print(f"  Test duration: {test_duration}s per mode")

    # Run tests
    test_sync_mode(config, test_duration)
    test_async_mode(config, test_duration)

    # Print comparison
    print_comparison_table()
    print_recommendations()

    print("\n" + "=" * 80)
    print("Comparison complete!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
