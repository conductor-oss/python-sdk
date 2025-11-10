"""
Task Context Example

Demonstrates how to use TaskContext to access task information and modify
task results during execution.

The TaskContext provides:
- Access to task metadata (task_id, workflow_id, retry_count, etc.)
- Ability to add logs visible in Conductor UI
- Ability to set callback delays for polling/retry patterns
- Access to input parameters

Run:
    python examples/task_context_example.py
"""

import asyncio
import signal
from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.context.task_context import get_task_context
from conductor.client.worker.worker_task import worker_task


# Example 1: Basic TaskContext usage - accessing task info
@worker_task(
    task_definition_name='task_info_example',
    thread_count=5
)
def task_info_example(data: dict) -> dict:
    """
    Demonstrates accessing task information via TaskContext.
    """
    # Get the current task context
    ctx = get_task_context()

    # Access task information
    task_id = ctx.get_task_id()
    workflow_id = ctx.get_workflow_instance_id()
    retry_count = ctx.get_retry_count()
    poll_count = ctx.get_poll_count()

    print(f"Task ID: {task_id}")
    print(f"Workflow ID: {workflow_id}")
    print(f"Retry Count: {retry_count}")
    print(f"Poll Count: {poll_count}")

    return {
        "task_id": task_id,
        "workflow_id": workflow_id,
        "retry_count": retry_count,
        "result": "processed"
    }


# Example 2: Adding logs via TaskContext
@worker_task(
    task_definition_name='logging_example',
    thread_count=5
)
async def logging_example(order_id: str, items: list) -> dict:
    """
    Demonstrates adding logs that will be visible in Conductor UI.
    """
    ctx = get_task_context()

    # Add logs as processing progresses
    ctx.add_log(f"Starting to process order {order_id}")
    ctx.add_log(f"Order has {len(items)} items")

    for i, item in enumerate(items):
        await asyncio.sleep(0.1)  # Simulate processing
        ctx.add_log(f"Processed item {i+1}/{len(items)}: {item}")

    ctx.add_log("Order processing completed")

    return {
        "order_id": order_id,
        "items_processed": len(items),
        "status": "completed"
    }


# Example 3: Callback pattern - polling external service
@worker_task(
    task_definition_name='polling_example',
    thread_count=10
)
async def polling_example(job_id: str) -> dict:
    """
    Demonstrates using callback_after for polling pattern.

    The task will check if a job is complete, and if not, set a callback
    to check again in 30 seconds.
    """
    ctx = get_task_context()

    ctx.add_log(f"Checking status of job {job_id}")

    # Simulate checking external service
    import random
    is_complete = random.random() > 0.7  # 30% chance of completion

    if is_complete:
        ctx.add_log(f"Job {job_id} is complete!")
        return {
            "job_id": job_id,
            "status": "completed",
            "result": "Job finished successfully"
        }
    else:
        # Job still running - poll again in 30 seconds
        ctx.add_log(f"Job {job_id} still running, will check again in 30s")
        ctx.set_callback_after(30)

        return {
            "job_id": job_id,
            "status": "in_progress",
            "message": "Job still running"
        }


# Example 4: Retry logic with context awareness
@worker_task(
    task_definition_name='retry_aware_example',
    thread_count=5
)
def retry_aware_example(operation: str) -> dict:
    """
    Demonstrates handling retries differently based on retry count.
    """
    ctx = get_task_context()

    retry_count = ctx.get_retry_count()

    if retry_count > 0:
        ctx.add_log(f"This is retry attempt #{retry_count}")
        # Could implement exponential backoff, different logic, etc.

    ctx.add_log(f"Executing operation: {operation}")

    # Simulate operation
    import random
    success = random.random() > 0.3

    if success:
        ctx.add_log("Operation succeeded")
        return {"status": "success", "operation": operation}
    else:
        ctx.add_log("Operation failed, will retry")
        raise Exception("Operation failed")


# Example 5: Combining context with async operations
@worker_task(
    task_definition_name='async_context_example',
    thread_count=10
)
async def async_context_example(urls: list) -> dict:
    """
    Demonstrates using TaskContext in async worker with concurrent operations.
    """
    ctx = get_task_context()

    ctx.add_log(f"Starting to fetch {len(urls)} URLs")
    ctx.add_log(f"Task ID: {ctx.get_task_id()}")

    results = []

    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            for i, url in enumerate(urls):
                ctx.add_log(f"Fetching URL {i+1}/{len(urls)}: {url}")

                try:
                    response = await client.get(url)
                    results.append({
                        "url": url,
                        "status": response.status_code,
                        "success": True
                    })
                    ctx.add_log(f"✓ {url} - {response.status_code}")
                except Exception as e:
                    results.append({
                        "url": url,
                        "error": str(e),
                        "success": False
                    })
                    ctx.add_log(f"✗ {url} - Error: {e}")

    except Exception as e:
        ctx.add_log(f"Fatal error: {e}")
        raise

    ctx.add_log(f"Completed fetching {len(results)} URLs")

    return {
        "total": len(urls),
        "successful": sum(1 for r in results if r.get("success")),
        "results": results
    }


# Example 6: Accessing input parameters via context
@worker_task(
    task_definition_name='input_access_example',
    thread_count=5
)
def input_access_example() -> dict:
    """
    Demonstrates accessing task input via context.

    This is useful when you want to access raw input data or when
    using dynamic parameter inspection.
    """
    ctx = get_task_context()

    # Get all input parameters
    input_data = ctx.get_input()

    ctx.add_log(f"Received input parameters: {list(input_data.keys())}")

    # Process based on input
    for key, value in input_data.items():
        ctx.add_log(f"  {key} = {value}")

    return {
        "processed_keys": list(input_data.keys()),
        "input_count": len(input_data)
    }


async def main():
    """
    Main entry point demonstrating TaskContext examples.
    """
    api_config = Configuration()

    print("=" * 60)
    print("Conductor TaskContext Examples")
    print("=" * 60)
    print(f"Server: {api_config.host}")
    print()
    print("Workers demonstrating TaskContext usage:")
    print("  • task_info_example - Access task metadata")
    print("  • logging_example - Add logs to task")
    print("  • polling_example - Use callback_after for polling")
    print("  • retry_aware_example - Handle retries intelligently")
    print("  • async_context_example - TaskContext in async workers")
    print("  • input_access_example - Access task input via context")
    print()
    print("Key TaskContext Features:")
    print("  ✓ Access task metadata (ID, workflow ID, retry count)")
    print("  ✓ Add logs visible in Conductor UI")
    print("  ✓ Set callback delays for polling patterns")
    print("  ✓ Thread-safe and async-safe (uses contextvars)")
    print("=" * 60)
    print("\nStarting workers... Press Ctrl+C to stop\n")

    try:
        async with TaskHandlerAsyncIO(configuration=api_config) as task_handler:
            loop = asyncio.get_running_loop()

            def signal_handler():
                print("\n\nReceived shutdown signal, stopping workers...")
                loop.create_task(task_handler.stop())

            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, signal_handler)

            await task_handler.wait()

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")

    except Exception as e:
        print(f"\n\nError: {e}")
        raise

    print("\nWorkers stopped. Goodbye!")


if __name__ == '__main__':
    """
    Run the TaskContext examples.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
