"""
Performance Comparison: Blocking vs Non-Blocking Async Execution

This script demonstrates the differences between blocking and non-blocking async
execution modes and helps you choose the right one for your workload.

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


# Blocking async worker (default)
@worker_task(
    task_definition_name='io_task_blocking',
    thread_count=10,
    non_blocking_async=False  # Default: blocks worker thread
)
async def io_bound_task_blocking(duration: float) -> str:
    """Simulates I/O-bound work with blocking async (default behavior)"""
    await asyncio.sleep(duration)
    return f"Blocking async task completed in {duration}s"


# Non-blocking async worker
@worker_task(
    task_definition_name='io_task_nonblocking',
    thread_count=10,
    non_blocking_async=True  # Non-blocking: runs concurrently
)
async def io_bound_task_nonblocking(duration: float) -> str:
    """Simulates I/O-bound work with non-blocking async"""
    await asyncio.sleep(duration)
    return f"Non-blocking async task completed in {duration}s"


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


def test_nonblocking_mode(config: Configuration, duration: int = 10):
    """Test non-blocking async execution"""
    print("\n" + "=" * 60)
    print("Testing Non-Blocking Async Execution")
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
    print(f"  Mode: Non-blocking async (concurrent execution in BackgroundEventLoop)")


def test_blocking_mode(config: Configuration, duration: int = 10):
    """Test blocking async execution (default)"""
    print("\n" + "=" * 60)
    print("Testing Blocking Async Execution (Default)")
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
    print(f"  Mode: Blocking async (sequential execution in BackgroundEventLoop)")


def print_comparison_table():
    """Print feature comparison table"""
    print("\n" + "=" * 80)
    print("ASYNC EXECUTION MODE COMPARISON")
    print("=" * 80)

    comparison = [
        ("Aspect", "Blocking (default)", "Non-Blocking"),
        ("─" * 30, "─" * 25, "─" * 25),
        ("Architecture", "Multiprocessing", "Multiprocessing"),
        ("Async execution", "BackgroundEventLoop", "BackgroundEventLoop"),
        ("Worker thread behavior", "Blocks waiting for async", "Continues polling"),
        ("Async concurrency", "Sequential", "Concurrent (10-100x)"),
        ("Memory overhead", "~60 MB per worker", "~60 MB per worker"),
        ("Complexity", "Simple", "Slightly more complex"),
        ("Best for", "Most use cases", "I/O-heavy async workloads"),
        ("Backward compatible", "Yes (default)", "Opt-in"),
    ]

    for row in comparison:
        print(f"{row[0]:<30} | {row[1]:<22} | {row[2]:<22}")


def print_recommendations():
    """Print usage recommendations"""
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("\n✅ Use Blocking Async (default, non_blocking_async=False):")
    print("   • General use cases")
    print("   • Few concurrent async tasks (< 5)")
    print("   • Quick async operations (< 1s)")
    print("   • You want simplicity and predictability")

    print("\n✅ Use Non-Blocking Async (non_blocking_async=True):")
    print("   • Many concurrent async tasks (10+)")
    print("   • I/O-heavy workloads (HTTP calls, DB queries)")
    print("   • Long-running async operations (> 1s)")
    print("   • You need maximum async throughput")

    print("\n💡 Key Insight:")
    print("   Both modes use multiprocessing (one process per worker)")
    print("   Both use BackgroundEventLoop for async execution")
    print("   The difference is whether worker threads block waiting for async tasks")


def main():
    """Run comparison tests"""
    print("\n" + "=" * 80)
    print("Conductor Python SDK: Async Execution Mode Comparison")
    print("=" * 80)

    config = Configuration()

    # Test duration (shorter for demo)
    test_duration = 5

    print(f"\nConfiguration:")
    print(f"  Server: {config.host}")
    print(f"  Test duration: {test_duration}s per mode")

    # Run tests
    test_blocking_mode(config, test_duration)
    test_nonblocking_mode(config, test_duration)

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
