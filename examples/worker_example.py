"""
Comprehensive Worker Example
=============================

Demonstrates both async and sync workers with practical use cases.

Async Workers (async def):
--------------------------
- Best for I/O-bound tasks: HTTP calls, database queries, file operations
- High concurrency (100+ concurrent tasks per thread)
- Runs in BackgroundEventLoop for efficient async execution
- Configure with thread_count for concurrency control

Sync Workers (def):
-------------------
- Best for CPU-bound tasks or legacy code
- Moderate concurrency (limited by thread_count)
- Runs in thread pool to avoid blocking
- For heavy CPU work, consider multiprocessing TaskHandler

Task Lifecycle:
---------------
1. Poll → Worker polls Conductor for tasks
2. Execute → Task function runs (async or sync)
3. Update → Result sent back to Conductor
4. Repeat

Metrics:
--------
- HTTP mode (recommended): Built-in server at http://localhost:8000/metrics
- File mode: Writes to disk (higher overhead)
- Automatic aggregation across processes
- Event-driven collection (zero coupling with worker logic)
"""

import asyncio
import logging
import os
import shutil
import time
from typing import Union

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context import get_task_context, TaskInProgress
from conductor.client.worker.worker_task import worker_task


# ============================================================================
# ASYNC WORKERS - I/O-Bound Tasks
# ============================================================================

@worker_task(
    task_definition_name='fetch_user_data',
    thread_count=50,  # High concurrency for I/O-bound tasks
    poll_timeout=100,
    lease_extend_enabled=False
)
async def fetch_user_data(user_id: str) -> dict:
    """
    Async worker for I/O-bound operations (e.g., HTTP API calls, database queries).

    Perfect for:
    - REST API calls
    - Database queries
    - File I/O operations
    - Any operation that waits for external resources

    Benefits:
    - 10-100x better concurrency than sync for I/O
    - Efficient resource usage (single thread, many concurrent tasks)
    - Native async/await support

    Args:
        user_id: User identifier to fetch

    Returns:
        dict: User data with profile information
    """
    ctx = get_task_context()
    ctx.add_log(f"Fetching user data for user_id={user_id}")

    # Simulate async HTTP call or database query
    await asyncio.sleep(0.5)  # Replace with actual async I/O: await aiohttp.get(...)

    ctx.add_log(f"Successfully fetched user data for user_id={user_id}")

    return {
        'user_id': user_id,
        'name': f'User {user_id}',
        'email': f'user{user_id}@example.com',
        'status': 'active',
        'fetch_time': time.time()
    }


@worker_task(
    task_definition_name='send_notification',
    thread_count=100,  # Very high concurrency for fast I/O tasks
    poll_timeout=100,
    lease_extend_enabled=False
)
async def send_notification(user_id: str, message: str) -> dict:
    """
    Async worker for sending notifications (email, SMS, push, etc.).

    Demonstrates:
    - Lightweight async tasks
    - High concurrency (100+ concurrent tasks)
    - Fast I/O operations
    - Can return None (no result needed)

    Args:
        user_id: User to notify
        message: Notification message

    Returns:
        dict: Notification status
    """
    ctx = get_task_context()
    ctx.add_log(f"Sending notification to user_id={user_id}: {message}")

    # Simulate async notification service call
    await asyncio.sleep(0.2)  # Replace with: await send_email(...) or await push_notification(...)

    ctx.add_log(f"Notification sent to user_id={user_id}")

    return {
        'user_id': user_id,
        'status': 'sent',
        'sent_at': time.time()
    }


@worker_task(
    task_definition_name='async_returns_none',
    thread_count=20,
    poll_timeout=100,
    lease_extend_enabled=False
)
async def async_returns_none(data: dict) -> None:
    """
    Async worker that returns None (no result needed).

    Use case: Fire-and-forget tasks like logging, cleanup, cache invalidation.

    Note: SDK 1.2.6+ supports async tasks returning None using sentinel pattern.

    Args:
        data: Input data to process

    Returns:
        None: No result needed
    """
    ctx = get_task_context()
    ctx.add_log(f"Processing data: {data}")

    await asyncio.sleep(0.1)

    ctx.add_log("Processing complete - no return value needed")
    # Explicitly return None or just don't return anything
    return None


# ============================================================================
# SYNC WORKERS - CPU-Bound Tasks or Legacy Code
# ============================================================================

@worker_task(
    task_definition_name='process_image',
    thread_count=4,  # Lower concurrency for CPU-bound tasks
    poll_timeout=100,
    lease_extend_enabled=True  # Enable for tasks that take >30 seconds
)
def process_image(image_url: str, filters: list) -> dict:
    """
    Sync worker for CPU-bound image processing.

    Perfect for:
    - Image/video processing
    - Data transformation
    - Heavy computation
    - Legacy synchronous code

    Note: For heavy CPU work across multiple cores, use multiprocessing TaskHandler.

    Args:
        image_url: URL of image to process
        filters: List of filters to apply

    Returns:
        dict: Processing result with output URL
    """
    ctx = get_task_context()
    ctx.add_log(f"Processing image: {image_url} with filters: {filters}")

    # Simulate CPU-intensive image processing
    time.sleep(2)  # Replace with actual processing: PIL.Image.open(...).filter(...)

    output_url = f"{image_url}_processed"
    ctx.add_log(f"Image processing complete: {output_url}")

    return {
        'input_url': image_url,
        'output_url': output_url,
        'filters_applied': filters,
        'processing_time_seconds': 2
    }


@worker_task(
    task_definition_name='generate_report',
    thread_count=2,  # Very low concurrency for heavy CPU tasks
    poll_timeout=100,
    lease_extend_enabled=True  # Enable for heavy computation that takes time
)
def generate_report(report_type: str, date_range: dict) -> dict:
    """
    Sync worker for CPU-intensive report generation.

    Demonstrates:
    - Heavy CPU-bound work
    - Low concurrency (avoid GIL contention)
    - Lease extension for long-running tasks

    Args:
        report_type: Type of report to generate
        date_range: Date range for the report

    Returns:
        dict: Report data and metadata
    """
    ctx = get_task_context()
    ctx.add_log(f"Generating {report_type} report for {date_range}")

    # Simulate heavy computation (data aggregation, analysis, etc.)
    time.sleep(3)

    ctx.add_log(f"Report generation complete: {report_type}")

    return {
        'report_type': report_type,
        'date_range': date_range,
        'status': 'completed',
        'row_count': 10000,
        'file_size_mb': 5.2
    }


@worker_task(
    task_definition_name='long_running_task',
    thread_count=5,
    poll_timeout=100,
    lease_extend_enabled=True  # Enable for long-running tasks
)
def long_running_task(job_id: str) -> Union[dict, TaskInProgress]:
    """
    Long-running task that uses TaskInProgress for polling-based execution.

    Demonstrates:
    - Union[dict, TaskInProgress] return type
    - Using poll_count to track progress
    - callback_after_seconds for polling interval
    - Incremental progress updates

    Use case: Tasks that take minutes/hours and need progress tracking.

    Args:
        job_id: Job identifier

    Returns:
        TaskInProgress: When still processing (polls 1-4)
        dict: When complete (poll 5+)
    """
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    ctx.add_log(f"Processing job {job_id}, poll {poll_count}/5")

    if poll_count < 5:
        # Still processing - return TaskInProgress with incremental updates
        return TaskInProgress(
            callback_after_seconds=1,  # Poll again after 1 second
            output={
                'job_id': job_id,
                'status': 'processing',
                'poll_count': poll_count,
                'progress_percent': poll_count * 20,  # 20%, 40%, 60%, 80%
                'message': f'Working on job {job_id}, poll {poll_count}/5'
            }
        )

    # Complete after 5 polls (~5 seconds total)
    ctx.add_log(f"Job {job_id} completed")
    return {
        'job_id': job_id,
        'status': 'completed',
        'result': 'success',
        'total_time_seconds': 5,
        'total_polls': poll_count
    }


# ============================================================================
# MAIN - TaskHandler Setup
# ============================================================================

def main():
    """
    Main entry point demonstrating TaskHandler with both async and sync workers.

    Configuration:
    - Reads from environment variables (CONDUCTOR_SERVER_URL, CONDUCTOR_AUTH_KEY, etc.)
    - HTTP metrics mode (recommended): Built-in server on port 8000
    - Auto-discovers workers with @worker_task decorator
    """

    # Configuration from environment variables
    api_config = Configuration()

    # Metrics configuration - HTTP mode (recommended)
    metrics_dir = os.path.join('/Users/viren/', 'conductor_metrics')

    # Clean up any stale metrics data from previous runs
    if os.path.exists(metrics_dir):
        shutil.rmtree(metrics_dir)
    os.makedirs(metrics_dir, exist_ok=True)

    metrics_settings = MetricsSettings(
        directory=metrics_dir,
        update_interval=10,
        http_port=8000  # Built-in HTTP server for metrics
    )

    print("=" * 80)
    print("Conductor Worker Example - Async and Sync Workers")
    print("=" * 80)
    print()
    print("Workers registered:")
    print("  Async (I/O-bound):")
    print("    - fetch_user_data: Fetch user data from API/DB")
    print("    - send_notification: Send email/SMS/push notifications")
    print("    - async_returns_none: Fire-and-forget task (returns None)")
    print()
    print("  Sync (CPU-bound):")
    print("    - process_image: CPU-intensive image processing")
    print("    - generate_report: Heavy data aggregation and analysis")
    print("    - long_running_task: Polling-based long-running task")
    print()
    print(f"Metrics available at: http://localhost:8000/metrics")
    print(f"Health check at: http://localhost:8000/health")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()

    try:
        with TaskHandler(
            configuration=api_config,
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=True,
            import_modules=[]  # Add modules if workers are in separate files
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
    Run the worker example.

    Quick Start:
    ------------
    1. Set environment variables:
       export CONDUCTOR_SERVER_URL=https://your-server.com/api
       export CONDUCTOR_AUTH_KEY=your_key
       export CONDUCTOR_AUTH_SECRET=your_secret

    2. Run the workers:
       python examples/worker_example.py

    3. View metrics:
       curl http://localhost:8000/metrics

    Choosing Async vs Sync:
    -----------------------
    Use ASYNC (async def) for:
    - HTTP API calls
    - Database queries
    - File I/O operations
    - Network operations
    - Any I/O-bound work

    Use SYNC (def) for:
    - CPU-intensive computation
    - Legacy synchronous code
    - Simple tasks with no I/O
    - When you can't use async libraries

    Performance Guidelines:
    -----------------------
    Async workers:
    - thread_count: 50-100 for I/O-bound tasks
    - Can handle 100+ concurrent tasks per thread
    - 10-100x better than sync for I/O

    Sync workers:
    - thread_count: 2-10 for CPU-bound tasks
    - Avoid high concurrency (GIL contention)
    - For heavy CPU work, use multiprocessing TaskHandler

    Metrics Available:
    ------------------
    - conductor_task_poll: Number of task polls
    - conductor_task_poll_time: Time spent polling
    - conductor_task_execute_time: Task execution time
    - conductor_task_execute_error: Execution errors
    - conductor_task_result_size: Result payload size

    Prometheus Scrape Config:
    -------------------------
    scrape_configs:
      - job_name: 'conductor-workers'
        static_configs:
          - targets: ['localhost:8000']
    """
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        main()
    except KeyboardInterrupt:
        pass
