import signal
from typing import Union

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.context import get_task_context, TaskInProgress
from conductor.client.worker.worker_task import worker_task


@worker_task(
    task_definition_name='calculate',
    poll_interval_millis=100  # Multiprocessing uses poll_interval instead of poll_timeout
)
def calculate_fibonacci(n: int) -> int:
    """
    CPU-bound work benefits from true parallelism in multiprocessing mode.
    Bypasses Python GIL for better CPU utilization.

    Note: Multiprocessing is ideal for CPU-intensive tasks like this.
    """
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


@worker_task(
    task_definition_name='long_running_task',
    poll_interval_millis=100
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
    """
    Main entry point demonstrating multiprocessing task handler.

    Uses true parallelism - each worker runs in its own process,
    bypassing Python's GIL for better CPU utilization.
    """

    # Configuration - defaults to reading from environment variables:
    # - CONDUCTOR_SERVER_URL: e.g., https://developer.orkescloud.com/api
    # - CONDUCTOR_AUTH_KEY: API key
    # - CONDUCTOR_AUTH_SECRET: API secret
    api_config = Configuration()

    print("\nStarting multiprocessing workers... Press Ctrl+C to stop\n")

    try:
        # Create TaskHandler with worker discovery
        task_handler = TaskHandler(
            configuration=api_config,
            scan_for_annotated_workers=True,
            import_modules=["helloworld.greetings_worker", "user_example.user_workers"]
        )

        # Start worker processes (blocks until stopped)
        # This will spawn separate processes for each worker
        task_handler.start_processes()

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")

    except Exception as e:
        print(f"\n\nError: {e}")
        raise

    print("\nWorkers stopped. Goodbye!")


if __name__ == '__main__':
    """
    Run the multiprocessing workers.

    Key differences from AsyncIO:
    - Uses TaskHandler instead of TaskHandlerAsyncIO
    - Each worker runs in its own process (true parallelism)
    - Better for CPU-bound tasks (bypasses GIL)
    - Higher memory footprint but better CPU utilization
    - Uses poll_interval instead of poll_timeout

    To run:
        python examples/multiprocessing_workers.py
    """
    try:
        main()
    except KeyboardInterrupt:
        pass
