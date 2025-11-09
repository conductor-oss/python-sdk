"""
Performance Comparison: Multiprocessing vs AsyncIO

This script demonstrates the differences between multiprocessing and asyncio
implementations and helps you choose the right one for your workload.

Run:
    python examples/compare_multiprocessing_vs_asyncio.py
"""

import asyncio
import time
import psutil
import os
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task


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


async def test_asyncio(config: Configuration, duration: int = 10):
    """Test AsyncIO implementation"""
    print("\n" + "=" * 60)
    print("Testing AsyncIO Implementation")
    print("=" * 60)

    start_memory = measure_memory()
    print(f"Starting memory: {start_memory:.2f} MB")

    start_time = time.time()

    async with TaskHandlerAsyncIO(configuration=config) as handler:
        # Run for specified duration
        await asyncio.sleep(duration)

    elapsed = time.time() - start_time
    end_memory = measure_memory()

    print(f"\nResults:")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  Ending memory: {end_memory:.2f} MB")
    print(f"  Memory used: {end_memory - start_memory:.2f} MB")
    print(f"  Process count: 1 (single process)")


def test_multiprocessing(config: Configuration, duration: int = 10):
    """Test Multiprocessing implementation"""
    print("\n" + "=" * 60)
    print("Testing Multiprocessing Implementation")
    print("=" * 60)

    start_memory = measure_memory()
    print(f"Starting memory: {start_memory:.2f} MB")

    # Count child processes
    parent = psutil.Process(os.getpid())
    initial_children = len(parent.children(recursive=True))

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


def print_comparison_table():
    """Print feature comparison table"""
    print("\n" + "=" * 80)
    print("FEATURE COMPARISON")
    print("=" * 80)

    comparison = [
        ("Aspect", "Multiprocessing", "AsyncIO"),
        ("─" * 30, "─" * 20, "─" * 20),
        ("Memory (10 workers)", "~500-1000 MB", "~50-100 MB"),
        ("I/O-bound throughput", "Good", "Excellent"),
        ("CPU-bound throughput", "Excellent", "Limited (GIL)"),
        ("Fault isolation", "Yes (process crash)", "No (shared fate)"),
        ("Debugging", "Complex (multiple processes)", "Simple (single process)"),
        ("Context switching", "OS-level (expensive)", "Coroutine (cheap)"),
        ("Concurrency model", "True parallelism", "Cooperative"),
        ("Scaling", "Linear memory cost", "Minimal memory cost"),
        ("Dependencies", "None (stdlib)", "httpx (external)"),
        ("Best for", "CPU-bound tasks", "I/O-bound tasks"),
    ]

    for row in comparison:
        print(f"{row[0]:<30} | {row[1]:<20} | {row[2]:<20}")


def print_recommendations():
    """Print usage recommendations"""
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("\n✅ Use AsyncIO when:")
    print("   • Tasks are primarily I/O-bound (HTTP calls, DB queries, file I/O)")
    print("   • You need 10+ workers")
    print("   • Memory is constrained")
    print("   • You want simpler debugging")
    print("   • You're comfortable with async/await syntax")

    print("\n✅ Use Multiprocessing when:")
    print("   • Tasks are CPU-bound (image processing, ML inference)")
    print("   • You need absolute fault isolation")
    print("   • You have complex shared state requirements")
    print("   • You want battle-tested stability")

    print("\n⚠️  Consider Hybrid Approach when:")
    print("   • You have both I/O-bound and CPU-bound tasks")
    print("   • Use AsyncIO with ProcessPoolExecutor for CPU work")
    print("   • See examples/asyncio_workers.py for implementation")


async def main():
    """Run comparison tests"""
    print("\n" + "=" * 80)
    print("Conductor Python SDK: Multiprocessing vs AsyncIO Comparison")
    print("=" * 80)

    # Check dependencies
    try:
        import httpx
        asyncio_available = True
    except ImportError:
        asyncio_available = False
        print("\n⚠️  WARNING: httpx not installed. AsyncIO test will be skipped.")
        print("   Install with: pip install httpx")

    config = Configuration()

    # Test duration (shorter for demo)
    test_duration = 5

    print(f"\nConfiguration:")
    print(f"  Server: {config.host}")
    print(f"  Test duration: {test_duration}s per implementation")

    # Run tests
    if asyncio_available:
        await test_asyncio(config, test_duration)

    test_multiprocessing(config, test_duration)

    # Print comparison
    print_comparison_table()
    print_recommendations()

    print("\n" + "=" * 80)
    print("Comparison complete!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
