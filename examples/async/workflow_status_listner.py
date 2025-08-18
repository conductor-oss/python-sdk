import asyncio
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.task.http_task import HttpTask


async def main():
    api_config = Configuration()
    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(api_client=api_client, configuration=api_config)

        workflow = AsyncConductorWorkflow(name='workflow_status_listener_demo', version=1,
                                    executor=clients.get_workflow_executor())
        workflow >> HttpTask(task_ref_name='http_ref', http_input={
            'uri': 'https://orkes-api-tester.orkesconductor.com/api'
        })
        workflow.enable_status_listener('kafka:abcd')
        await workflow.register(overwrite=True)
        print(f'Registered {workflow.name}')


if __name__ == '__main__':
    asyncio.run(main())
