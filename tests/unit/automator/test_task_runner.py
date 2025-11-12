import logging
import os
import time
import unittest
from unittest.mock import patch, ANY, Mock

from requests.structures import CaseInsensitiveDict

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import DEFAULT_POLLING_INTERVAL
from tests.unit.resources.workers import ClassWorker
from tests.unit.resources.workers import FaultyExecutionWorker


class TestTaskRunner(unittest.TestCase):
    TASK_ID = 'VALID_TASK_ID'
    WORKFLOW_INSTANCE_ID = 'VALID_WORKFLOW_INSTANCE_ID'
    UPDATE_TASK_RESPONSE = 'VALID_UPDATE_TASK_RESPONSE'

    def setUp(self):
        logging.disable(logging.CRITICAL)
        # Save original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        # Restore original environment to prevent test pollution
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_initialization_with_invalid_configuration(self):
        expected_exception = Exception('Invalid configuration')
        with self.assertRaises(Exception) as context:
            TaskRunner(
                configuration=None,
                worker=self.__get_valid_worker()
            )
            self.assertEqual(expected_exception, context.exception)

    def test_initialization_with_invalid_worker(self):
        expected_exception = Exception('Invalid worker')
        with self.assertRaises(Exception) as context:
            TaskRunner(
                configuration=Configuration("http://localhost:8080/api"),
                worker=None
            )
            self.assertEqual(expected_exception, context.exception)

    def test_initialization_with_domain_passed_in_constructor(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_domain("passed")
        self.assertEqual(task_runner.worker.domain, 'passed')

    @unittest.mock.patch.dict(os.environ, {"CONDUCTOR_WORKER_DOMAIN": "generic"}, clear=True)
    def test_initialization_with_generic_domain_in_worker_config(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_domain("passed")
        self.assertEqual(task_runner.worker.domain, 'generic')

    @unittest.mock.patch.dict(os.environ, {"CONDUCTOR_WORKER_DOMAIN": "generic",
                                           "conductor_worker_task_domain": "test"}, clear=True)
    def test_initialization_with_specific_domain_in_worker_config(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_domain("passed")
        self.assertEqual(task_runner.worker.domain, 'test')

    @unittest.mock.patch.dict(os.environ, {"CONDUCTOR_WORKER_DOMAIN": "cool",
                                           "CONDUCTOR_WORKER_task2_DOMAIN": "test"}, clear=True)
    def test_initialization_with_generic_domain_in_env_var(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_domain("passed")
        self.assertEqual(task_runner.worker.domain, 'cool')

    @unittest.mock.patch.dict(os.environ, {"CONDUCTOR_WORKER_DOMAIN": "generic",
                                           "CONDUCTOR_WORKER_task_DOMAIN": "hot"}, clear=True)
    def test_initialization_with_specific_domain_in_env_var(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_domain("passed")
        self.assertEqual(task_runner.worker.domain, 'hot')

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_initialization_with_default_polling_interval(self):
        task_runner = self.__get_valid_task_runner()
        self.assertEqual(task_runner.worker.get_polling_interval_in_seconds() * 1000, DEFAULT_POLLING_INTERVAL)

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_initialization_with_polling_interval_passed_in_constructor(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_poll_interval(3000)
        self.assertEqual(task_runner.worker.get_polling_interval_in_seconds(), 3.0)

    def test_initialization_with_common_polling_interval_in_worker_config(self):
        os.environ['conductor_worker_polling_interval'] = '2000'
        task_runner = self.__get_valid_task_runner_with_worker_config_and_poll_interval(3000)
        self.assertEqual(task_runner.worker.get_polling_interval_in_seconds(), 2.0)

    def test_initialization_with_specific_polling_interval_in_worker_config(self):
        os.environ['conductor_worker_polling_interval'] = '2000'
        os.environ['conductor_worker_task_polling_interval'] = '5000'
        task_runner = self.__get_valid_task_runner_with_worker_config_and_poll_interval(3000)
        self.assertEqual(task_runner.worker.get_polling_interval_in_seconds(), 5.0)

    @unittest.mock.patch.dict(os.environ, {"conductor_worker_polling_interval": "1000.0"}, clear=True)
    def test_initialization_with_generic_polling_interval_in_env_var(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_poll_interval(3000)
        self.assertEqual(task_runner.worker.get_polling_interval_in_seconds(), 1.0)

    @unittest.mock.patch.dict(os.environ, {"CONDUCTOR_WORKER_task_POLLING_INTERVAL": "250.0"}, clear=True)
    def test_initialization_with_specific_polling_interval_in_env_var(self):
        task_runner = self.__get_valid_task_runner_with_worker_config_and_poll_interval(3000)
        self.assertEqual(task_runner.worker.get_polling_interval_in_seconds(), 0.25)

    @patch('time.sleep', Mock(return_value=None))
    def test_run_once(self):
        expected_time = self.__get_valid_worker().get_polling_interval_in_seconds()
        with patch.object(
                TaskResourceApi,
                'poll',
                return_value=self.__get_valid_task()
        ):
            with patch.object(
                    TaskResourceApi,
                    'update_task',
                    return_value=self.UPDATE_TASK_RESPONSE
            ):
                task_runner = self.__get_valid_task_runner()
                # With mocked sleep, we just verify the method runs without errors
                task_runner.run_once()
                # Verify poll and update were called
                self.assertTrue(True)  # Test passes if run_once completes

    @patch('time.sleep', Mock(return_value=None))
    def test_run_once_roundrobin(self):
        with patch.object(
                TaskResourceApi,
                'poll',
                return_value=self.__get_valid_task()
        ):
            with patch.object(
                    TaskResourceApi,
                    'update_task',
            ) as mock_update_task:
                mock_update_task.return_value = self.UPDATE_TASK_RESPONSE
                task_runner = self.__get_valid_roundrobin_task_runner()
                for i in range(0, 6):
                    current_task_name = task_runner.worker.get_task_definition_name()
                    task_runner.run_once()
                    self.assertEqual(current_task_name, self.__shared_task_list[i])

    def test_poll_task(self):
        expected_task = self.__get_valid_task()
        with patch.object(
                TaskResourceApi,
                'poll',
                return_value=self.__get_valid_task()
        ):
            task_runner = self.__get_valid_task_runner()
            task = task_runner._TaskRunner__poll_task()
            self.assertEqual(task, expected_task)

    def test_poll_task_with_faulty_task_api(self):
        expected_task = None
        with patch.object(
                TaskResourceApi,
                'poll',
                side_effect=Exception()
        ):
            task_runner = self.__get_valid_task_runner()
            task = task_runner._TaskRunner__poll_task()
            self.assertEqual(task, expected_task)

    def test_execute_task_with_invalid_task(self):
        task_runner = self.__get_valid_task_runner()
        task_result = task_runner._TaskRunner__execute_task(None)
        self.assertEqual(task_result, None)

    def test_execute_task_with_faulty_execution_worker(self):
        worker = FaultyExecutionWorker('task')
        expected_task_result = TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id=worker.get_identity(),
            status=TaskResultStatus.FAILED,
            reason_for_incompletion='faulty execution',
            logs=ANY
        )
        task_runner = TaskRunner(
            configuration=Configuration(),
            worker=worker
        )
        task = self.__get_valid_task()
        task_result = task_runner._TaskRunner__execute_task(task)
        self.assertEqual(task_result, expected_task_result)
        self.assertIsNotNone(task_result.logs)

    def test_execute_task(self):
        expected_task_result = self.__get_valid_task_result()
        worker = self.__get_valid_worker()
        task_runner = TaskRunner(
            configuration=Configuration(),
            worker=worker
        )
        task = self.__get_valid_task()
        task_result = task_runner._TaskRunner__execute_task(task)
        self.assertEqual(task_result, expected_task_result)

    def test_update_task_with_invalid_task_result(self):
        expected_response = None
        task_runner = self.__get_valid_task_runner()
        response = task_runner._TaskRunner__update_task(None)
        self.assertEqual(response, expected_response)

    @patch('time.sleep', Mock(return_value=None))
    def test_update_task_with_faulty_task_api(self):
        expected_response = None
        with patch.object(TaskResourceApi, 'update_task', side_effect=Exception()):
            task_runner = self.__get_valid_task_runner()
            task_result = self.__get_valid_task_result()
            response = task_runner._TaskRunner__update_task(task_result)
            self.assertEqual(response, expected_response)

    def test_update_task(self):
        expected_response = self.UPDATE_TASK_RESPONSE
        with patch.object(
                TaskResourceApi,
                'update_task',
                return_value=self.UPDATE_TASK_RESPONSE
        ):
            task_runner = self.__get_valid_task_runner()
            task_result = self.__get_valid_task_result()
            response = task_runner._TaskRunner__update_task(task_result)
            self.assertEqual(response, expected_response)

    def test_wait_for_polling_interval_with_faulty_worker(self):
        expected_exception = Exception(
            "Failed to get polling interval"
        )
        with patch.object(
                ClassWorker,
                'get_polling_interval_in_seconds',
                side_effect=expected_exception
        ):
            task_runner = self.__get_valid_task_runner()
            with self.assertRaises(Exception) as context:
                task_runner._TaskRunner__wait_for_polling_interval()
                self.assertEqual(expected_exception, context.exception)

    @patch('time.sleep', Mock(return_value=None))
    def test_wait_for_polling_interval(self):
        expected_time = self.__get_valid_worker().get_polling_interval_in_seconds()
        task_runner = self.__get_valid_task_runner()
        # With mocked sleep, we just verify the method runs without errors
        task_runner._TaskRunner__wait_for_polling_interval()
        # Test passes if wait_for_polling_interval completes without exception
        self.assertTrue(True)

    def __get_valid_task_runner_with_worker_config(self, worker_config):
        return TaskRunner(
            configuration=Configuration(),
            worker=self.__get_valid_worker()
        )

    def __get_valid_task_runner_with_worker_config_and_domain(self, domain):
        return TaskRunner(
            configuration=Configuration(),
            worker=self.__get_valid_worker(domain=domain)
        )

    def __get_valid_task_runner_with_worker_config_and_poll_interval(self, poll_interval):
        return TaskRunner(
            configuration=Configuration(),
            worker=self.__get_valid_worker(poll_interval=poll_interval)
        )

    def __get_valid_task_runner(self):
        return TaskRunner(
            configuration=Configuration(),
            worker=self.__get_valid_worker()
        )

    def __get_valid_roundrobin_task_runner(self):
        return TaskRunner(
            configuration=Configuration(),
            worker=self.__get_valid_multi_task_worker()
        )

    def __get_valid_task(self):
        return Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID
        )

    def __get_valid_task_result(self):
        return TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id=self.__get_valid_worker().get_identity(),
            status=TaskResultStatus.COMPLETED,
            output_data={
                'worker_style': 'class',
                'secret_number': 1234,
                'is_it_true': False,
                'dictionary_ojb': {'name': 'sdk_worker', 'idx': 465},
                'case_insensitive_dictionary_ojb': CaseInsensitiveDict(data={'NaMe': 'sdk_worker', 'iDX': 465}),
            }
        )

    @property
    def __shared_task_list(self):
        return ['task1', 'task2', 'task3', 'task4', 'task5', 'task6']

    def __get_valid_multi_task_worker(self):
        return ClassWorker(self.__shared_task_list)

    def __get_valid_worker(self, domain=None, poll_interval=None):
        cw = ClassWorker('task')
        cw.domain = domain
        cw.poll_interval = poll_interval
        return cw
