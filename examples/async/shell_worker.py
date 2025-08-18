import asyncio
from typing import Dict

from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.shared.worker.exception import NonRetryableException


@worker_task(task_definition_name="file_operation")
def file_operation(
    operation: str, source: str, destination: str = None
) -> Dict[str, str]:
    try:
        import os
        import shutil

        if operation == "copy":
            if not destination:
                raise NonRetryableException("Destination required for copy operation")
            shutil.copy2(source, destination)
            result = f"Copied {source} to {destination}"

        elif operation == "move":
            if not destination:
                raise NonRetryableException("Destination required for move operation")
            shutil.move(source, destination)
            result = f"Moved {source} to {destination}"

        elif operation == "delete":
            if os.path.isfile(source):
                os.remove(source)
            elif os.path.isdir(source):
                shutil.rmtree(source)
            else:
                raise NonRetryableException(f"Path does not exist: {source}")
            result = f"Deleted {source}"

        elif operation == "mkdir":
            os.makedirs(source, exist_ok=True)
            result = f"Created directory {source}"

        elif operation == "exists":
            result = f"Path {source} exists: {os.path.exists(source)}"

        else:
            raise NonRetryableException(f"Unsupported operation: {operation}")

        return {
            "operation": operation,
            "source": source,
            "destination": destination,
            "result": result,
            "success": True,
        }

    except Exception as e:
        raise NonRetryableException(f"File operation failed: {str(e)}")


async def create_shell_workflow(workflow_executor) -> AsyncConductorWorkflow:
    workflow = AsyncConductorWorkflow(
        name="async_shell_operations", version=1, executor=workflow_executor
    )

    create_dir = file_operation(
        task_ref_name="create_temp_dir", operation="mkdir", source="./temp_workflow_dir"
    )

    cleanup = file_operation(
        task_ref_name="cleanup_temp_dir",
        operation="delete",
        source="./temp_workflow_dir",
    )

    workflow >> create_dir >> cleanup

    return workflow


async def main():
    # Configuration - defaults to reading from environment variables:
    # CONDUCTOR_SERVER_URL : conductor server e.g. https://play.orkes.io/api
    # CONDUCTOR_AUTH_KEY : API Authentication Key
    # CONDUCTOR_AUTH_SECRET: API Auth Secret
    api_config = Configuration()

    print("Starting async shell worker...")
    task_handler = TaskHandler(
        configuration=api_config, scan_for_annotated_workers=True
    )
    task_handler.start_processes()

    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(api_client=api_client, configuration=api_config)
        workflow_executor = clients.get_workflow_executor()

        print("Creating shell workflow...")
        workflow = await create_shell_workflow(workflow_executor)

        print("Registering shell workflow...")
        await workflow.register(True)

        print("Executing shell workflow...")
        workflow_run = await workflow.execute(workflow_input={})

        print(f"Workflow ID: {workflow_run.workflow_id}")
        print(f"Status: {workflow_run.status}")
        print(
            f"Execution URL: {api_config.ui_host}/execution/{workflow_run.workflow_id}"
        )

        task_handler.stop_processes()


if __name__ == "__main__":
    asyncio.run(main())
