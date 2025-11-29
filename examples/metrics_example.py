"""
Example demonstrating Prometheus metrics collection and HTTP endpoint exposure.

This example shows how to:
- Enable Prometheus metrics collection for task execution
- Expose metrics via HTTP endpoint for scraping (served from memory)
- Track task poll times, execution times, errors, and more
- Integrate with Prometheus monitoring

Metrics collected:
- task_poll_total: Total number of task polls
- task_poll_time_seconds: Task poll duration
- task_execute_time_seconds: Task execution duration
- task_execute_error_total: Total task execution errors
- task_result_size_bytes: Task result payload size
- http_api_client_request: API request duration with quantiles

HTTP Mode vs File Mode:
- With http_port: Metrics served from memory at /metrics endpoint (no file written)
- Without http_port: Metrics written to file (no HTTP server)

Usage:
    1. Run this example: python3 metrics_example.py
    2. View metrics: curl http://localhost:8000/metrics
    3. Configure Prometheus to scrape: http://localhost:8000/metrics
"""

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.worker.worker_task import worker_task


# Example worker tasks (same as async_worker_example.py)

@worker_task(
    task_definition_name='async_http_task',
    thread_count=10,
    poll_timeout=10
)
async def async_http_worker(url: str = 'https://api.example.com/data', delay: float = 0.1) -> dict:
    """
    Async worker that simulates HTTP requests.

    This worker uses async/await to avoid blocking while waiting for I/O.
    Demonstrates metrics collection for async I/O-bound tasks.
    """
    import asyncio
    from datetime import datetime

    # Simulate async HTTP request
    await asyncio.sleep(delay)

    return {
        'url': url,
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    }


@worker_task(
    task_definition_name='async_data_processor',
    thread_count=10,
    poll_timeout=10
)
async def async_data_processor(data: str, process_time: float = 0.5) -> dict:
    """
    Simple async worker with automatic parameter mapping.

    Input parameters are automatically extracted from task.input_data.
    Return value is automatically set as task.output_data.
    """
    import asyncio
    from datetime import datetime

    # Simulate async data processing
    await asyncio.sleep(process_time)

    # Process the data
    processed = data.upper()

    return {
        'original': data,
        'processed': processed,
        'length': len(processed),
        'processed_at': datetime.now().isoformat()
    }


@worker_task(
    task_definition_name='async_batch_processor',
    thread_count=5,
    poll_timeout=10
)
async def async_batch_processor(items: list) -> dict:
    """
    Process multiple items concurrently using asyncio.gather.

    Demonstrates how async workers can handle concurrent operations
    efficiently without blocking. Shows metrics for batch processing.
    """
    import asyncio
    from datetime import datetime

    async def process_item(item):
        await asyncio.sleep(0.1)  # Simulate I/O operation
        return f"processed_{item}"

    # Process all items concurrently
    results = await asyncio.gather(*[process_item(item) for item in items])

    return {
        'input_count': len(items),
        'results': results,
        'completed_at': datetime.now().isoformat()
    }


@worker_task(
    task_definition_name='sync_cpu_task',
    thread_count=5,
    poll_timeout=10
)
def sync_cpu_worker(n: int = 100000) -> dict:
    """
    Regular synchronous worker for CPU-bound operations.

    Use sync workers when your task is CPU-bound (calculations, parsing, etc.)
    Use async workers when your task is I/O-bound (network, database, files).
    Shows metrics collection for CPU-bound synchronous tasks.
    """
    # CPU-bound calculation
    result = sum(i * i for i in range(n))

    return {'result': result}

# Note: The HTTP server is now built into MetricsCollector.
# Simply specify http_port in MetricsSettings to enable it.


def main():
    """Run the example with metrics collection enabled."""

    # Configure metrics collection
    # The HTTP server is now built-in - just specify the http_port parameter
    metrics_settings = MetricsSettings(
        directory="/tmp/conductor-metrics",  # Temp directory for metrics .db files
        file_name="metrics.log",             # Metrics file name (for file-based access)
        update_interval=0.1,                 # Update every 100ms
        http_port=8000                       # Expose metrics via HTTP on port 8000
    )

    # Configure Conductor connection
    config = Configuration()

    print("=" * 80)
    print("Metrics Collection Example")
    print("=" * 80)
    print("")
    print("This example demonstrates Prometheus metrics collection and exposure.")
    print("")
    print(f"Metrics mode: HTTP (served from memory)")
    print(f"Metrics HTTP endpoint: http://localhost:{metrics_settings.http_port}/metrics")
    print(f"Health check: http://localhost:{metrics_settings.http_port}/health")
    print(f"Note: Metrics are NOT written to file when http_port is specified")
    print("")
    print("Workers available:")
    print("  - async_http_task: Async HTTP simulation (I/O-bound)")
    print("  - async_data_processor: Async data processing")
    print("  - async_batch_processor: Concurrent batch processing")
    print("  - sync_cpu_task: Synchronous CPU-bound calculations")
    print("")
    print("Try these commands:")
    print(f"  curl http://localhost:{metrics_settings.http_port}/metrics")
    print(f"  watch -n 1 'curl -s http://localhost:{metrics_settings.http_port}/metrics | grep task_poll_total'")
    print("")
    print("Press Ctrl+C to stop...")
    print("=" * 80)
    print("")

    try:
        # Create task handler with metrics enabled
        # The HTTP server will be started automatically by the MetricsProvider process
        with TaskHandler(
            configuration=config,
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=True
        ) as task_handler:
            task_handler.start_processes()
            task_handler.join_processes()

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")

    except Exception as e:
        print(f"\nError: {e}")
        raise

    print("\nWorkers stopped. Goodbye!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
