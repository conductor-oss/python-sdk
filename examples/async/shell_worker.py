import subprocess
import asyncio

from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow


@worker_task(task_definition_name='get_system_info')
def get_system_info() -> str:
    system_info = subprocess.run(['uname', '-a'], stdout=subprocess.PIPE, text=True)
    return system_info.stdout


async def create_shell_workflow(workflow_executor) -> AsyncConductorWorkflow:
    workflow = AsyncConductorWorkflow(
        name='async_shell_operations', 
        version=1, 
        executor=workflow_executor
    )
    
    system_info_task = get_system_info(task_ref_name='get_system_info')
    
    
    workflow >> system_info_task
    
    workflow.output_parameters(output_parameters={
        'system_info': system_info_task.output('result'),
    })
    
    return workflow


async def main():
    # Configuration - defaults to reading from environment variables:
    # CONDUCTOR_SERVER_URL : conductor server e.g. https://play.orkes.io/api
    # CONDUCTOR_AUTH_KEY : API Authentication Key
    # CONDUCTOR_AUTH_SECRET: API Auth Secret
    api_config = Configuration()
    
    print("Starting async shell worker...")
    task_handler = TaskHandler(
        configuration=api_config,
        scan_for_annotated_workers=True
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
        print(f"Execution URL: {api_config.ui_host}/execution/{workflow_run.workflow_id}")
        
        # Display workflow output
        if workflow_run.output:
            print(f"\nWorkflow Output:")
            print(f"System Info: {workflow_run.output.get('system_info', 'N/A')}")

        task_handler.stop_processes()


if __name__ == '__main__':
    asyncio.run(main())
