from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest, TaskResult
from conductor.shared.http.enums import TaskResultStatus
from conductor.client.http.models.workflow_state_update import WorkflowStateUpdate
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.http_task import HttpTask, HttpInput
from conductor.client.workflow.task.switch_task import SwitchTask
from conductor.client.workflow.task.wait_task import WaitTask


def create_workflow(clients: OrkesClients) -> ConductorWorkflow:
    workflow = ConductorWorkflow(executor=clients.get_workflow_executor(), name='sync_task_variable_updates', version=1)
    http = HttpTask(task_ref_name='http_ref',
                         http_input=HttpInput(uri='https://orkes-api-tester.orkesconductor.com/api'))
    wait = WaitTask(task_ref_name='wait_task_ref')
    wait_case_1 = WaitTask(task_ref_name='wait_task_ref_1')
    wait_case_2 = WaitTask(task_ref_name='wait_task_ref_2')

    switch = SwitchTask(task_ref_name='switch_ref', case_expression='${workflow.variables.case}')
    switch.switch_case('case1', [wait_case_1])
    switch.switch_case('case2', [wait_case_2])

    workflow >> http >> wait >> switch

    return workflow

def main():
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    workflow_client = clients.get_workflow_client()

    workflow = create_workflow(clients)

    request = StartWorkflowRequest()
    request.name = 'sync_task_variable_updates'
    request.version = 1
    workflow_run = workflow.execute(workflow_input={}, wait_for_seconds=10,
                                                    wait_until_task_ref='wait_task_ref')
    print(f'started {workflow_run.workflow_id}')
    print(f'see the execution at {api_config.ui_host}/execution/{workflow_run.workflow_id}')

    task_result = TaskResult()
    task_result.status = TaskResultStatus.COMPLETED

    state_update = WorkflowStateUpdate()
    state_update.task_reference_name = 'wait_task_ref'
    state_update.task_result = task_result
    state_update.variables = {
        'case': 'case1'
    }

    workflow_run = workflow_client.update_state(workflow_id=workflow_run.workflow_id, update_requesst=state_update,
                                                wait_for_seconds=1,
                                                wait_until_task_ref_names=['wait_task_ref_1', 'wait_task_ref_2'])
    last_task_ref = workflow_run.tasks[len(workflow_run.tasks) - 1].reference_task_name
    print(f'workflow: {workflow_run.status}, last task = {last_task_ref}')

    state_update.task_reference_name = last_task_ref
    workflow_run = workflow_client.update_state(workflow_id=workflow_run.workflow_id, update_requesst=state_update,
                                                wait_for_seconds=1)
    print(f'workflow: {workflow_run.status}, last task = {last_task_ref}')


if __name__ == '__main__':
    main()
