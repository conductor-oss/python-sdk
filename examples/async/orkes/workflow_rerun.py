import asyncio
import json
import uuid

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models import (
    ExtendedWorkflowDef,
    RerunWorkflowRequest,
    StartWorkflowRequest,
    TaskResult,
    WorkflowRun,
    WorkflowStateUpdate,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.shared.http.enums import TaskResultStatus


async def read_and_register_workflow(clients: OrkesClients) -> None:
    file = open("./examples/async/orkes/re_run_workflow.json")
    json_data = json.load(file)
    workflow = ExtendedWorkflowDef.from_json(json_str=json.dumps(json_data))
    await clients.get_metadata_client().update_workflow_def(workflow, overwrite=True)


async def start_workflow(workflow_client: OrkesWorkflowClient) -> WorkflowRun:
    request = StartWorkflowRequest(
        name="rerun_test", version=1, input={"case": "case1"}
    )
    request_id = str(uuid.uuid4())
    return await workflow_client.execute_workflow(
        start_workflow_request=request,
        request_id=request_id,
        wait_until_task_ref="simple_task_ref1_case1_1",
    )


async def main():
    api_config = Configuration()
    api_config.apply_logging_config()
    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(configuration=api_config, api_client=api_client)
        workflow_client = clients.get_workflow_client()

        await read_and_register_workflow(clients)

        workflow_run = await start_workflow(workflow_client)
        workflow_id = workflow_run.workflow_id
        print(f"started workflow with id {workflow_id}")
        print(
            f"You can monitor the workflow in the UI here: {api_config.ui_host}/execution/{workflow_id}"
        )

        update_request = WorkflowStateUpdate(
            task_reference_name="simple_task_ref1_case1_1",
            task_result=TaskResult(
                status=TaskResultStatus.COMPLETED,
                workflow_instance_id=workflow_id,
                task_id=workflow_run.tasks[2].task_id,
            ),
            variables={},
        )
        await workflow_client.update_state(
            workflow_id=workflow_id, update_request=update_request.model_dump()
        )

        update_request = WorkflowStateUpdate(
            task_reference_name="simple_task_ref1_case1_2",
            task_result=TaskResult(
                status=TaskResultStatus.COMPLETED,
                workflow_instance_id=workflow_id,
                task_id=workflow_run.tasks[1].task_id,
            ),
            variables={},
        )
        workflow_run = await workflow_client.update_state(
            workflow_id=workflow_id, update_request=update_request.model_dump()
        )

        rerun_request = RerunWorkflowRequest(
            re_run_from_task_id=workflow_run.tasks[1].task_id
        )
        await workflow_client.rerun_workflow(
            workflow_id=workflow_id, rerun_workflow_request=rerun_request
        )


if __name__ == "__main__":
    asyncio.run(main())
