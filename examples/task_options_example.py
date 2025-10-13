"""
Example demonstrating the @task_options decorator for configuring task definitions.

The @task_options decorator allows you to configure task execution parameters
declaratively on your worker functions. When tasks are registered, these options
are automatically applied to the task definition.
"""

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task
from conductor.shared.worker.task_options import task_options


@task_options(
    timeout_seconds=3600,
    response_timeout_seconds=300,
    retry_count=3,
    retry_logic="EXPONENTIAL_BACKOFF",
    retry_delay_seconds=10,
    backoff_scale_factor=2,
)
@worker_task(task_definition_name="process_payment")
def process_payment(task):
    payment_id = task.input_data.get("payment_id")
    amount = task.input_data.get("amount")

    print(f"Processing payment {payment_id} for ${amount}")

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
    description="Sends notification emails with rate limiting",
)
@worker_task(task_definition_name="send_notification")
def send_notification(task):
    recipient = task.input_data.get("email")
    message = task.input_data.get("message")

    print(f"Sending notification to {recipient}: {message}")

    return {"status": "sent", "recipient": recipient, "sent_at": "2025-10-13T10:00:00Z"}


@task_options(
    timeout_seconds=1800,
    response_timeout_seconds=120,
    retry_count=2,
    retry_logic="FIXED",
    retry_delay_seconds=5,
    timeout_policy="RETRY",
    description="Fast task with minimal retry",
)
@worker_task(task_definition_name="validate_data")
def validate_data(task):
    data = task.input_data.get("data")

    print(f"Validating data: {data}")

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
    description="Heavy processing task with aggressive retry",
)
@worker_task(task_definition_name="heavy_computation")
def heavy_computation(task):
    iterations = task.input_data.get("iterations", 1000)

    print(f"Running heavy computation with {iterations} iterations")

    result = sum(range(iterations))

    return {"status": "completed", "result": result, "iterations": iterations}


@task_options(
    timeout_seconds=600,
    response_timeout_seconds=60,
    timeout_policy="ALERT_ONLY",
    description="Quick task that only alerts on timeout",
)
@worker_task(task_definition_name="quick_check")
def quick_check(task):
    check_id = task.input_data.get("check_id")

    print(f"Performing quick check: {check_id}")

    return {"status": "checked", "check_id": check_id, "result": "pass"}


def main():
    config = Configuration()
    config.apply_logging_config()

    print("Starting workers with task options...")
    print("\nConfigured tasks:")
    print("1. process_payment - EXPONENTIAL_BACKOFF retry with 3 attempts")
    print(
        "2. send_notification - LINEAR_BACKOFF retry with rate limiting (100 req/min)"
    )
    print("3. validate_data - FIXED retry with 2 attempts")
    print("4. heavy_computation - EXPONENTIAL_BACKOFF with high concurrency limit")
    print("5. quick_check - Alert only on timeout\n")

    with TaskHandler(
        workers=[],
        configuration=config,
        scan_for_annotated_workers=True,
        import_modules=[],
    ) as task_handler:
        task_handler.start_processes()
        task_handler.join_processes()


if __name__ == "__main__":
    main()
