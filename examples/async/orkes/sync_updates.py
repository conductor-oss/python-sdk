import asyncio

from conductor.asyncio_client.adapters.models import (TaskResult,
                                                      WorkflowStateUpdate)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.workflow.conductor_workflow import \
    AsyncConductorWorkflow
from conductor.asyncio_client.workflow.task.http_task import (HttpInput,
                                                              HttpTask)
from conductor.asyncio_client.workflow.task.switch_task import SwitchTask
from conductor.asyncio_client.workflow.task.wait_task import WaitTask
from conductor.shared.http.enums import TaskResultStatus


def create_workflow(clients: OrkesClients) -> AsyncConductorWorkflow:
    workflow = AsyncConductorWorkflow(
        executor=clients.get_workflow_executor(),
        name="sync_task_variable_updates",
        version=1,
    )
    http = HttpTask(
        task_ref_name="http_ref",
        http_input=HttpInput(uri="https://orkes-api-tester.orkesconductor.com/api"),
    )
    wait = WaitTask(task_ref_name="wait_task_ref")
    wait_case_1 = WaitTask(task_ref_name="wait_task_ref_1")
    wait_case_2 = WaitTask(task_ref_name="wait_task_ref_2")

    switch = SwitchTask(
        task_ref_name="switch_ref", case_expression="${workflow.variables.case}"
    )
    switch.switch_case("case1", [wait_case_1])
    switch.switch_case("case2", [wait_case_2])

    workflow >> http >> wait >> switch

    return workflow


async def main():
    api_config = Configuration()
    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(configuration=api_config, api_client=api_client)
        workflow_client = clients.get_workflow_client()

        workflow = create_workflow(clients)

        workflow_run = await workflow.execute(
            workflow_input={}, wait_for_seconds=10, wait_until_task_ref="wait_task_ref"
        )
        print(f"started {workflow_run.workflow_id}")
        print(
            f"see the execution at {api_config.ui_host}/execution/{workflow_run.workflow_id}"
        )

        task_result = TaskResult(
            status=TaskResultStatus.COMPLETED,
            workflow_instance_id=workflow_run.workflow_id,
            task_id=workflow_run.tasks[1].task_id,
        )

        state_update = WorkflowStateUpdate(
            task_reference_name="wait_task_ref",
            task_result=task_result,
            variables={"case": "case1"},
        )

        workflow_run = await workflow_client.update_state(
            workflow_id=workflow_run.workflow_id, update_request=state_update
        )
        last_task_ref = workflow_run.tasks[
            len(workflow_run.tasks) - 1
        ].reference_task_name
        print(f"workflow: {workflow_run.status}, last task = {last_task_ref}")

        state_update.task_reference_name = last_task_ref
        workflow_run = await workflow_client.update_state(
            workflow_id=workflow_run.workflow_id, update_request=state_update
        )
        print(f"workflow: {workflow_run.status}, last task = {last_task_ref}")


if __name__ == "__main__":
    asyncio.run(main())
