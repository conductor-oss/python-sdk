"""
Worker Discovery: Sync vs Async Example

Demonstrates that worker discovery is execution-model agnostic.
Workers can be discovered once and used with either:
- TaskHandler (sync, multiprocessing-based)
- TaskHandlerAsyncIO (async, asyncio-based)

The discovery mechanism just imports Python modules - it doesn't care
whether the workers are sync or async functions.
"""

import sys
from pathlib import Path

# Add examples directory to path
examples_dir = Path(__file__).parent
if str(examples_dir) not in sys.path:
    sys.path.insert(0, str(examples_dir))

from conductor.client.worker.worker_loader import auto_discover_workers
from conductor.client.configuration.configuration import Configuration


def demonstrate_sync_compatibility():
    """
    Demonstrate that discovered workers work with sync TaskHandler
    """
    print("\n" + "=" * 70)
    print("Sync TaskHandler Compatibility")
    print("=" * 70)

    # Discover workers
    loader = auto_discover_workers(
        packages=['worker_discovery.my_workers'],
        print_summary=False
    )

    print(f"\n✓ Discovered {loader.get_worker_count()} workers")
    print(f"✓ Workers: {', '.join(loader.get_worker_names())}\n")

    # Workers can be used with sync TaskHandler (multiprocessing)
    from conductor.client.automator.task_handler import TaskHandler

    try:
        # Create TaskHandler with discovered workers
        handler = TaskHandler(
            configuration=Configuration(),
            scan_for_annotated_workers=True  # Uses discovered workers
        )

        print("✓ TaskHandler (sync) created successfully")
        print("✓ Discovered workers are compatible with sync execution")
        print("✓ Both sync and async workers can run in TaskHandler")
        print("  - Sync workers: Run in worker processes")
        print("  - Async workers: Run in event loop within worker processes")

    except Exception as e:
        print(f"✗ Error: {e}")


def demonstrate_async_compatibility():
    """
    Demonstrate that discovered workers work with async TaskHandlerAsyncIO
    """
    print("\n" + "=" * 70)
    print("Async TaskHandlerAsyncIO Compatibility")
    print("=" * 70)

    # Discover workers (same discovery process)
    loader = auto_discover_workers(
        packages=['worker_discovery.my_workers'],
        print_summary=False
    )

    print(f"\n✓ Discovered {loader.get_worker_count()} workers")
    print(f"✓ Workers: {', '.join(loader.get_worker_names())}\n")

    # Workers can be used with async TaskHandlerAsyncIO
    from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO

    try:
        # Create TaskHandlerAsyncIO with discovered workers
        handler = TaskHandlerAsyncIO(
            configuration=Configuration()
            # Automatically uses discovered workers
        )

        print("✓ TaskHandlerAsyncIO (async) created successfully")
        print("✓ Discovered workers are compatible with async execution")
        print("✓ Both sync and async workers can run in TaskHandlerAsyncIO")
        print("  - Sync workers: Run in thread pool")
        print("  - Async workers: Run natively in event loop")

    except Exception as e:
        print(f"✗ Error: {e}")


def demonstrate_worker_types():
    """
    Show that worker discovery finds both sync and async workers
    """
    print("\n" + "=" * 70)
    print("Worker Types in Discovery")
    print("=" * 70)

    # Discover workers
    loader = auto_discover_workers(
        packages=['worker_discovery.my_workers'],
        print_summary=False
    )

    print(f"\nDiscovered workers:")

    workers = loader.get_workers()
    for worker in workers:
        task_name = worker.get_task_definition_name()
        func = worker._execute_function if hasattr(worker, '_execute_function') else worker.execute_function

        # Check if function is async
        import asyncio
        is_async = asyncio.iscoroutinefunction(func)

        print(f"  • {task_name:20} -> {'async' if is_async else 'sync '} function")

    print("\n✓ Discovery finds both sync and async workers")
    print("✓ Execution model is determined by the worker function, not discovery")


def demonstrate_execution_model_agnostic():
    """
    Demonstrate that discovery is execution-model agnostic
    """
    print("\n" + "=" * 70)
    print("Execution-Model Agnostic Discovery")
    print("=" * 70)

    print("\nWorker Discovery Process:")
    print("  1. Scan Python packages")
    print("  2. Import modules")
    print("  3. Find @worker_task decorated functions")
    print("  4. Register workers in global registry")
    print("\n✓ No difference between sync/async during discovery")
    print("✓ Discovery only imports and registers")
    print("✓ Execution model determined at runtime by TaskHandler choice")

    print("\nTaskHandler Choice Determines Execution:")
    print("  • TaskHandler (sync):")
    print("    - Uses multiprocessing")
    print("    - Sync workers run directly")
    print("    - Async workers run in event loop")
    print("\n  • TaskHandlerAsyncIO (async):")
    print("    - Uses asyncio")
    print("    - Sync workers run in thread pool")
    print("    - Async workers run natively")

    print("\n✓ Same workers, different execution strategies")
    print("✓ Discovery is completely independent of execution model")


def main():
    """Main entry point"""
    print("\n" + "=" * 70)
    print("Worker Discovery: Sync vs Async Compatibility")
    print("=" * 70)
    print("\nDemonstrating that worker discovery is execution-model agnostic.")
    print("The same discovered workers can be used with both sync and async handlers.\n")

    try:
        demonstrate_worker_types()
        demonstrate_sync_compatibility()
        demonstrate_async_compatibility()
        demonstrate_execution_model_agnostic()

        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print("\n✓ Worker discovery works identically for sync and async")
        print("✓ Discovery is just module importing and registration")
        print("✓ Execution model is chosen by TaskHandler type")
        print("✓ Same workers can run in both execution models")
        print("\nKey Insight:")
        print("  Worker discovery ≠ Worker execution")
        print("  Discovery finds workers, execution runs them")
        print("\n")

    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
