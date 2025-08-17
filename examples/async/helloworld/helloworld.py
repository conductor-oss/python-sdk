import asyncio

from greetings_workflow import greetings_workflow

from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.executor.workflow_executor import (
    AsyncWorkflowExecutor,
)


async def register_workflow(
    workflow_executor: AsyncWorkflowExecutor,
) -> AsyncConductorWorkflow:
    workflow = greetings_workflow(workflow_executor=workflow_executor)
    await workflow.register(True)
    return workflow


async def main():
    # points to http://localhost:8080/api by default
    api_config = Configuration()
    async with ApiClient(api_config._http_config) as api_client:
        workflow_executor = AsyncWorkflowExecutor(
            configuration=api_config, api_client=api_client
        )
        # Needs to be done only when registering a workflow one-time
        workflow = await register_workflow(workflow_executor)

        task_handler = TaskHandler(configuration=api_config)
        task_handler.start_processes()

        workflow_run = await workflow_executor.execute(
            name=workflow.name,
            version=workflow.version,
            workflow_input={"name": "World"},
        )

    print(f'\nworkflow result: {workflow_run.output}\n')
    print(
        f"see the workflow execution here: {api_config.ui_host}/execution/{workflow_run.workflow_id}\n"
    )

    task_handler.stop_processes()


if __name__ == "__main__":
    asyncio.run(main())
