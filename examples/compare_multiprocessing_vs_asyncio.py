"""
Performance Comparison: asyncio=False vs asyncio=True

This script demonstrates the differences between execution modes in the unified
TaskHandler and helps you choose the right one for your workload.

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


# I/O-bound worker (simulates API call)
@worker_task(task_definition_name='io_task')
async def io_bound_task(duration: float) -> str:
    """Simulates I/O-bound work (HTTP call, DB query, etc.)"""
    await asyncio.sleep(duration)
    return f"I/O task completed in {duration}s"


# CPU-bound worker (simulates computation)
@worker_task(task_definition_name='cpu_task')
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


def test_asyncio_mode(config: Configuration, duration: int = 10):
    """Test asyncio=True execution mode"""
    print("\n" + "=" * 60)
    print("Testing asyncio=True Execution Mode")
    print("=" * 60)

    start_memory = measure_memory()
    print(f"Starting memory: {start_memory:.2f} MB")

    # Count child processes
    parent = psutil.Process(os.getpid())

    start_time = time.time()

    handler = TaskHandler(configuration=config, asyncio=True)
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
    print(f"  Mode: Dedicated event loop per worker process")


def test_default_mode(config: Configuration, duration: int = 10):
    """Test asyncio=False (default) execution mode"""
    print("\n" + "=" * 60)
    print("Testing asyncio=False (Default) Execution Mode")
    print("=" * 60)

    start_memory = measure_memory()
    print(f"Starting memory: {start_memory:.2f} MB")

    # Count child processes
    parent = psutil.Process(os.getpid())

    start_time = time.time()

    handler = TaskHandler(configuration=config, asyncio=False)
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
    print(f"  Mode: BackgroundEventLoop for async workers")


def print_comparison_table():
    """Print feature comparison table"""
    print("\n" + "=" * 80)
    print("EXECUTION MODE COMPARISON")
    print("=" * 80)

    comparison = [
        ("Aspect", "asyncio=False (default)", "asyncio=True"),
        ("─" * 30, "─" * 25, "─" * 25),
        ("Architecture", "Multiprocessing", "Multiprocessing"),
        ("Polling", "Sync (requests)", "Sync (requests)"),
        ("Async execution", "BackgroundEventLoop", "Dedicated event loop"),
        ("Sync execution", "Direct", "Thread pool"),
        ("Memory overhead", "~60 MB per worker", "~60 MB + thread pool"),
        ("Best for", "Most use cases", "Pure async workloads"),
        ("Async perf", "1.5-2x faster", "Slightly faster"),
        ("Fault isolation", "Yes (process crash)", "Yes (process crash)"),
    ]

    for row in comparison:
        print(f"{row[0]:<30} | {row[1]:<20} | {row[2]:<20}")


def print_recommendations():
    """Print usage recommendations"""
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("\n✅ Use asyncio=False (default) when:")
    print("   • General use cases")
    print("   • Mixed sync and async workers")
    print("   • CPU-bound tasks")
    print("   • You want simplicity")

    print("\n✅ Use asyncio=True when:")
    print("   • Pure async workload")
    print("   • You want dedicated event loop per worker")
    print("   • Fine-tuned async control needed")

    print("\n💡 Key Insight:")
    print("   Both modes use multiprocessing (one process per worker)")
    print("   The difference is only in how async workers are executed")


def main():
    """Run comparison tests"""
    print("\n" + "=" * 80)
    print("Conductor Python SDK: Execution Mode Comparison")
    print("=" * 80)

    config = Configuration()

    # Test duration (shorter for demo)
    test_duration = 5

    print(f"\nConfiguration:")
    print(f"  Server: {config.host}")
    print(f"  Test duration: {test_duration}s per implementation")

    # Run tests
    test_default_mode(config, test_duration)
    test_asyncio_mode(config, test_duration)

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
