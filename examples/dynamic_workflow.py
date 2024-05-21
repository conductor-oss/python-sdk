"""
This is a dynamic workflow that can be created and executed at run time.
dynamic_workflow will run worker tasks get_user_email and send_email in the same order.
For use cases in which the workflow cannot be defined statically, dynamic workflows is a useful approach.
For detailed explanation, https://github.com/conductor-sdk/conductor-python/blob/main/workflows.md
"""
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.start_workflow_request import IdempotencyStrategy
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow


@worker_task(task_definition_name='get_user_email')
def get_user_email(userid: str) -> str:
    return f'{userid}@example.com'


@worker_task(task_definition_name='send_email')
def send_email(email: str, subject: str, body: str):
    print(f'sending email to {email} with subject {subject} and body {body}')


def main():
    # defaults to reading the configuration using following env variables
    # CONDUCTOR_SERVER_URL : conductor server e.g. https://play.orkes.io/api
    # CONDUCTOR_AUTH_KEY : API Authentication Key
    # CONDUCTOR_AUTH_SECRET: API Auth Secret
    api_config = Configuration()

    task_handler = TaskHandler(configuration=api_config)
    task_handler.start_processes()

    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow = ConductorWorkflow(name='dynamic_workflow', version=1, executor=workflow_executor)
    get_email = get_user_email(task_ref_name='get_user_email_ref', userid=workflow.input('userid'))
    sendmail = send_email(task_ref_name='send_email_ref', email=get_email.output('result'), subject='Hello from Orkes',
                          body='Test Email')
    workflow >> get_email >> sendmail

    # Configure the output of the workflow
    workflow.output_parameters(output_parameters={
        'email': get_email.output('result')
    })

    workflow_run = workflow.execute(workflow_input={'userid': 'user_a'})
    print(f'\nworkflow output:  {workflow_run.output}\n')
    print(f'check the workflow execution here: {api_config.ui_host}/execution/{workflow_run.workflow_id}')
    task_handler.stop_processes()


if __name__ == '__main__':
    main()
