"""
Async example demonstrating the @task_options decorator with async worker tasks.

The @task_options decorator works the same way with async tasks as it does with
synchronous tasks.
"""

import asyncio

from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.shared.worker.task_options import task_options


@task_options(
    timeout_seconds=3600,
    response_timeout_seconds=300,
    retry_count=3,
    retry_logic="EXPONENTIAL_BACKOFF",
    retry_delay_seconds=10,
    backoff_scale_factor=2,
)
@worker_task(task_definition_name="async_process_payment")
async def async_process_payment(task):
    payment_id = task.input_data.get("payment_id")
    amount = task.input_data.get("amount")

    print(f"Processing payment {payment_id} for ${amount}")

    await asyncio.sleep(0.1)

    return {
        "status": "completed",
        "payment_id": payment_id,
        "confirmation": f"CONF-{payment_id}",
    }


@task_options(
    timeout_seconds=7200,
    response_timeout_seconds=600,
    retry_count=5,
    retry_logic="LINEAR_BACKOFF",
    retry_delay_seconds=30,
    concurrent_exec_limit=10,
    rate_limit_per_frequency=100,
    rate_limit_frequency_in_seconds=60,
    description="Async notification sender with rate limiting",
)
@worker_task(task_definition_name="async_send_notification")
async def async_send_notification(task):
    recipient = task.input_data.get("email")
    message = task.input_data.get("message")

    print(f"Sending notification to {recipient}: {message}")

    await asyncio.sleep(0.1)

    return {"status": "sent", "recipient": recipient, "sent_at": "2025-10-13T10:00:00Z"}


@task_options(
    timeout_seconds=1800,
    response_timeout_seconds=120,
    retry_count=2,
    retry_logic="FIXED",
    retry_delay_seconds=5,
    timeout_policy="RETRY",
    description="Fast async task with minimal retry",
)
@worker_task(task_definition_name="async_validate_data")
async def async_validate_data(task):
    data = task.input_data.get("data")

    print(f"Validating data: {data}")

    await asyncio.sleep(0.05)

    if not data:
        return {"status": "failed", "error": "No data provided"}

    return {"status": "valid", "validated_data": data}


@task_options(
    timeout_seconds=3600,
    response_timeout_seconds=300,
    retry_count=10,
    retry_logic="EXPONENTIAL_BACKOFF",
    retry_delay_seconds=5,
    backoff_scale_factor=3,
    timeout_policy="TIME_OUT_WF",
    concurrent_exec_limit=5,
    description="Heavy async processing task with aggressive retry",
)
@worker_task(task_definition_name="async_heavy_computation")
async def async_heavy_computation(task):
    iterations = task.input_data.get("iterations", 1000)

    print(f"Running heavy computation with {iterations} iterations")

    await asyncio.sleep(0.1)

    result = sum(range(iterations))

    return {"status": "completed", "result": result, "iterations": iterations}


async def main():
    config = Configuration()
    config.apply_logging_config()

    print("Starting async workers with task options...")
    print("\nConfigured async tasks:")
    print("1. async_process_payment - EXPONENTIAL_BACKOFF retry with 3 attempts")
    print(
        "2. async_send_notification - LINEAR_BACKOFF retry with rate limiting (100 req/min)"
    )
    print("3. async_validate_data - FIXED retry with 2 attempts")
    print(
        "4. async_heavy_computation - EXPONENTIAL_BACKOFF with high concurrency limit\n"
    )

    task_handler = TaskHandler(
        workers=[],
        configuration=config,
        scan_for_annotated_workers=True,
        import_modules=[],
    )

    try:
        task_handler.start_processes()
        task_handler.join_processes()
    finally:
        task_handler.stop_processes()


if __name__ == "__main__":
    asyncio.run(main())
