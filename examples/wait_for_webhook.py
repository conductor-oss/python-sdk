from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.wait_for_webhook_task import wait_for_webhook


@worker_task(task_definition_name='get_user_email')
def get_user_email(userid: str) -> str:
    return f'{userid}@example.com'


@worker_task(task_definition_name='send_email')
def send_email(email: str, subject: str, body: str):
    print(f'sending email to {email} with subject {subject} and body {body}')


def main():
    api_config = Configuration()

    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()

    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()

    workflow = ConductorWorkflow(name='wait_for_webhook', version=1, executor=workflow_executor)
    get_email = get_user_email(task_ref_name='get_user_email_ref', userid=workflow.input('userid'))
    sendmail = send_email(task_ref_name='send_email_ref', email=get_email.output('result'), subject='Hello from Orkes',
                          body='Test Email')

    workflow >> get_email >> sendmail >> wait_for_webhook(task_ref_name="wait_ref", matches={
        "$['type']": "customer",
        "$['id']": workflow.input("userid")
    })

    # webhook workflows MUST be registered before they can be used with a webhook
    workflow.register(overwrite=True)
    print(f'done registering workflow...')

    # create a webhook in the UI by navigating to Webhook and creating one that responds to the webhook events
    # Ensure that the webhook is configured to receive events and dispatch to the workflow that is created above
    # docs
    # https://orkes.io/content/reference-docs/system-tasks/wait-for-webhook

    request = StartWorkflowRequest(input={'userid': 'user_a'})
    request.name = workflow.name
    request.version = workflow.version

    workflow_run = workflow_client.execute_workflow(start_workflow_request=request, wait_for_seconds=60)

    # execute method will wait until the webhook task is completed, use the following cURL as sample
    """
    curl --location 'http://localhost:8080/webhook/YOUR_WEBHOOK_ID' \
        --header 'a: b' \
        --header 'Content-Type: application/json' \
        --data '{
            "id": "user_a",
            "type": "customer"
        }'
    """

    print(f'workflow execution {workflow_run.workflow_id}')
    task_handler.stop_processes()


if __name__ == '__main__':
    main()
