"""
Worker Configuration Example

Demonstrates hierarchical worker configuration using environment variables.

This example shows how to override worker settings at deployment time without
changing code, using a three-tier configuration hierarchy:

1. Code-level defaults (lowest priority)
2. Global worker config: conductor.worker.all.<property>
3. Worker-specific config: conductor.worker.<worker_name>.<property>

Usage:
    # Run with code defaults
    python worker_configuration_example.py

    # Run with global overrides
    export conductor.worker.all.domain=production
    export conductor.worker.all.poll_interval=250
    python worker_configuration_example.py

    # Run with worker-specific overrides
    export conductor.worker.all.domain=production
    export conductor.worker.critical_task.thread_count=20
    export conductor.worker.critical_task.poll_interval=100
    python worker_configuration_example.py
"""

import asyncio
import os
from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task
from conductor.client.worker.worker_config import resolve_worker_config, get_worker_config_summary


# Example 1: Standard worker with default configuration
@worker_task(
    task_definition_name='process_order',
    poll_interval_millis=1000,
    domain='dev',
    thread_count=5,
    poll_timeout=100
)
async def process_order(order_id: str) -> dict:
    """Process an order - standard priority"""
    return {
        'status': 'processed',
        'order_id': order_id,
        'worker_type': 'standard'
    }


# Example 2: High-priority worker that might need more resources in production
@worker_task(
    task_definition_name='critical_task',
    poll_interval_millis=1000,
    domain='dev',
    thread_count=5,
    poll_timeout=100
)
async def critical_task(task_id: str) -> dict:
    """Critical task that needs high priority in production"""
    return {
        'status': 'completed',
        'task_id': task_id,
        'priority': 'critical'
    }


# Example 3: Background worker that can run with fewer resources
@worker_task(
    task_definition_name='background_task',
    poll_interval_millis=2000,
    domain='dev',
    thread_count=2,
    poll_timeout=200
)
async def background_task(job_id: str) -> dict:
    """Background task - low priority"""
    return {
        'status': 'completed',
        'job_id': job_id,
        'priority': 'low'
    }


def print_configuration_examples():
    """Print examples of how configuration hierarchy works"""
    print("\n" + "="*80)
    print("Worker Configuration Hierarchy Examples")
    print("="*80)

    # Show current environment variables
    print("\nCurrent Environment Variables:")
    env_vars = {k: v for k, v in os.environ.items() if k.startswith('conductor.worker')}
    if env_vars:
        for key, value in sorted(env_vars.items()):
            print(f"  {key} = {value}")
    else:
        print("  (No conductor.worker.* environment variables set)")

    print("\n" + "-"*80)

    # Example 1: process_order configuration
    print("\n1. Standard Worker (process_order):")
    print("   Code defaults: poll_interval=1000, domain='dev', thread_count=5")

    config1 = resolve_worker_config(
        worker_name='process_order',
        poll_interval=1000,
        domain='dev',
        thread_count=5,
        poll_timeout=100
    )
    print(f"\n   Resolved configuration:")
    print(f"     poll_interval: {config1['poll_interval']}")
    print(f"     domain: {config1['domain']}")
    print(f"     thread_count: {config1['thread_count']}")
    print(f"     poll_timeout: {config1['poll_timeout']}")

    # Example 2: critical_task configuration
    print("\n2. Critical Worker (critical_task):")
    print("   Code defaults: poll_interval=1000, domain='dev', thread_count=5")

    config2 = resolve_worker_config(
        worker_name='critical_task',
        poll_interval=1000,
        domain='dev',
        thread_count=5,
        poll_timeout=100
    )
    print(f"\n   Resolved configuration:")
    print(f"     poll_interval: {config2['poll_interval']}")
    print(f"     domain: {config2['domain']}")
    print(f"     thread_count: {config2['thread_count']}")
    print(f"     poll_timeout: {config2['poll_timeout']}")

    # Example 3: background_task configuration
    print("\n3. Background Worker (background_task):")
    print("   Code defaults: poll_interval=2000, domain='dev', thread_count=2")

    config3 = resolve_worker_config(
        worker_name='background_task',
        poll_interval=2000,
        domain='dev',
        thread_count=2,
        poll_timeout=200
    )
    print(f"\n   Resolved configuration:")
    print(f"     poll_interval: {config3['poll_interval']}")
    print(f"     domain: {config3['domain']}")
    print(f"     thread_count: {config3['thread_count']}")
    print(f"     poll_timeout: {config3['poll_timeout']}")

    print("\n" + "-"*80)
    print("\nConfiguration Priority: Worker-specific > Global > Code defaults")
    print("\nExample Environment Variables:")
    print("  # Global override (all workers)")
    print("  export conductor.worker.all.domain=production")
    print("  export conductor.worker.all.poll_interval=250")
    print()
    print("  # Worker-specific override (only critical_task)")
    print("  export conductor.worker.critical_task.thread_count=20")
    print("  export conductor.worker.critical_task.poll_interval=100")
    print("\n" + "="*80 + "\n")


async def main():
    """Main function to demonstrate worker configuration"""

    # Print configuration examples
    print_configuration_examples()

    # Note: This example doesn't actually connect to Conductor server
    # It just demonstrates the configuration resolution

    print("Configuration resolution complete!")
    print("\nTo see different configurations, try setting environment variables:")
    print("\n  # Test global override:")
    print("  export conductor.worker.all.poll_interval=500")
    print("  python worker_configuration_example.py")
    print("\n  # Test worker-specific override:")
    print("  export conductor.worker.critical_task.thread_count=20")
    print("  python worker_configuration_example.py")
    print("\n  # Test production-like scenario:")
    print("  export conductor.worker.all.domain=production")
    print("  export conductor.worker.all.poll_interval=250")
    print("  export conductor.worker.critical_task.thread_count=50")
    print("  export conductor.worker.critical_task.poll_interval=50")
    print("  python worker_configuration_example.py")


if __name__ == '__main__':
    asyncio.run(main())
