import urllib3

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from greetings_workflow import greetings_workflow
import requests


def register_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    workflow = greetings_workflow(workflow_executor=workflow_executor)
    workflow.register(True)
    return workflow


@worker_task(task_definition_name='hello')
def hello(name: str) -> str:
    print(f'executing.... {name}')
    return f'Hello {name}'


def main():
    urllib3.disable_warnings()

    # points to http://localhost:8080/api by default
    api_config = Configuration()
    api_config.http_connection = requests.Session()
    api_config.http_connection.verify = False

    metadata_client = OrkesMetadataClient(api_config)
    task_client = OrkesTaskClient(api_config)
    workflow_client = OrkesWorkflowClient(api_config)

    task_handler = TaskHandler(configuration=api_config)
    task_handler.start_processes()

    # task_handler.stop_processes()


if __name__ == '__main__':
    main()
