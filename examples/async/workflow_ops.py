import asyncio
import uuid

from conductor.asyncio_client.adapters.models import (
    ExtendedTaskDef,
    RerunWorkflowRequest,
    StartWorkflowRequest,
    TaskResult,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.executor.workflow_executor import (
    AsyncWorkflowExecutor,
)
from conductor.asyncio_client.workflow.task.http_task import HttpTask
from conductor.asyncio_client.workflow.task.simple_task import SimpleTask
from conductor.asyncio_client.workflow.task.wait_task import WaitTask


async def register_retryable_task(metadata_client: OrkesMetadataClient) -> None:
    """Register a task definition with retry configuration"""
    task_def = ExtendedTaskDef(
        name="retryable_task",
        retry_count=3,
        retry_logic="LINEAR_BACKOFF",
        retry_delay_seconds=1,
        timeoutSeconds=3600,
        totalTimeoutSeconds=3600,
        pollTimeoutSeconds=60,
        concurrentExecLimit=3,
    )

    await metadata_client.register_task_def(task_def)
    print(f"Registered retryable task definition: {task_def.name}")


async def start_workflow(workflow_executor: AsyncWorkflowExecutor) -> str:
    workflow = AsyncConductorWorkflow(
        name="workflow_signals_demo", version=1, executor=workflow_executor
    )
    wait_for_two_sec = WaitTask(task_ref_name="wait_for_2_sec", wait_for_seconds=2)
    http_call = HttpTask(
        task_ref_name="call_remote_api",
        http_input={"uri": "https://orkes-api-tester.orkesconductor.com/api"},
    )
    wait_for_signal = WaitTask(task_ref_name="wait_for_signal")

    # Add a retryable task
    retryable_task = SimpleTask(
        task_def_name="retryable_task", task_reference_name="retryable_task_ref"
    )

    workflow >> wait_for_two_sec >> retryable_task >> wait_for_signal >> http_call
    return await workflow.start_workflow(
        StartWorkflowRequest(
            name="workflow_signals_demo",
            version=1,
            input={},
            correlation_id="correlation_123",
        )
    )


async def main():
    api_config = Configuration()

    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(api_client=api_client, configuration=api_config)
        workflow_client = clients.get_workflow_client()
        task_client = clients.get_task_client()
        metadata_client = clients.get_metadata_client()

        # Register the retryable task definition
        await register_retryable_task(metadata_client)

        workflow_id = await start_workflow(clients.get_workflow_executor())
        print(f"started workflow with id {workflow_id}")
        print(
            f"You can monitor the workflow in the UI here: {api_config.ui_host}/execution/{workflow_id}"
        )

        # Get the workflow execution status
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        last_task = workflow.tasks[len(workflow.tasks) - 1]
        print(
            f"workflow status is {workflow.status} and currently running task is {last_task.reference_task_name}"
        )

        # Let's wait for 2+ seconds for the wait task to complete
        await asyncio.sleep(3)
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        last_task = workflow.tasks[len(workflow.tasks) - 1]
        # we shoudl see retryable_task is the last task now since the wait_for_2_sec should have completed by now
        print(
            f"workflow status is {workflow.status} and currently running task is {last_task.reference_task_name}"
        )

        # Let's terminate this workflow
        await workflow_client.terminate_workflow(
            workflow_id=workflow_id, reason="testing termination"
        )
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        last_task = workflow.tasks[len(workflow.tasks) - 1]
        print(
            f"workflow status is {workflow.status} and status of last task {last_task.status}"
        )

        # we can retry the workflow
        await workflow_client.retry_workflow(workflow_id=workflow_id)
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        last_task = workflow.tasks[len(workflow.tasks) - 1]
        print(
            f"workflow status is {workflow.status} and status of last task {last_task.reference_task_name} is {last_task.status}"
        )

        # Mark the WAIT task as completed by calling Task completion API
        task_result = TaskResult(
            workflow_instance_id=workflow_id,
            task_id=last_task.task_id,
            status="COMPLETED",
            output_data={"greetings": "hello from Orkes"},
        )
        await task_client.update_task(task_result)
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        last_task = workflow.tasks[len(workflow.tasks) - 1]
        print(
            f"workflow status is {workflow.status} and status of last task {last_task.reference_task_name} is {last_task.status}"
        )
        await asyncio.sleep(2)

        rerun_request = RerunWorkflowRequest()
        rerun_request.re_run_from_task_id = workflow.tasks[1].task_id
        await workflow_client.rerun_workflow(
            workflow_id=workflow_id, rerun_workflow_request=rerun_request
        )

        # Let's restart the workflow
        await workflow_client.terminate_workflow(
            workflow_id=workflow_id, reason="terminating so we can do a restart"
        )
        await workflow_client.restart_workflow(workflow_id=workflow_id)

        # Let's pause the workflow
        await workflow_client.pause_workflow(workflow_id=workflow_id)
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        print(f"workflow status is {workflow.status}")

        # let's sleep for 3 second and check the status
        await asyncio.sleep(3)
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        # wait task should have completed
        wait_task = workflow.tasks[0]
        print(
            f"workflow status is {workflow.status} and wait task is {wait_task.status}"
        )
        # because workflow is paused, no further task should have been scheduled, making WAIT the last task
        # expecting only 1 task
        print(f"no. of tasks in workflow are {len(workflow.tasks)}")

        # let's resume the workflow now
        await workflow_client.resume_workflow(workflow_id=workflow_id)
        workflow = await workflow_client.get_workflow(
            workflow_id=workflow_id, include_tasks=True
        )
        # There should be 2 tasks
        print(
            f"no. of tasks in workflow are {len(workflow.tasks)} and last task is {workflow.tasks[len(workflow.tasks) - 1].reference_task_name}"
        )

        search_results = await workflow_client.search(
            start=0, size=100, free_text="*", query='correlationId = "correlation_123"'
        )

        print(
            f"found {len(search_results.results)} execution  with correlation_id  "
            f'"correlation_123" '
        )

        correlation_id = str(uuid.uuid4())
        search_results = await workflow_client.search(
            start=0,
            size=100,
            free_text="*",
            query=f'status IN (RUNNING) AND correlationId = "{correlation_id}"',
        )
        # shouldn't find anything!
        print(
            f"found {len(search_results.results)} workflows with correlation id {correlation_id}"
        )

        # Terminate the workflow
        await workflow_client.terminate_workflow(
            workflow_id=workflow_id, reason="terminating for testing"
        )


if __name__ == "__main__":
    asyncio.run(main())
