"""
Task Configuration Example
===========================

Demonstrates how to programmatically create and configure task definitions.

What it does:
-------------
- Creates a TaskDef with retry configuration (3 retries with linear backoff)
- Sets concurrency limits (max 3 concurrent executions)
- Configures various timeout settings (poll, execution, response)
- Sets rate limits (100 executions per 10-second window)
- Registers the task definition with Conductor server

Use Cases:
----------
- Programmatically managing task definitions (Infrastructure as Code)
- Setting task-level retry policies
- Configuring timeout and concurrency controls
- Implementing rate limiting for external API calls
- Creating task definitions as part of deployment automation

Key Configuration Options:
--------------------------
- retry_count: Number of retry attempts on failure
- retry_logic: LINEAR_BACKOFF, EXPONENTIAL_BACKOFF, FIXED
- retry_delay_seconds: Wait time between retries
- concurrent_exec_limit: Max concurrent executions
- poll_timeout_seconds: Task fails if not polled within this time
- timeout_seconds: Total execution timeout
- response_timeout_seconds: Timeout if no status update received
- rate_limit_per_frequency: Rate limit per time window
- rate_limit_frequency_in_seconds: Time window for rate limit

Key Concepts:
-------------
- TaskDef: Python object representing task metadata
- MetadataClient: API client for managing task definitions
- Configuration: Server connection settings
- Rate Limiting: Control task execution frequency
"""
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import TaskDef
from conductor.client.orkes_clients import OrkesClients


def main():
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    metadata_client = clients.get_metadata_client()

    task_def = TaskDef()
    task_def.name = 'task_with_retries'
    task_def.retry_count = 3
    task_def.retry_logic = 'LINEAR_BACKOFF'
    task_def.retry_delay_seconds = 1

    # only allow 3 tasks at a time to be in the IN_PROGRESS status
    task_def.concurrent_exec_limit = 3

    # timeout the task if not polled within 60 seconds of scheduling
    task_def.poll_timeout_seconds = 60

    # timeout the task if the task does not COMPLETE in 2 minutes
    task_def.timeout_seconds = 120

    # for the long running tasks, timeout if the task does not get updated in COMPLETED or IN_PROGRESS status in
    # 60 seconds after the last update
    task_def.response_timeout_seconds = 60

    # only allow 100 executions in a 10-second window! -- Note, this is complementary to concurrent_exec_limit
    task_def.rate_limit_per_frequency = 100
    task_def.rate_limit_frequency_in_seconds = 10

    metadata_client.register_task_def(task_def=task_def)

    print(f'registered the task -- see the details {api_config.ui_host}/taskDef/{task_def.name}')


if __name__ == '__main__':
    main()
