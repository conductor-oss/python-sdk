import unittest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.http_task import HttpTask
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.switch_task import SwitchTask
from examples.helloworld.greetings_worker import greet

class WorkflowUnitTest(unittest.TestCase):
    """
    This is an example of how to write a UNIT test for the workflow
    to run:

    python3 -m unittest discover --verbose --start-directory=./

    """
    @classmethod
    def setUpClass(cls) -> None:
        api_config = Configuration()
        clients = OrkesClients(configuration=api_config)
        cls.workflow_executor = clients.get_workflow_executor()
        cls.workflow_client = clients.get_workflow_client()

    def test_greetings_worker(self):
        """
        Tests for the workers
        Conductor workers are regular python functions and can be unit or integrated tested just like any other function
        """
        name = 'test'
        result = greet(name=name)
        self.assertEqual(f'Hello {name}', result)

    def test_workflow_execution(self):
        """
        Test a complete workflow end to end with mock outputs for the task executions
        """
        wf = ConductorWorkflow(name='unit_testing_example', version=1, executor=self.workflow_executor)
        task1 = SimpleTask(task_def_name='hello', task_reference_name='hello_ref_1')
        task2 = SimpleTask(task_def_name='hello', task_reference_name='hello_ref_2')
        task3 = SimpleTask(task_def_name='hello', task_reference_name='hello_ref_3')

        decision = SwitchTask(task_ref_name='switch_ref', case_expression=task1.output('city'))
        decision.switch_case('NYC', task2)
        decision.default_case(task3)

        http = HttpTask(task_ref_name='http', http_input={'uri': 'https://orkes-api-tester.orkesconductor.com/api'})
        wf >> http
        wf >> task1 >> decision

        task_ref_to_mock_output = {}

        # task1 has two attempts, first one failed and second succeeded
        task_ref_to_mock_output[task1.task_reference_name] = [{
            'status': 'FAILED',
            'output': {
                'key': 'failed'
            }
        },
            {
                'status': 'COMPLETED',
                'output': {
                    'city': 'NYC'
                }
            }
        ]

        task_ref_to_mock_output[task2.task_reference_name] = [
            {
                'status': 'COMPLETED',
                'output': {
                    'key': 'task2.output'
                }
            }
        ]

        task_ref_to_mock_output[http.task_reference_name] = [
            {
                'status': 'COMPLETED',
                'output': {
                    'key': 'http.output'
                }
            }
        ]

        test_request = WorkflowTestRequest(name=wf.name, version=wf.version,
                                           task_ref_to_mock_output=task_ref_to_mock_output,
                                           workflow_def=wf.to_workflow_def())
        run = self.workflow_client.test_workflow(test_request=test_request)

        print(f'completed the test run')
        print(f'status: {run.status}')
        self.assertEqual(run.status, 'COMPLETED')

        print(f'first task (HTTP) status: {run.tasks[0].task_type}')
        self.assertEqual(run.tasks[0].task_type, 'HTTP')

        print(f'{run.tasks[1].reference_task_name} status: {run.tasks[1].status} (expected to be FAILED)')
        self.assertEqual(run.tasks[1].status, 'FAILED')

        print(f'{run.tasks[2].reference_task_name} status: {run.tasks[2].status} (expected to be COMPLETED')
        self.assertEqual(run.tasks[2].status, 'COMPLETED')

        print(f'{run.tasks[4].reference_task_name} status: {run.tasks[4].status} (expected to be COMPLETED')
        self.assertEqual(run.tasks[4].status, 'COMPLETED')

        # assert that the task2 was executed
        self.assertEqual(run.tasks[4].reference_task_name, task2.task_reference_name)
