"""
Workflow Unit Testing Example
==============================

This module demonstrates how to write unit tests for Conductor workflows and workers.

Key Concepts:
-------------
1. **Worker Testing**: Test worker functions independently as regular Python functions
2. **Workflow Testing**: Test complete workflows end-to-end with mocked task outputs
3. **Mock Outputs**: Simulate task execution results without running actual workers
4. **Retry Simulation**: Test retry logic by providing multiple outputs (failed then succeeded)
5. **Decision Testing**: Verify switch/decision logic with different input scenarios

Test Types:
-----------
- **Unit Test (test_greetings_worker)**: Tests a single worker function in isolation
- **Integration Test (test_workflow_execution)**: Tests complete workflow with mocked dependencies

Running Tests:
--------------
    python3 -m unittest discover --verbose --start-directory=./
    python3 -m unittest examples.test_workflows.WorkflowUnitTest

Use Cases:
----------
- Validate workflow logic before deployment
- Test error handling and retry behavior
- Verify decision/switch conditions
- CI/CD pipeline integration
- Regression testing for workflow changes
"""

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
    Unit tests for Conductor workflows and workers.

    This test suite demonstrates:
    - Testing individual worker functions
    - Testing complete workflow execution with mocked task outputs
    - Simulating task failures and retries
    - Validating workflow decision logic
    """
    @classmethod
    def setUpClass(cls) -> None:
        api_config = Configuration()
        clients = OrkesClients(configuration=api_config)
        cls.workflow_executor = clients.get_workflow_executor()
        cls.workflow_client = clients.get_workflow_client()

    def test_greetings_worker(self):
        """
        Unit test for a worker function.

        Demonstrates:
        - Worker functions are regular Python functions that can be tested directly
        - No need to start worker processes or connect to Conductor server
        - Fast, isolated testing of business logic
        - Can use standard Python testing tools (unittest, pytest, etc.)

        This approach is ideal for:
        - Testing worker logic in isolation
        - Running tests in CI/CD pipelines
        - Test-driven development (TDD)
        - Quick feedback during development
        """
        name = 'test'
        result = greet(name=name)
        self.assertEqual(f'Hello {name}', result)

    def test_workflow_execution(self):
        """
        Integration test for a complete workflow with mocked task outputs.

        Demonstrates:
        - Testing workflow logic without running actual workers
        - Mocking task outputs to simulate different scenarios
        - Testing retry behavior (task failure followed by success)
        - Testing decision/switch logic with different inputs
        - Validating workflow execution paths

        Key Benefits:
        - Fast execution (no actual task execution)
        - Deterministic results (mocked outputs)
        - No external dependencies (no worker processes)
        - Test error scenarios safely
        - Validate workflow structure and logic

        Workflow Structure:
        -------------------
        1. HTTP task (always succeeds)
        2. task1 (fails first, succeeds on retry with city='NYC')
        3. Switch decision based on task1.output('city')
        4. If city='NYC': execute task2
        5. Otherwise: execute task3

        Expected Flow:
        --------------
        HTTP → task1 (FAILED) → task1 (RETRY, COMPLETED) → switch → task2
        """
        # Create workflow with tasks
        wf = ConductorWorkflow(name='unit_testing_example', version=1, executor=self.workflow_executor)
        task1 = SimpleTask(task_def_name='hello', task_reference_name='hello_ref_1')
        task2 = SimpleTask(task_def_name='hello', task_reference_name='hello_ref_2')
        task3 = SimpleTask(task_def_name='hello', task_reference_name='hello_ref_3')

        # Switch decision: if city='NYC' → task2, else → task3
        decision = SwitchTask(task_ref_name='switch_ref', case_expression=task1.output('city'))
        decision.switch_case('NYC', task2)
        decision.default_case(task3)

        # HTTP task to simulate external API call
        http = HttpTask(task_ref_name='http', http_input={'uri': 'https://orkes-api-tester.orkesconductor.com/api'})
        wf >> http
        wf >> task1 >> decision

        # Mock outputs for each task
        task_ref_to_mock_output = {}

        # task1 has two attempts: first fails, second succeeds
        # This tests retry behavior
        task_ref_to_mock_output[task1.task_reference_name] = [{
            'status': 'FAILED',
            'output': {
                'key': 'failed'
            }
        },
            {
                'status': 'COMPLETED',
                'output': {
                    'city': 'NYC'  # This triggers the switch to execute task2
                }
            }
        ]

        # task2 succeeds (executed because city='NYC')
        task_ref_to_mock_output[task2.task_reference_name] = [
            {
                'status': 'COMPLETED',
                'output': {
                    'key': 'task2.output'
                }
            }
        ]

        # HTTP task succeeds
        task_ref_to_mock_output[http.task_reference_name] = [
            {
                'status': 'COMPLETED',
                'output': {
                    'key': 'http.output'
                }
            }
        ]

        # Execute workflow test with mocked outputs
        test_request = WorkflowTestRequest(name=wf.name, version=wf.version,
                                           task_ref_to_mock_output=task_ref_to_mock_output,
                                           workflow_def=wf.to_workflow_def())
        run = self.workflow_client.test_workflow(test_request=test_request)

        # Verify workflow completed successfully
        print(f'completed the test run')
        print(f'status: {run.status}')
        self.assertEqual(run.status, 'COMPLETED')

        # Verify HTTP task executed first
        print(f'first task (HTTP) status: {run.tasks[0].task_type}')
        self.assertEqual(run.tasks[0].task_type, 'HTTP')

        # Verify task1 failed on first attempt (retry test)
        print(f'{run.tasks[1].reference_task_name} status: {run.tasks[1].status} (expected to be FAILED)')
        self.assertEqual(run.tasks[1].status, 'FAILED')

        # Verify task1 succeeded on retry
        print(f'{run.tasks[2].reference_task_name} status: {run.tasks[2].status} (expected to be COMPLETED')
        self.assertEqual(run.tasks[2].status, 'COMPLETED')

        # Verify switch decision executed task2 (because city='NYC')
        print(f'{run.tasks[4].reference_task_name} status: {run.tasks[4].status} (expected to be COMPLETED')
        self.assertEqual(run.tasks[4].status, 'COMPLETED')

        # Verify the correct branch was taken (task2, not task3)
        self.assertEqual(run.tasks[4].reference_task_name, task2.task_reference_name)
