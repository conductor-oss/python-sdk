"""
Workflow Operations Example
============================

Demonstrates various workflow lifecycle operations and control mechanisms.

What it does:
-------------
- Start workflow: Create and execute a new workflow instance
- Pause workflow: Temporarily halt workflow execution
- Resume workflow: Continue paused workflow
- Terminate workflow: Force stop a running workflow
- Restart workflow: Restart from a specific task
- Rerun workflow: Re-execute from beginning with same/different inputs
- Update task: Manually update task status and output
- Signal workflow: Send external signals to waiting workflows

Use Cases:
----------
- Workflow lifecycle management (start, pause, resume, terminate)
- Manual intervention in workflow execution
- Debugging and testing workflows
- Implementing human-in-the-loop patterns
- External event handling via signals
- Recovery from failures (restart, rerun)

Key Operations:
---------------
- start_workflow(): Launch new workflow instance
- pause_workflow(): Halt at current task
- resume_workflow(): Continue from pause
- terminate_workflow(): Force stop with reason
- restart_workflow(): Resume from failed task
- rerun_workflow(): Start fresh with new/same inputs
- update_task(): Manually complete tasks
- complete_signal(): Send signal to waiting task

Key Concepts:
-------------
- WorkflowClient: API for workflow operations
- Workflow signals: External event triggers
- Manual task completion: Override task execution
- Correlation IDs: Track related workflow instances
- Idempotency: Prevent duplicate workflow starts
"""
import time
import uuid

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest, RerunWorkflowRequest, TaskResult
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.http_task import HttpTask
from conductor.client.workflow.task.wait_task import WaitTask


def start_workflow(workflow_executor: WorkflowExecutor) -> str:
    workflow = ConductorWorkflow(name='workflow_signals_demo', version=1, executor=workflow_executor)
    wait_for_two_sec = WaitTask(task_ref_name='wait_for_2_sec', wait_for_seconds=2)
    http_call = HttpTask(task_ref_name='call_remote_api', http_input={
        'uri': 'https://orkes-api-tester.orkesconductor.com/api'
    })
    wait_for_signal = WaitTask(task_ref_name='wait_for_signal')

    workflow >> wait_for_two_sec >> wait_for_signal >> http_call
    return workflow.start_workflow(StartWorkflowRequest(input={}, correlation_id='correlation_123'))


def main():
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    workflow_client = clients.get_workflow_client()
    task_client = clients.get_task_client()

    workflow_id = start_workflow(clients.get_workflow_executor())
    print(f'started workflow with id {workflow_id}')
    print(f'You can monitor the workflow in the UI here: {api_config.ui_host}/execution/{workflow_id}')

    # Get the workflow execution status
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    last_task = workflow.tasks[len(workflow.tasks) - 1]
    print(f'workflow status is {workflow.status} and currently running task is {last_task.reference_task_name}')

    # Let's wait for 2+ seconds for the wait task to complete
    time.sleep(3)
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    last_task = workflow.tasks[len(workflow.tasks) - 1]
    # we shoudl see wait_for_signal is the last task now since the wait_for_2_sec should have completed by now
    print(f'workflow status is {workflow.status} and currently running task is {last_task.reference_task_name}')

    # Let's terminate this workflow
    workflow_client.terminate_workflow(workflow_id=workflow_id, reason='testing termination')
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    last_task = workflow.tasks[len(workflow.tasks) - 1]
    print(f'workflow status is {workflow.status} and status of last task {last_task.status}')

    # we can retry the workflow
    workflow_client.retry_workflow(workflow_id=workflow_id)
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    last_task = workflow.tasks[len(workflow.tasks) - 1]
    print(
        f'workflow status is {workflow.status} and status of last task {last_task.reference_task_name} is {last_task.status}')

    # Mark the WAIT task as completed by calling Task completion API
    task_result = TaskResult(workflow_instance_id=workflow_id, task_id=last_task.task_id, status='COMPLETED',
                             output_data={'greetings': 'hello from Orkes'})
    task_client.update_task(task_result)
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    last_task = workflow.tasks[len(workflow.tasks) - 1]
    print(
        f'workflow status is {workflow.status} and status of last task {last_task.reference_task_name} is {last_task.status}')
    time.sleep(2)

    rerun_request = RerunWorkflowRequest()
    rerun_request.re_run_from_task_id = workflow.tasks[1].task_id
    workflow_client.rerun_workflow(workflow_id=workflow_id, rerun_workflow_request=rerun_request)

    # Let's restart the workflow
    workflow_client.terminate_workflow(workflow_id=workflow_id, reason='terminating so we can do a restart')
    workflow_client.restart_workflow(workflow_id=workflow_id)

    # Let's pause the workflow
    workflow_client.pause_workflow(workflow_id=workflow_id)
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    print(f'workflow status is {workflow.status}')

    # let's sleep for 3 second and check the status
    time.sleep(3)
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    # wait task should have completed
    wait_task = workflow.tasks[0]
    print(f'workflow status is {workflow.status} and wait task is {wait_task.status}')
    # because workflow is paused, no further task should have been scheduled, making WAIT the last task
    # expecting only 1 task
    print(f'no. of tasks in workflow are {len(workflow.tasks)}')

    # let's resume the workflow now
    workflow_client.resume_workflow(workflow_id=workflow_id)
    workflow = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    # There should be 2 tasks
    print(
        f'no. of tasks in workflow are {len(workflow.tasks)} and last task is {workflow.tasks[len(workflow.tasks) - 1].reference_task_name}')

    search_results = workflow_client.search(start=0, size=100, free_text='*',
                                            query='correlationId = "correlation_123" ')

    print(f'found {len(search_results.results)} execution  with correlation_id  '
          f'"correlation_123" ')

    correlation_id = str(uuid.uuid4())
    search_results = workflow_client.search(start=0, size=100, free_text='*',
                                            query=f' status IN (RUNNING) AND correlationId = "{correlation_id}" ')
    # shouldn't find anything!
    print(f'found {len(search_results.results)} workflows with correlation id {correlation_id}')

    # Terminate the workflow
    workflow_client.terminate_workflow(workflow_id=workflow_id, reason='terminating for testing')




if __name__ == '__main__':
    main()
