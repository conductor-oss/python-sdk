"""
Worker Discovery Example

Demonstrates automatic worker discovery from packages, similar to
Spring's component scanning in Java.

This example shows how to:
1. Scan packages for @worker_task decorated functions
2. Automatically register all discovered workers
3. Start the task handler with all workers

Directory Structure:
    examples/worker_discovery/
        my_workers/
            order_tasks.py      (3 workers: process_order, validate_order, cancel_order)
            payment_tasks.py    (2 workers: process_payment, refund_payment)
        other_workers/
            notification_tasks.py (2 workers: send_email, send_sms)

Run:
    python examples/worker_discovery_example.py
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add examples directory to path so we can import worker_discovery
examples_dir = Path(__file__).parent
if str(examples_dir) not in sys.path:
    sys.path.insert(0, str(examples_dir))

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_loader import (
    WorkerLoader,
    scan_for_workers,
    auto_discover_workers
)


async def example_1_basic_scanning():
    """
    Example 1: Basic package scanning

    Scan specific packages to discover workers.
    """
    print("\n" + "=" * 70)
    print("Example 1: Basic Package Scanning")
    print("=" * 70)

    loader = WorkerLoader()

    # Scan single package
    loader.scan_packages(['worker_discovery.my_workers'])

    # Print summary
    loader.print_summary()

    print(f"Worker names: {loader.get_worker_names()}")
    print()


async def example_2_multiple_packages():
    """
    Example 2: Scan multiple packages

    Scan multiple packages at once.
    """
    print("\n" + "=" * 70)
    print("Example 2: Multiple Package Scanning")
    print("=" * 70)

    loader = WorkerLoader()

    # Scan multiple packages
    loader.scan_packages([
        'worker_discovery.my_workers',
        'worker_discovery.other_workers'
    ])

    # Print summary
    loader.print_summary()


async def example_3_convenience_function():
    """
    Example 3: Using convenience function

    Use scan_for_workers() convenience function.
    """
    print("\n" + "=" * 70)
    print("Example 3: Convenience Function")
    print("=" * 70)

    # Scan packages using convenience function
    loader = scan_for_workers(
        'worker_discovery.my_workers',
        'worker_discovery.other_workers'
    )

    loader.print_summary()


async def example_4_auto_discovery():
    """
    Example 4: Auto-discovery with summary

    Use auto_discover_workers() for one-liner discovery.
    """
    print("\n" + "=" * 70)
    print("Example 4: Auto-Discovery")
    print("=" * 70)

    # Auto-discover with summary
    loader = auto_discover_workers(
        packages=[
            'worker_discovery.my_workers',
            'worker_discovery.other_workers'
        ],
        print_summary=True
    )

    print(f"Total workers discovered: {loader.get_worker_count()}")
    print()


async def example_5_run_with_discovered_workers():
    """
    Example 5: Run task handler with discovered workers

    This is the typical production use case.
    """
    print("\n" + "=" * 70)
    print("Example 5: Running Task Handler with Discovered Workers")
    print("=" * 70)

    # Auto-discover workers
    loader = auto_discover_workers(
        packages=[
            'worker_discovery.my_workers',
            'worker_discovery.other_workers'
        ],
        print_summary=True
    )

    # Configuration
    api_config = Configuration()

    print(f"Server: {api_config.host}")
    print(f"\nStarting task handler with {loader.get_worker_count()} workers...")
    print("Press Ctrl+C to stop\n")

    # Start task handler with discovered workers
    try:
        async with TaskHandler(configuration=api_config) as task_handler:
            # Set up graceful shutdown
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

    print("\nWorkers stopped. Goodbye!")


async def example_6_selective_scanning():
    """
    Example 6: Selective scanning (non-recursive)

    Only scan top-level package, not subpackages.
    """
    print("\n" + "=" * 70)
    print("Example 6: Selective Scanning (Non-Recursive)")
    print("=" * 70)

    loader = WorkerLoader()

    # Scan only top-level, no subpackages
    loader.scan_packages(['worker_discovery.my_workers'], recursive=False)

    loader.print_summary()


async def example_7_specific_modules():
    """
    Example 7: Scan specific modules

    Scan individual modules instead of entire packages.
    """
    print("\n" + "=" * 70)
    print("Example 7: Specific Module Scanning")
    print("=" * 70)

    loader = WorkerLoader()

    # Scan specific modules
    loader.scan_module('worker_discovery.my_workers.order_tasks')
    loader.scan_module('worker_discovery.other_workers.notification_tasks')
    # Note: payment_tasks not scanned

    loader.print_summary()


async def run_all_examples():
    """Run all examples in sequence"""
    await example_1_basic_scanning()
    await example_2_multiple_packages()
    await example_3_convenience_function()
    await example_4_auto_discovery()
    await example_6_selective_scanning()
    await example_7_specific_modules()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nTo run the task handler with discovered workers, uncomment")
    print("the example_5_run_with_discovered_workers() call in main()\n")


async def main():
    """
    Main entry point
    """
    print("\n" + "=" * 70)
    print("Worker Discovery Examples")
    print("=" * 70)
    print("\nDemonstrates automatic worker discovery from packages,")
    print("similar to Spring's component scanning in Java.\n")

    # Run all examples
    await run_all_examples()

    # Uncomment to run task handler with discovered workers:
    # await example_5_run_with_discovered_workers()


if __name__ == '__main__':
    """
    Run the worker discovery examples.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
