import asyncio

from conductor.asyncio_client.adapters.models import (
    ExtendedWorkflowDef,
    StartWorkflowRequest,
    StateChangeEvent,
    Task,
    TaskDef,
    TaskResult,
    WorkflowTask,
)
from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.shared.http.enums import TaskResultStatus


@worker_task(task_definition_name="audit_log")
def audit_log(workflow_input: object, status: str, name: str):
    print(f"task {name} is in {status} status, with workflow input as {workflow_input}")


@worker_task(task_definition_name="simple_task_1")
def simple_task_1(task: Task) -> str:
    return "OK"


@worker_task(task_definition_name="simple_task_2")
def simple_task_2(task: Task) -> TaskResult:
    return TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
        worker_id=task.worker_id,
        status=TaskResultStatus.FAILED_WITH_TERMINAL_ERROR,
    )


async def main():
    api_config = Configuration()

    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()

    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(configuration=api_config, api_client=api_client)
        metadata_client = clients.get_metadata_client()
        workflow_client = clients.get_workflow_client()

        task1 = WorkflowTask(
            type="SIMPLE",
            name="simple_task_1",
            task_reference_name="simple_task_1_ref",
            on_state_change={
                "onStart": [
                    StateChangeEvent(
                        type="audit_log",
                        payload={
                            "workflow_input": "${workflow.input}",
                            "status": "${simple_task_1_ref.status}",
                            "name": "simple_task_1_ref",
                        },
                    )
                ]
            },
        )

        task_def = TaskDef(
            name="simple_task_2",
            retry_count=0,
            timeout_seconds=600,
            total_timeout_seconds=600,
        )
        task2 = WorkflowTask(
            type="SIMPLE",
            name="simple_task_2",
            task_reference_name="simple_task_2_ref",
            task_definition=task_def,
            on_state_change={
                "onScheduled": [
                    StateChangeEvent(
                        type="audit_log",
                        payload={
                            "workflow_input": "${workflow.input}",
                            "status": "${simple_task_2_ref.status}",
                            "name": "simple_task_2_ref",
                        },
                    )
                ],
                "onStart": [
                    StateChangeEvent(
                        type="audit_log",
                        payload={
                            "workflow_input": "${workflow.input}",
                            "status": "${simple_task_2_ref.status}",
                            "name": "simple_task_2_ref",
                        },
                    )
                ],
                "onFailed": [
                    StateChangeEvent(
                        type="audit_log",
                        payload={
                            "workflow_input": "${workflow.input}",
                            "status": "${simple_task_2_ref.status}",
                            "name": "simple_task_2_ref",
                        },
                    )
                ],
            },
        )

        workflow = ExtendedWorkflowDef(
            name="test_audit_logs",
            version=1,
            timeoutSeconds=600,
            tasks=[
                task1,
                task2,
            ],
        )

        await metadata_client.register_workflow_def(
            extended_workflow_def=workflow, overwrite=True
        )
        request = StartWorkflowRequest(
            name=workflow.name,
            version=workflow.version,
            input={"a": "aa", "b": "bb", "c": 42},
        )

        workflow_id = await workflow_client.start_workflow(
            start_workflow_request=request
        )
        print(f"workflow_id {workflow_id}")

    task_handler.join_processes()


if __name__ == "__main__":
    asyncio.run(main())
