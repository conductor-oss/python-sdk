from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import WorkflowDef, WorkflowTask, Task, StartWorkflowRequest, TaskDef, TaskResult
from conductor.client.http.models.state_change_event import StateChangeEventAdapter as StateChangeEvent, StateChangeEventType, StateChangeConfig
from conductor.shared.http.enums import TaskResultStatus
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task


@worker_task(task_definition_name='audit_log')
def audit_log(workflow_input: object, status: str, name: str):
    print(f'task {name} is in {status} status, with workflow input as {workflow_input}')


@worker_task(task_definition_name='simple_task_1')
def simple_task_1(task: Task) -> str:
    return 'OK'


@worker_task(task_definition_name='simple_task_2')
def simple_task_2(task: Task) -> TaskResult:
    return task.to_task_result(status=TaskResultStatus.FAILED_WITH_TERMINAL_ERROR)


def main():
    api_config = Configuration()
    clients = OrkesClients()
    metadata_client = clients.get_metadata_client()
    workflow_client = clients.get_workflow_client()

    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()

    workflow = WorkflowDef()
    workflow.name = 'test_audit_logs'
    workflow.version = 1

    task1 = WorkflowTask()
    task1.type = 'SIMPLE'
    task1.name = 'simple_task_1'
    task1.task_reference_name = 'simple_task_1_ref'
    task1.on_state_change = StateChangeConfig(event_type=StateChangeEventType.onStart,
                                              events=[
                                                  StateChangeEvent(type='audit_log',
                                                                   payload={
                                                                       'workflow_input': '${workflow.input}',
                                                                       'status': '${simple_task_1_ref.status}',
                                                                       'name': 'simple_task_1_ref'
                                                                   })
                                              ])

    task_def = TaskDef()
    task_def.name = 'simple_task_2'
    task_def.retry_count = 0
    task2 = WorkflowTask()
    task2.type = 'SIMPLE'
    task2.name = 'simple_task_2'
    task2.task_reference_name = 'simple_task_2_ref'
    task2.task_definition = task_def

    task2.on_state_change = StateChangeConfig(event_type=[StateChangeEventType.onScheduled,
                                                          StateChangeEventType.onStart,
                                                          StateChangeEventType.onFailed],
                                              events=[
                                                  StateChangeEvent(type='audit_log',
                                                                   payload={
                                                                       'workflow_input': '${workflow.input}',
                                                                       'status': '${simple_task_2_ref.status}',
                                                                       'name': 'simple_task_2_ref'
                                                                   })
                                              ])

    workflow.tasks.append(task1)
    workflow.tasks.append(task2)

    metadata_client.register_workflow_def(workflow_def=workflow, overwrite=True)
    request = StartWorkflowRequest()
    request.name = workflow.name
    request.version = workflow.version
    request.input = {
        'a': 'aa',
        'b': 'bb',
        'c': 42
    }
    workflow_id = workflow_client.start_workflow(start_workflow_request=request)
    print(f'workflow_id {workflow_id}')

    task_handler.join_processes()


if __name__ == '__main__':
    main()
