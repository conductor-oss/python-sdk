import asyncio
import uuid

from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.task.http_poll_task import HttpPollTask
from conductor.shared.workflow.models import HttpPollInput


async def main():
    configuration = Configuration()
    async with ApiClient(configuration) as api_client:
        workflow_executor = OrkesClients(api_client).get_workflow_executor()
        workflow = AsyncConductorWorkflow(
            executor=workflow_executor, name="http_poll_example_" + str(uuid.uuid4())
        )
        http_poll = HttpPollTask(
            task_ref_name="http_poll_ref",
            http_input=HttpPollInput(
                uri="https://orkes-api-tester.orkesconductor.com/api",
                polling_strategy="EXPONENTIAL_BACKOFF",
                polling_interval=5,
                termination_condition="(function(){ return $.output.response.body.randomInt < 5000;})();",
            ),
        )
        workflow >> http_poll

        # execute the workflow to get the results
        result = await workflow.execute(workflow_input={}, wait_for_seconds=10)
    print(f"Started workflow with id {result.workflow_id}")
    print(
        f"See the workflow execution: {configuration.ui_host}/execution/{result.workflow_id}\n"
    )


if __name__ == "__main__":
    asyncio.run(main())
