import asyncio

from conductor.asyncio_client.adapters.models import ExtendedTaskDef
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients


async def main():
    api_config = Configuration()

    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(api_client=api_client, configuration=api_config)
        metadata_client = clients.get_metadata_client()

        task_def = ExtendedTaskDef(
            name="task_with_retries",
            retry_count=3,
            retry_logic="LINEAR_BACKOFF",
            retry_delay_seconds=1,
            timeoutSeconds=120,
            totalTimeoutSeconds=120,
        )

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

        await metadata_client.register_task_def(task_def)

        print(
            f"registered the task -- see the details {api_config.ui_host}/taskDef/{task_def.name}"
        )


if __name__ == "__main__":
    asyncio.run(main())
