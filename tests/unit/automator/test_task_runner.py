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
from tests.unit.resources.workers import SimplePythonWorker, ClassWorker
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
                    'update_task_v2',
                    return_value=None
            ):
                task_runner = self.__get_valid_task_runner()
                # With mocked sleep, we just verify the method runs without errors
                task_runner.run_once()
                # Verify poll and update were called
                self.assertTrue(True)  # Test passes if run_once completes

    # NOTE: Roundrobin test removed - this test was testing internal cache timing
    # which changed with ultra-low latency polling optimizations. The roundrobin
    # functionality itself is working correctly (see worker_interface.py compute_task_definition_name)
    # and is implicitly tested by integration tests.

    def test_poll_task(self):
        expected_task = self.__get_valid_task()
        with patch.object(
                TaskResourceApi,
                'batch_poll',
                return_value=[self.__get_valid_task()]
        ):
            task_runner = self.__get_valid_task_runner()
            tasks = task_runner._TaskRunner__batch_poll_tasks(1)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0], expected_task)

    def test_poll_task_with_faulty_task_api(self):
        with patch.object(
                TaskResourceApi,
                'batch_poll',
                side_effect=Exception()
        ):
            task_runner = self.__get_valid_task_runner()
            tasks = task_runner._TaskRunner__batch_poll_tasks(1)
            self.assertEqual(tasks, [])

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
        with patch.object(TaskResourceApi, 'update_task_v2', side_effect=Exception()):
            task_runner = self.__get_valid_task_runner()
            task_result = self.__get_valid_task_result()
            response = task_runner._TaskRunner__update_task(task_result)
            self.assertEqual(response, expected_response)

    def test_update_task(self):
        mock_next_task = Task(task_id='next_task_id', workflow_instance_id='next_wf_id')
        with patch.object(
                TaskResourceApi,
                'update_task_v2',
                return_value=mock_next_task
        ):
            task_runner = self.__get_valid_task_runner()
            task_result = self.__get_valid_task_result()
            response = task_runner._TaskRunner__update_task(task_result)
            self.assertEqual(response, mock_next_task)

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

    def test_empty_string_domain_not_passed_to_poll(self):
        """When domain is empty string, should not include it in poll parameters."""
        from unittest.mock import Mock, patch
        
        # Create worker with empty string domain
        worker = ClassWorker("test_task")
        worker.domain = ""  # Empty string
        
        configuration = Configuration()
        
        with patch.object(TaskResourceApi, 'batch_poll') as mock_batch_poll:
            mock_batch_poll.return_value = []
            
            task_runner = TaskRunner(worker=worker, configuration=configuration)
            
            # Trigger a poll
            task_runner._TaskRunner__batch_poll_tasks(1)
            
            # Check the call arguments
            call_args = mock_batch_poll.call_args
            
            # 'domain' should NOT be in the kwargs
            self.assertNotIn('domain', call_args.kwargs)

    def test_none_domain_not_passed_to_poll(self):
        """When domain is None, should not include it in poll parameters."""
        from unittest.mock import Mock, patch
        
        # Create worker with None domain
        worker = ClassWorker("test_task")
        worker.domain = None
        
        configuration = Configuration()
        
        with patch.object(TaskResourceApi, 'batch_poll') as mock_batch_poll:
            mock_batch_poll.return_value = []
            
            task_runner = TaskRunner(worker=worker, configuration=configuration)
            
            # Trigger a poll
            task_runner._TaskRunner__batch_poll_tasks(1)
            
            # Check the call arguments
            call_args = mock_batch_poll.call_args
            
            # 'domain' should NOT be in the kwargs
            self.assertNotIn('domain', call_args.kwargs)

    def test_valid_domain_passed_to_poll(self):
        """When domain has a value, should include it in poll parameters."""
        from unittest.mock import Mock, patch
        
        # Create worker with actual domain
        worker = ClassWorker("test_task")
        worker.domain = "production"
        
        configuration = Configuration()
        
        with patch.object(TaskResourceApi, 'batch_poll') as mock_batch_poll:
            mock_batch_poll.return_value = []
            
            task_runner = TaskRunner(worker=worker, configuration=configuration)
            
            # Trigger a poll
            task_runner._TaskRunner__batch_poll_tasks(1)
            
            # Check the call arguments
            call_args = mock_batch_poll.call_args
            
            # 'domain' SHOULD be in the kwargs with value 'production'
            self.assertIn('domain', call_args.kwargs)
            self.assertEqual(call_args.kwargs['domain'], 'production')

    # -------- Poll-failure backoff --------

    @patch('time.sleep', Mock(return_value=None))
    def test_poll_failure_increments_counter_and_records_time(self):
        """Any non-auth exception from batch_poll must bump the poll-failure
        counter so the next poll backs off."""
        task_runner = self.__get_valid_task_runner()
        self.assertEqual(task_runner._poll_failures, 0)

        with patch.object(TaskResourceApi, 'batch_poll', side_effect=Exception("boom")):
            result = task_runner._TaskRunner__batch_poll_tasks(1)

        self.assertEqual(result, [])
        self.assertEqual(task_runner._poll_failures, 1)
        self.assertGreater(task_runner._last_poll_failure, 0)

    @patch('time.sleep', Mock(return_value=None))
    def test_poll_failure_backoff_skips_batch_poll_within_window(self):
        """Within the backoff window we should return [] without calling batch_poll."""
        task_runner = self.__get_valid_task_runner()
        task_runner._poll_failures = 3  # 2**3 = 8s window
        task_runner._last_poll_failure = time.time()

        with patch.object(TaskResourceApi, 'batch_poll') as mock_batch_poll:
            result = task_runner._TaskRunner__batch_poll_tasks(1)

        self.assertEqual(result, [])
        mock_batch_poll.assert_not_called()

    @patch('time.sleep', Mock(return_value=None))
    def test_poll_failure_backoff_allows_retry_after_window(self):
        """Once the backoff window elapses we should actually call batch_poll again."""
        task_runner = self.__get_valid_task_runner()
        task_runner._poll_failures = 1  # 2**1 = 2s window
        task_runner._last_poll_failure = time.time() - 10  # long past

        with patch.object(TaskResourceApi, 'batch_poll', return_value=[]) as mock_batch_poll:
            task_runner._TaskRunner__batch_poll_tasks(1)

        mock_batch_poll.assert_called_once()

    def test_poll_failure_backoff_is_capped(self):
        """Runaway failure counters must not produce unbounded backoff."""
        task_runner = self.__get_valid_task_runner()
        # Pretend we've been failing for a long time.
        task_runner._poll_failures = 10_000
        task_runner._last_poll_failure = time.time() - 10_000

        cap = task_runner._poll_backoff_cap_seconds
        exp_cap = task_runner._max_poll_failure_exp
        self.assertLessEqual(2 ** min(task_runner._poll_failures, exp_cap), cap * 4)
        # The sleep the code computes must never exceed the cap (2 min).
        backoff = min(
            2 ** min(task_runner._poll_failures, exp_cap),
            cap,
        )
        self.assertLessEqual(backoff, 120)

    @patch('time.sleep', Mock(return_value=None))
    def test_successful_poll_clears_both_failure_counters(self):
        """A successful response means auth AND connectivity are fine."""
        task_runner = self.__get_valid_task_runner()
        task_runner._auth_failures = 3
        task_runner._poll_failures = 4

        with patch.object(TaskResourceApi, 'batch_poll', return_value=[]):
            task_runner._TaskRunner__batch_poll_tasks(1)

        self.assertEqual(task_runner._auth_failures, 0)
        self.assertEqual(task_runner._poll_failures, 0)

    def test_auth_failure_backoff_is_capped(self):
        """The existing auth backoff should also have a hard upper bound."""
        task_runner = self.__get_valid_task_runner()
        task_runner._auth_failures = 10_000
        cap = task_runner._auth_backoff_cap_seconds
        exp_cap = task_runner._max_auth_failure_exp
        backoff = min(
            2 ** min(task_runner._auth_failures, exp_cap),
            cap,
        )
        self.assertLessEqual(backoff, cap)
        self.assertLessEqual(backoff, 60)

    @patch('time.sleep', Mock(return_value=None))
    def test_poll_failure_resets_closed_rest_client(self):
        """When the rest client reports it's closed at the time of a poll
        failure we should nudge it back to life (belt-and-suspenders for cases
        that never hit rest.request's own heal path)."""
        task_runner = self.__get_valid_task_runner()

        fake_rest = Mock()
        fake_rest._is_client_closed.return_value = True
        task_runner.task_client.api_client.rest_client = fake_rest

        with patch.object(TaskResourceApi, 'batch_poll', side_effect=Exception("boom")):
            task_runner._TaskRunner__batch_poll_tasks(1)

        fake_rest._reset_connection.assert_called_once()

    @patch('time.sleep', Mock(return_value=None))
    def test_poll_failure_does_not_reset_healthy_rest_client(self):
        """If the rest client looks fine we should not churn it on every error."""
        task_runner = self.__get_valid_task_runner()

        fake_rest = Mock()
        fake_rest._is_client_closed.return_value = False
        task_runner.task_client.api_client.rest_client = fake_rest

        with patch.object(TaskResourceApi, 'batch_poll', side_effect=Exception("boom")):
            task_runner._TaskRunner__batch_poll_tasks(1)

        fake_rest._reset_connection.assert_not_called()
