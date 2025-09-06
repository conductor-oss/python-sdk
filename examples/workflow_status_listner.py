import time
import uuid

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest, RerunWorkflowRequest, TaskResult
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.http_task import HttpTask
from conductor.client.workflow.task.wait_task import WaitTask


def main():
    api_config = Configuration()
    api_config.apply_logging_config()
    clients = OrkesClients(configuration=api_config)

    workflow = ConductorWorkflow(name='workflow_status_listener_demo', version=1,
                                 executor=clients.get_workflow_executor())
    workflow >> HttpTask(task_ref_name='http_ref', http_input={
        'uri': 'https://orkes-api-tester.orkesconductor.com/api'
    })
    workflow.enable_status_listener('kafka:abcd')
    workflow.register(overwrite=True)
    print(f'Registered {workflow.name}')


if __name__ == '__main__':
    main()
