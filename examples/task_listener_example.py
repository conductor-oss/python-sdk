"""
Example demonstrating TaskRunnerEventsListener for pre/post processing of worker tasks.

This example shows how to implement a custom event listener to:
- Log task execution events
- Add custom headers or context before task execution
- Process task results after execution
- Track task timing and errors
- Implement retry logic or custom error handling

The listener pattern is useful for:
- Request/response logging
- Distributed tracing integration
- Custom metrics collection
- Authentication/authorization
- Data enrichment
- Error recovery
"""

import logging
from typing import Union

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.context import get_task_context, TaskInProgress
from conductor.client.worker.worker_task import worker_task
from event_listener_examples import (
    TaskExecutionLogger,
    TaskTimingTracker,
    DistributedTracingListener
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# Example worker tasks (same as asyncio_workers.py)

@worker_task(
    task_definition_name='calculate',
    thread_count=100,
    poll_timeout=10,
    lease_extend_enabled=False
)
async def calculate_fibonacci(n: int) -> int:
    """
    CPU-bound work automatically runs in thread pool.
    For heavy CPU work, consider using multiprocessing TaskHandler instead.

    Note: thread_count=100 limits concurrent CPU-intensive tasks to avoid
    overwhelming the system (GIL contention).
    """
    if n <= 1:
        return n
    return await calculate_fibonacci(n - 1) + await calculate_fibonacci(n - 2)


@worker_task(
    task_definition_name='long_running_task',
    thread_count=5,
    poll_timeout=100,
    lease_extend_enabled=True
)
def long_running_task(job_id: str) -> Union[dict, TaskInProgress]:
    """
    Long-running task that takes ~5 seconds total (5 polls × 1 second).

    Demonstrates:
    - Union[dict, TaskInProgress] return type
    - Using poll_count to track progress
    - callback_after_seconds for polling interval
    - Type-safe handling of in-progress vs completed states

    Args:
        job_id: Job identifier

    Returns:
        TaskInProgress: When still processing (polls 1-4)
        dict: When complete (poll 5)
    """
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    ctx.add_log(f"Processing job {job_id}, poll {poll_count}/5")

    if poll_count < 5:
        # Still processing - return TaskInProgress
        return TaskInProgress(
            callback_after_seconds=1,  # Poll again after 1 second
            output={
                'job_id': job_id,
                'status': 'processing',
                'poll_count': poll_count,
                f'poll_count_{poll_count}': poll_count,
                'progress': poll_count * 20,  # 20%, 40%, 60%, 80%
                'message': f'Working on job {job_id}, poll {poll_count}/5'
            }
        )

    # Complete after 5 polls (5 seconds total)
    ctx.add_log(f"Job {job_id} completed")
    return {
        'job_id': job_id,
        'status': 'completed',
        'result': 'success',
        'total_time_seconds': 5,
        'total_polls': poll_count
    }


def main():
    """Run the example with event listeners."""

    # Configure Conductor connection
    config = Configuration()

    # Create event listeners
    logger_listener = TaskExecutionLogger()
    timing_tracker = TaskTimingTracker()
    tracing_listener = DistributedTracingListener()

    print("=" * 80)
    print("TaskRunnerEventsListener Example")
    print("=" * 80)
    print("")
    print("This example demonstrates event listeners for task pre/post processing:")
    print("  1. TaskExecutionLogger - Logs all task lifecycle events")
    print("  2. TaskTimingTracker - Tracks and reports execution statistics")
    print("  3. DistributedTracingListener - Simulates distributed tracing")
    print("")
    print("Workers available:")
    print("  - calculate: Fibonacci calculator (async)")
    print("  - long_running_task: Multi-poll task with progress tracking")
    print("")
    print("Press Ctrl+C to stop...")
    print("=" * 80)
    print("")

    try:
        # Create task handler with multiple listeners
        with TaskHandler(
            configuration=config,
            scan_for_annotated_workers=True,
            import_modules=["helloworld.greetings_worker", "user_example.user_workers"],
            event_listeners=[
                logger_listener,
                timing_tracker,
                tracing_listener
            ]
        ) as task_handler:
            task_handler.start_processes()
            task_handler.join_processes()

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")

    except Exception as e:
        print(f"\nError: {e}")
        raise

    print("\nWorkers stopped. Goodbye!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
