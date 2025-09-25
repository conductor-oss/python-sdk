import uuid

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.http_poll_task import HttpPollTask, HttpPollInput


def main():
    api_config = Configuration()
    api_config.apply_logging_config()

    workflow_executor = OrkesClients().get_workflow_executor()
    workflow = ConductorWorkflow(executor=workflow_executor, name='http_poll_example_' + str(uuid.uuid4()))
    http_poll = HttpPollTask(task_ref_name='http_poll_ref',
                             http_input=HttpPollInput(
                                 uri='https://orkes-api-tester.orkesconductor.com/api',
                                 polling_strategy='EXPONENTIAL_BACKOFF',
                                 polling_interval=1000,
                                 termination_condition='(function(){ return $.output.response.body.randomInt < 10;})();'),
                             )
    workflow >> http_poll

    # execute the workflow to get the results
    result = workflow.execute(workflow_input={}, wait_for_seconds=10)
    print(f'result: {result.output}')


if __name__ == '__main__':
    main()
