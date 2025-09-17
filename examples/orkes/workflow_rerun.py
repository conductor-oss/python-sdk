import json

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest, RerunWorkflowRequest, TaskResult, WorkflowRun, \
    WorkflowDef
from conductor.shared.http.enums import TaskResultStatus
from conductor.client.http.models.workflow_def import to_workflow_def
from conductor.client.http.models.workflow_state_update import WorkflowStateUpdate
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow_client import WorkflowClient


def read_and_register_workflow(clients: OrkesClients) -> None:
    file = open('re_run_workflow.json')
    json_data = json.load(file)
    workflow = to_workflow_def(json_data=json_data)
    print(f'loaded workflow {workflow}')
    clients.get_metadata_client().update_workflow_def(workflow, overwrite=True)

def start_workflow(workflow_client: WorkflowClient) -> WorkflowRun:
    request = StartWorkflowRequest()
    request.name = 'rerun_test'
    request.version = 1
    request.input = {
        'case': 'case1'
    }
    return workflow_client.execute_workflow(start_workflow_request=request,
                                            wait_until_task_ref='simple_task_ref1_case1_1')


def main():
    api_config = Configuration()
    api_config.apply_logging_config()
    clients = OrkesClients(configuration=api_config)
    workflow_client = clients.get_workflow_client()

    # Let's load up the workflow definition from a file and register
    read_and_register_workflow(clients)

    workflow_run = start_workflow(workflow_client)
    workflow_id = workflow_run.workflow_id
    print(f'started workflow with id {workflow_id}')
    print(f'You can monitor the workflow in the UI here: {api_config.ui_host}/execution/{workflow_id}')

    update_request = WorkflowStateUpdate()
    update_request.task_reference_name = 'simple_task_ref1_case1_1'
    update_request.task_result = TaskResult()
    update_request.task_result.status = TaskResultStatus.COMPLETED
    workflow_client.update_state(workflow_id=workflow_id, update_requesst=update_request,
                                 wait_until_task_ref_names='simple_task_ref1_case1_2', wait_for_seconds=0)

    update_request.task_reference_name = 'simple_task_ref1_case1_2'
    workflow_run = workflow_client.update_state(workflow_id=workflow_id, update_requesst=update_request,
                                                wait_until_task_ref_names='simple_task_ref2_case1_1',
                                                wait_for_seconds=0)

    task = workflow_run.get_task(task_reference_name='simple_task_ref1_case1_2')
    rerun_request = RerunWorkflowRequest()
    rerun_request.re_run_from_task_id = task.task_id
    workflow_client.rerun_workflow(workflow_id=workflow_id, rerun_workflow_request=rerun_request)


if __name__ == '__main__':
    main()
