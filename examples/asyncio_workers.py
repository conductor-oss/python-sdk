import os
import shutil
from typing import Union

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context import get_task_context, TaskInProgress
from conductor.client.worker.worker_task import worker_task
from examples.task_listener_example import TaskExecutionLogger


@worker_task(
    task_definition_name='calculate',
    thread_count=100,  # Lower concurrency for CPU-bound tasks
    poll_timeout=10,
    lease_extend_enabled=False
)
async def calculate_fibonacci(n: int) -> int:
    """
    CPU-bound work automatically runs in thread pool.
    For heavy CPU work, consider using multiprocessing TaskHandler instead.

    Note: thread_count=4 limits concurrent CPU-intensive tasks to avoid
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
    """
    Main entry point demonstrating TaskHandler with async workers.
    """

    # Configuration - defaults to reading from environment variables:
    # - CONDUCTOR_SERVER_URL: e.g., https://developer.orkescloud.com/api
    # - CONDUCTOR_AUTH_KEY: API key
    # - CONDUCTOR_AUTH_SECRET: API secret
    api_config = Configuration()

    # Configure metrics publishing (optional)
    # Create a dedicated directory for metrics to avoid conflicts
    metrics_dir = os.path.join('/Users/viren/', 'conductor_metrics')

    # Clean up any stale metrics data from previous runs
    if os.path.exists(metrics_dir):
        shutil.rmtree(metrics_dir)
    os.makedirs(metrics_dir, exist_ok=True)

    # Prometheus metrics will be written to the metrics directory every 10 seconds
    metrics_settings = MetricsSettings(
        directory=metrics_dir,
        file_name='conductor_metrics.prom',
        update_interval=10
    )

    print("\nStarting workers... Press Ctrl+C to stop")
    print(f"Metrics will be published to: {metrics_dir}/conductor_metrics.prom\n")

    # Using TaskHandler with async workers
    # Async workers automatically use BackgroundEventLoop for efficient async execution
    try:
        with TaskHandler(
            configuration=api_config,
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=True,
            import_modules=["helloworld.greetings_worker", "user_example.user_workers"]
        ) as task_handler:
            task_handler.start_processes()
            task_handler.join_processes()

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")

    except Exception as e:
        print(f"\n\nError: {e}")
        raise

    print("\nWorkers stopped. Goodbye!")


if __name__ == '__main__':
    """
    Run the main function with TaskHandler.

    Async Execution:
    ----------------
    - Async workers (async def) automatically use BackgroundEventLoop
    - Execution mode is detected from function signature (def vs async def)
    - async def provides 10-100x better concurrency for I/O-bound workloads
    - BackgroundEventLoop is 1.5-2x faster than asyncio.run()

    Metrics Available:
    ------------------
    The metrics file will contain Prometheus-formatted metrics including:
    - conductor_task_poll: Number of task polls
    - conductor_task_poll_time: Time spent polling for tasks
    - conductor_task_poll_error: Number of poll errors
    - conductor_task_execute_time: Time spent executing tasks
    - conductor_task_execute_error: Number of task execution errors
    - conductor_task_result_size: Size of task results

    To view metrics:
        cat /tmp/conductor_metrics/conductor_metrics.prom

    To scrape with Prometheus:
        scrape_configs:
          - job_name: 'conductor-workers'
            static_configs:
              - targets: ['localhost:9090']
            file_sd_configs:
              - files:
                  - /tmp/conductor_metrics/conductor_metrics.prom
    """
    try:
        main()
    except KeyboardInterrupt:
        pass
