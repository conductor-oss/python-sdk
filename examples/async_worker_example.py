"""
Example demonstrating async workers with Conductor Python SDK.

This example shows how to write async workers for I/O-bound operations
that benefit from the persistent background event loop for better performance.
"""

import asyncio
from datetime import datetime
from conductor.client.configuration.configuration import Configuration
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_task import WorkerTask
from conductor.client.http.models import Task, TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus


# Example 1: Async worker as a function with Task parameter
async def async_http_worker(task: Task) -> TaskResult:
    """
    Async worker that simulates HTTP requests.

    This worker uses async/await to avoid blocking while waiting for I/O.
    The SDK automatically uses a persistent background event loop for
    efficient execution.
    """
    task_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
    )

    url = task.input_data.get('url', 'https://api.example.com/data')
    delay = task.input_data.get('delay', 0.1)

    # Simulate async HTTP request
    await asyncio.sleep(delay)

    task_result.add_output_data('url', url)
    task_result.add_output_data('status', 'success')
    task_result.add_output_data('timestamp', datetime.now().isoformat())
    task_result.status = TaskResultStatus.COMPLETED

    return task_result


# Example 2: Async worker as an annotation with automatic input/output mapping
@WorkerTask(task_definition_name='async_data_processor', poll_interval=1.0)
async def async_data_processor(data: str, process_time: float = 0.5) -> dict:
    """
    Simple async worker with automatic parameter mapping.

    Input parameters are automatically extracted from task.input_data.
    Return value is automatically set as task.output_data.
    """
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


# Example 3: Async worker for concurrent operations
@WorkerTask(task_definition_name='async_batch_processor')
async def async_batch_processor(items: list) -> dict:
    """
    Process multiple items concurrently using asyncio.gather.

    Demonstrates how async workers can handle concurrent operations
    efficiently without blocking.
    """

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


# Example 4: Sync worker for comparison (CPU-bound)
def sync_cpu_worker(task: Task) -> TaskResult:
    """
    Regular synchronous worker for CPU-bound operations.

    Use sync workers when your task is CPU-bound (calculations, parsing, etc.)
    Use async workers when your task is I/O-bound (network, database, files).
    """
    task_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
    )

    # CPU-bound calculation
    n = task.input_data.get('n', 100000)
    result = sum(i * i for i in range(n))

    task_result.add_output_data('result', result)
    task_result.status = TaskResultStatus.COMPLETED

    return task_result


def main():
    """
    Run both async and sync workers together.

    The SDK automatically detects async functions and executes them
    using the persistent background event loop for optimal performance.
    """
    # Configuration
    configuration = Configuration(
        server_api_url='http://localhost:8080/api',
        debug=True,
    )

    # Mix of async and sync workers
    workers = [
        # Async workers - optimized for I/O operations
        Worker(
            task_definition_name='async_http_task',
            execute_function=async_http_worker,
            poll_interval=1.0
        ),
        # Note: Annotated workers (@WorkerTask) are automatically discovered
        # when scan_for_annotated_workers=True

        # Sync worker - for CPU-bound operations
        Worker(
            task_definition_name='sync_cpu_task',
            execute_function=sync_cpu_worker,
            poll_interval=1.0
        ),
    ]

    print("Starting workers...")
    print("- Async workers use persistent background event loop (1.5-2x faster)")
    print("- Sync workers run normally for CPU-bound operations")
    print()

    # Start workers with annotated worker scanning enabled
    with TaskHandler(workers, configuration, scan_for_annotated_workers=True) as task_handler:
        task_handler.start_processes()
        task_handler.join_processes()


if __name__ == '__main__':
    main()
