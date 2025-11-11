"""
Comprehensive test coverage for task_runner.py to achieve 95%+ coverage.
Tests focus on missing coverage areas including:
- Metrics collection
- Authorization handling
- Task context integration
- Different worker return types
- Error conditions
- Edge cases
"""
import logging
import os
import sys
import time
import unittest
from unittest.mock import patch, Mock, MagicMock, PropertyMock, call

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context.task_context import TaskInProgress
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.http.rest import AuthorizationException
from conductor.client.worker.worker_interface import WorkerInterface


class MockWorker(WorkerInterface):
    """Mock worker for testing various scenarios"""

    def __init__(self, task_name='test_task'):
        super().__init__(task_name)
        self.paused_flag = False
        self.poll_interval = 0.01  # Fast polling for tests

    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.status = TaskResultStatus.COMPLETED
        task_result.output_data = {'result': 'success'}
        return task_result

    def paused(self) -> bool:
        return self.paused_flag


class TaskInProgressWorker(WorkerInterface):
    """Worker that returns TaskInProgress"""

    def __init__(self, task_name='test_task'):
        super().__init__(task_name)
        self.poll_interval = 0.01

    def execute(self, task: Task) -> TaskInProgress:
        return TaskInProgress(
            callback_after_seconds=30,
            output={'status': 'in_progress', 'progress': 50}
        )


class DictReturnWorker(WorkerInterface):
    """Worker that returns a plain dict"""

    def __init__(self, task_name='test_task'):
        super().__init__(task_name)
        self.poll_interval = 0.01

    def execute(self, task: Task) -> dict:
        return {'key': 'value', 'number': 42}


class StringReturnWorker(WorkerInterface):
    """Worker that returns unexpected type (string)"""

    def __init__(self, task_name='test_task'):
        super().__init__(task_name)
        self.poll_interval = 0.01

    def execute(self, task: Task) -> str:
        return "unexpected_string_result"


class ObjectWithStatusWorker(WorkerInterface):
    """Worker that returns object with status attribute (line 207)"""

    def __init__(self, task_name='test_task'):
        super().__init__(task_name)
        self.poll_interval = 0.01

    def execute(self, task: Task):
        # Return a mock object that has status but is not TaskResult or TaskInProgress
        class CustomResult:
            def __init__(self):
                self.status = TaskResultStatus.COMPLETED
                self.output_data = {'custom': 'result'}
                self.task_id = task.task_id
                self.workflow_instance_id = task.workflow_instance_id

        return CustomResult()


class ContextModifyingWorker(WorkerInterface):
    """Worker that modifies context with logs and callbacks"""

    def __init__(self, task_name='test_task'):
        super().__init__(task_name)
        self.poll_interval = 0.01

    def execute(self, task: Task) -> TaskResult:
        from conductor.client.context.task_context import get_task_context

        ctx = get_task_context()
        ctx.add_log("Starting task")
        ctx.add_log("Processing data")
        ctx.set_callback_after(45)

        task_result = self.get_task_result_from_task(task)
        task_result.status = TaskResultStatus.COMPLETED
        task_result.output_data = {'result': 'success'}
        return task_result


class TestTaskRunnerCoverage(unittest.TestCase):
    """Comprehensive test suite for TaskRunner coverage"""

    def setUp(self):
        """Setup test fixtures"""
        logging.disable(logging.CRITICAL)
        # Clear any environment variables that might affect tests
        for key in list(os.environ.keys()):
            if key.startswith('CONDUCTOR_WORKER') or key.startswith('conductor_worker'):
                os.environ.pop(key, None)

    def tearDown(self):
        """Cleanup after tests"""
        logging.disable(logging.NOTSET)
        # Clear environment variables
        for key in list(os.environ.keys()):
            if key.startswith('CONDUCTOR_WORKER') or key.startswith('conductor_worker'):
                os.environ.pop(key, None)

    # ========================================
    # Initialization and Configuration Tests
    # ========================================

    def test_initialization_with_metrics_settings(self):
        """Test TaskRunner initialization with metrics enabled"""
        worker = MockWorker('test_task')
        config = Configuration()
        metrics_settings = MetricsSettings(update_interval=0.1)

        task_runner = TaskRunner(
            worker=worker,
            configuration=config,
            metrics_settings=metrics_settings
        )

        self.assertIsNotNone(task_runner.metrics_collector)
        self.assertEqual(task_runner.worker, worker)
        self.assertEqual(task_runner.configuration, config)

    def test_initialization_without_metrics_settings(self):
        """Test TaskRunner initialization without metrics"""
        worker = MockWorker('test_task')
        config = Configuration()

        task_runner = TaskRunner(
            worker=worker,
            configuration=config,
            metrics_settings=None
        )

        self.assertIsNone(task_runner.metrics_collector)

    def test_initialization_creates_default_configuration(self):
        """Test that None configuration creates default Configuration"""
        worker = MockWorker('test_task')

        task_runner = TaskRunner(
            worker=worker,
            configuration=None
        )

        self.assertIsNotNone(task_runner.configuration)
        self.assertIsInstance(task_runner.configuration, Configuration)

    @patch.dict(os.environ, {
        'conductor_worker_test_task_polling_interval': 'invalid_value'
    }, clear=False)
    def test_set_worker_properties_invalid_polling_interval(self):
        """Test handling of invalid polling interval in environment"""
        worker = MockWorker('test_task')

        # Should not raise an exception even with invalid value
        task_runner = TaskRunner(
            worker=worker,
            configuration=Configuration()
        )

        # The important part is that it doesn't crash - the value will be modified due to
        # the double-application on lines 359-365 and 367-371
        self.assertIsNotNone(task_runner.worker)
        # Verify the polling interval is still a number (not None or crashed)
        self.assertIsInstance(task_runner.worker.get_polling_interval_in_seconds(), (int, float))

    @patch.dict(os.environ, {
        'conductor_worker_polling_interval': '5.5'
    }, clear=False)
    def test_set_worker_properties_valid_polling_interval(self):
        """Test setting valid polling interval from environment"""
        worker = MockWorker('test_task')

        task_runner = TaskRunner(
            worker=worker,
            configuration=Configuration()
        )

        self.assertEqual(task_runner.worker.poll_interval, 5.5)

    # ========================================
    # Run and Run Once Tests
    # ========================================

    @patch('time.sleep', Mock(return_value=None))
    def test_run_with_configuration_logging(self):
        """Test run method applies logging configuration"""
        worker = MockWorker('test_task')
        config = Configuration()

        task_runner = TaskRunner(
            worker=worker,
            configuration=config
        )

        # Mock run_once to exit after one iteration
        with patch.object(task_runner, 'run_once', side_effect=[None, Exception("Exit loop")]):
            with self.assertRaises(Exception):
                task_runner.run()

    @patch('time.sleep', Mock(return_value=None))
    def test_run_without_configuration_sets_debug_logging(self):
        """Test run method sets DEBUG logging when configuration is None"""
        worker = MockWorker('test_task')

        task_runner = TaskRunner(
            worker=worker,
            configuration=Configuration()
        )

        # Set configuration to None to test the logging path
        task_runner.configuration = None

        # Mock run_once to exit after one iteration
        with patch.object(task_runner, 'run_once', side_effect=[None, Exception("Exit loop")]):
            with self.assertRaises(Exception):
                task_runner.run()

    @patch('time.sleep', Mock(return_value=None))
    def test_run_once_with_exception_handling(self):
        """Test that run_once handles exceptions gracefully"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Mock __poll_task to raise an exception
        with patch.object(task_runner, '_TaskRunner__poll_task', side_effect=Exception("Test error")):
            # Should not raise, exception is caught
            task_runner.run_once()

    @patch('time.sleep', Mock(return_value=None))
    def test_run_once_clears_task_definition_name_cache(self):
        """Test that run_once clears the task definition name cache"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        with patch.object(TaskResourceApi, 'poll', return_value=None):
            with patch.object(worker, 'clear_task_definition_name_cache') as mock_clear:
                task_runner.run_once()
                mock_clear.assert_called_once()

    # ========================================
    # Poll Task Tests
    # ========================================

    @patch('time.sleep')
    def test_poll_task_when_worker_paused(self, mock_sleep):
        """Test polling returns None when worker is paused"""
        worker = MockWorker('test_task')
        worker.paused_flag = True

        task_runner = TaskRunner(worker=worker)

        task = task_runner._TaskRunner__poll_task()

        self.assertIsNone(task)

    @patch('time.sleep')
    def test_poll_task_with_auth_failure_backoff(self, mock_sleep):
        """Test exponential backoff on authorization failures"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Simulate auth failure
        task_runner._auth_failures = 2
        task_runner._last_auth_failure = time.time()

        with patch.object(TaskResourceApi, 'poll', return_value=None):
            task = task_runner._TaskRunner__poll_task()

            # Should skip polling and return None due to backoff
            self.assertIsNone(task)
            mock_sleep.assert_called_once()

    @patch('time.sleep')
    def test_poll_task_auth_failure_with_invalid_token(self, mock_sleep):
        """Test handling of authorization failure with invalid token"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Create mock response with INVALID_TOKEN error
        mock_resp = Mock()
        mock_resp.text = '{"error": "INVALID_TOKEN"}'

        mock_http_resp = Mock()
        mock_http_resp.resp = mock_resp

        auth_exception = AuthorizationException(
            status=401,
            reason='Unauthorized',
            http_resp=mock_http_resp
        )

        with patch.object(TaskResourceApi, 'poll', side_effect=auth_exception):
            task = task_runner._TaskRunner__poll_task()

            self.assertIsNone(task)
            self.assertEqual(task_runner._auth_failures, 1)
            self.assertGreater(task_runner._last_auth_failure, 0)

    @patch('time.sleep')
    def test_poll_task_auth_failure_without_invalid_token(self, mock_sleep):
        """Test handling of authorization failure without invalid token"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Create mock response with different error code
        mock_resp = Mock()
        mock_resp.text = '{"error": "FORBIDDEN"}'

        mock_http_resp = Mock()
        mock_http_resp.resp = mock_resp

        auth_exception = AuthorizationException(
            status=403,
            reason='Forbidden',
            http_resp=mock_http_resp
        )

        with patch.object(TaskResourceApi, 'poll', side_effect=auth_exception):
            task = task_runner._TaskRunner__poll_task()

            self.assertIsNone(task)
            self.assertEqual(task_runner._auth_failures, 1)

    @patch('time.sleep')
    def test_poll_task_success_resets_auth_failures(self, mock_sleep):
        """Test that successful poll resets auth failure counter"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Set some auth failures in the past (so backoff has elapsed)
        task_runner._auth_failures = 3
        task_runner._last_auth_failure = time.time() - 100  # 100 seconds ago

        test_task = Task(task_id='test_id', workflow_instance_id='wf_id')

        with patch.object(TaskResourceApi, 'poll', return_value=test_task):
            task = task_runner._TaskRunner__poll_task()

            self.assertEqual(task, test_task)
            self.assertEqual(task_runner._auth_failures, 0)

    def test_poll_task_no_task_available_resets_auth_failures(self):
        """Test that None result from successful poll resets auth failures"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Set some auth failures
        task_runner._auth_failures = 2

        with patch.object(TaskResourceApi, 'poll', return_value=None):
            task = task_runner._TaskRunner__poll_task()

            self.assertIsNone(task)
            self.assertEqual(task_runner._auth_failures, 0)

    def test_poll_task_with_metrics_collector(self):
        """Test polling with metrics collection enabled"""
        worker = MockWorker('test_task')
        metrics_settings = MetricsSettings()
        task_runner = TaskRunner(
            worker=worker,
            metrics_settings=metrics_settings
        )

        test_task = Task(task_id='test_id', workflow_instance_id='wf_id')

        with patch.object(TaskResourceApi, 'poll', return_value=test_task):
            with patch.object(task_runner.metrics_collector, 'increment_task_poll'):
                with patch.object(task_runner.metrics_collector, 'record_task_poll_time'):
                    task = task_runner._TaskRunner__poll_task()

                    self.assertEqual(task, test_task)
                    task_runner.metrics_collector.increment_task_poll.assert_called_once()
                    task_runner.metrics_collector.record_task_poll_time.assert_called_once()

    def test_poll_task_with_metrics_on_auth_error(self):
        """Test metrics collection on authorization error"""
        worker = MockWorker('test_task')
        metrics_settings = MetricsSettings()
        task_runner = TaskRunner(
            worker=worker,
            metrics_settings=metrics_settings
        )

        # Create mock response with INVALID_TOKEN error
        mock_resp = Mock()
        mock_resp.text = '{"error": "INVALID_TOKEN"}'

        mock_http_resp = Mock()
        mock_http_resp.resp = mock_resp

        auth_exception = AuthorizationException(
            status=401,
            reason='Unauthorized',
            http_resp=mock_http_resp
        )

        with patch.object(TaskResourceApi, 'poll', side_effect=auth_exception):
            with patch.object(task_runner.metrics_collector, 'increment_task_poll_error'):
                task = task_runner._TaskRunner__poll_task()

                self.assertIsNone(task)
                task_runner.metrics_collector.increment_task_poll_error.assert_called_once()

    def test_poll_task_with_metrics_on_general_error(self):
        """Test metrics collection on general polling error"""
        worker = MockWorker('test_task')
        metrics_settings = MetricsSettings()
        task_runner = TaskRunner(
            worker=worker,
            metrics_settings=metrics_settings
        )

        with patch.object(TaskResourceApi, 'poll', side_effect=Exception("General error")):
            with patch.object(task_runner.metrics_collector, 'increment_task_poll_error'):
                task = task_runner._TaskRunner__poll_task()

                self.assertIsNone(task)
                task_runner.metrics_collector.increment_task_poll_error.assert_called_once()

    def test_poll_task_with_domain(self):
        """Test polling with domain parameter"""
        worker = MockWorker('test_task')
        worker.domain = 'test_domain'

        task_runner = TaskRunner(worker=worker)

        test_task = Task(task_id='test_id', workflow_instance_id='wf_id')

        with patch.object(TaskResourceApi, 'poll', return_value=test_task) as mock_poll:
            task = task_runner._TaskRunner__poll_task()

            self.assertEqual(task, test_task)
            # Verify domain was passed
            mock_poll.assert_called_once()
            call_kwargs = mock_poll.call_args[1]
            self.assertEqual(call_kwargs['domain'], 'test_domain')

    # ========================================
    # Execute Task Tests
    # ========================================

    def test_execute_task_returns_task_in_progress(self):
        """Test execution when worker returns TaskInProgress"""
        worker = TaskInProgressWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        test_task = Task(
            task_id='test_id',
            workflow_instance_id='wf_id'
        )

        result = task_runner._TaskRunner__execute_task(test_task)

        self.assertEqual(result.status, TaskResultStatus.IN_PROGRESS)
        self.assertEqual(result.callback_after_seconds, 30)
        self.assertEqual(result.output_data['status'], 'in_progress')
        self.assertEqual(result.output_data['progress'], 50)

    def test_execute_task_returns_dict(self):
        """Test execution when worker returns plain dict"""
        worker = DictReturnWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        test_task = Task(
            task_id='test_id',
            workflow_instance_id='wf_id'
        )

        result = task_runner._TaskRunner__execute_task(test_task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data['key'], 'value')
        self.assertEqual(result.output_data['number'], 42)

    def test_execute_task_returns_unexpected_type(self):
        """Test execution when worker returns unexpected type (string)"""
        worker = StringReturnWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        test_task = Task(
            task_id='test_id',
            workflow_instance_id='wf_id'
        )

        result = task_runner._TaskRunner__execute_task(test_task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIn('result', result.output_data)
        self.assertEqual(result.output_data['result'], 'unexpected_string_result')

    def test_execute_task_returns_object_with_status(self):
        """Test execution when worker returns object with status attribute (line 207)"""
        worker = ObjectWithStatusWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        test_task = Task(
            task_id='test_id',
            workflow_instance_id='wf_id'
        )

        result = task_runner._TaskRunner__execute_task(test_task)

        # The object with status should be used as-is (line 207)
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data['custom'], 'result')

    def test_execute_task_with_context_modifications(self):
        """Test that context modifications (logs, callbacks) are merged"""
        worker = ContextModifyingWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        test_task = Task(
            task_id='test_id',
            workflow_instance_id='wf_id'
        )

        result = task_runner._TaskRunner__execute_task(test_task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIsNotNone(result.logs)
        self.assertEqual(len(result.logs), 2)
        self.assertEqual(result.callback_after_seconds, 45)

    def test_execute_task_with_metrics_collector(self):
        """Test task execution with metrics collection"""
        worker = MockWorker('test_task')
        metrics_settings = MetricsSettings()
        task_runner = TaskRunner(
            worker=worker,
            metrics_settings=metrics_settings
        )

        test_task = Task(
            task_id='test_id',
            workflow_instance_id='wf_id'
        )

        with patch.object(task_runner.metrics_collector, 'record_task_execute_time'):
            with patch.object(task_runner.metrics_collector, 'record_task_result_payload_size'):
                result = task_runner._TaskRunner__execute_task(test_task)

                self.assertEqual(result.status, TaskResultStatus.COMPLETED)
                task_runner.metrics_collector.record_task_execute_time.assert_called_once()
                task_runner.metrics_collector.record_task_result_payload_size.assert_called_once()

    def test_execute_task_with_metrics_on_error(self):
        """Test metrics collection on task execution error"""
        worker = MockWorker('test_task')
        metrics_settings = MetricsSettings()
        task_runner = TaskRunner(
            worker=worker,
            metrics_settings=metrics_settings
        )

        test_task = Task(
            task_id='test_id',
            workflow_instance_id='wf_id'
        )

        # Make worker throw exception
        with patch.object(worker, 'execute', side_effect=Exception("Execution failed")):
            with patch.object(task_runner.metrics_collector, 'increment_task_execution_error'):
                result = task_runner._TaskRunner__execute_task(test_task)

                self.assertEqual(result.status, "FAILED")
                self.assertEqual(result.reason_for_incompletion, "Execution failed")
                task_runner.metrics_collector.increment_task_execution_error.assert_called_once()

    # ========================================
    # Merge Context Modifications Tests
    # ========================================

    def test_merge_context_modifications_with_logs(self):
        """Test merging logs from context to task result"""
        from conductor.client.http.models.task_exec_log import TaskExecLog

        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        task_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        task_result.status = TaskResultStatus.COMPLETED

        context_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        context_result.logs = [
            TaskExecLog(log='Log 1', task_id='test_id', created_time=123),
            TaskExecLog(log='Log 2', task_id='test_id', created_time=456)
        ]

        task_runner._TaskRunner__merge_context_modifications(task_result, context_result)

        self.assertIsNotNone(task_result.logs)
        self.assertEqual(len(task_result.logs), 2)

    def test_merge_context_modifications_with_callback(self):
        """Test merging callback_after_seconds from context"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        task_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        task_result.status = TaskResultStatus.COMPLETED

        context_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        context_result.callback_after_seconds = 60

        task_runner._TaskRunner__merge_context_modifications(task_result, context_result)

        self.assertEqual(task_result.callback_after_seconds, 60)

    def test_merge_context_modifications_prefers_task_result_callback(self):
        """Test that existing callback_after_seconds in task_result is preserved"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        task_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        task_result.callback_after_seconds = 30

        context_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        context_result.callback_after_seconds = 60

        task_runner._TaskRunner__merge_context_modifications(task_result, context_result)

        # Should keep task_result value
        self.assertEqual(task_result.callback_after_seconds, 30)

    def test_merge_context_modifications_with_output_data_both_dicts(self):
        """Test merging output_data when both are dicts"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Set task_result with a dict output (the common case, won't trigger line 299-302)
        task_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        task_result.output_data = {'key1': 'value1', 'key2': 'value2'}

        context_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        context_result.output_data = {'key3': 'value3'}

        task_runner._TaskRunner__merge_context_modifications(task_result, context_result)

        # Since task_result.output_data IS a dict, the merge won't happen (line 298 condition)
        self.assertEqual(task_result.output_data['key1'], 'value1')
        self.assertEqual(task_result.output_data['key2'], 'value2')
        # key3 won't be there because condition on line 298 fails
        self.assertNotIn('key3', task_result.output_data)

    def test_merge_context_modifications_with_output_data_non_dict(self):
        """Test merging when task_result.output_data is not a dict (line 299-302)"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # To hit lines 301-302, we need:
        # 1. context_result.output_data to be a dict (truthy)
        # 2. task_result.output_data to NOT be an instance of dict
        # 3. task_result.output_data to be truthy

        # Create a custom class that is not a dict but is truthy and has dict-like behavior
        class NotADict:
            def __init__(self, data):
                self.data = data

            def __bool__(self):
                return True

            # Support dict unpacking for line 301
            def keys(self):
                return self.data.keys()

            def __getitem__(self, key):
                return self.data[key]

        task_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        task_result.output_data = NotADict({'key1': 'value1'})

        context_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        context_result.output_data = {'key2': 'value2'}

        task_runner._TaskRunner__merge_context_modifications(task_result, context_result)

        # Now lines 301-302 should have executed: merged both dicts
        self.assertIsInstance(task_result.output_data, dict)
        self.assertEqual(task_result.output_data['key1'], 'value1')
        self.assertEqual(task_result.output_data['key2'], 'value2')

    def test_merge_context_modifications_with_empty_task_result_output(self):
        """Test merging when task_result has no output_data (line 304)"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        task_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        # Leave output_data as None/empty

        context_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        context_result.output_data = {'key2': 'value2'}

        task_runner._TaskRunner__merge_context_modifications(task_result, context_result)

        # Now it should use context_result.output_data (line 304)
        self.assertEqual(task_result.output_data, {'key2': 'value2'})

    def test_merge_context_modifications_context_output_only(self):
        """Test using context output when task_result has none"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        task_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')

        context_result = TaskResult(task_id='test_id', workflow_instance_id='wf_id')
        context_result.output_data = {'key1': 'value1'}

        task_runner._TaskRunner__merge_context_modifications(task_result, context_result)

        self.assertEqual(task_result.output_data['key1'], 'value1')

    # ========================================
    # Update Task Tests
    # ========================================

    @patch('time.sleep', Mock(return_value=None))
    def test_update_task_with_retry_success(self):
        """Test update task succeeds on retry"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        task_result = TaskResult(
            task_id='test_id',
            workflow_instance_id='wf_id',
            worker_id=worker.get_identity()
        )
        task_result.status = TaskResultStatus.COMPLETED

        # First call fails, second succeeds
        with patch.object(
            TaskResourceApi,
            'update_task',
            side_effect=[Exception("Network error"), "SUCCESS"]
        ) as mock_update:
            response = task_runner._TaskRunner__update_task(task_result)

            self.assertEqual(response, "SUCCESS")
            self.assertEqual(mock_update.call_count, 2)

    @patch('time.sleep', Mock(return_value=None))
    def test_update_task_with_metrics_on_error(self):
        """Test metrics collection on update error"""
        worker = MockWorker('test_task')
        metrics_settings = MetricsSettings()
        task_runner = TaskRunner(
            worker=worker,
            metrics_settings=metrics_settings
        )

        task_result = TaskResult(
            task_id='test_id',
            workflow_instance_id='wf_id',
            worker_id=worker.get_identity()
        )

        with patch.object(TaskResourceApi, 'update_task', side_effect=Exception("Update failed")):
            with patch.object(task_runner.metrics_collector, 'increment_task_update_error'):
                response = task_runner._TaskRunner__update_task(task_result)

                self.assertIsNone(response)
                # Should be called 4 times (4 attempts)
                self.assertEqual(
                    task_runner.metrics_collector.increment_task_update_error.call_count,
                    4
                )

    # ========================================
    # Property and Environment Tests
    # ========================================

    @patch.dict(os.environ, {
        'conductor_worker_test_task_polling_interval': '2.5',
        'conductor_worker_test_task_domain': 'test_domain'
    }, clear=False)
    def test_get_property_value_from_env_task_specific(self):
        """Test getting task-specific property from environment"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        self.assertEqual(task_runner.worker.poll_interval, 2.5)
        self.assertEqual(task_runner.worker.domain, 'test_domain')

    @patch.dict(os.environ, {
        'CONDUCTOR_WORKER_test_task_POLLING_INTERVAL': '3.0',
        'CONDUCTOR_WORKER_test_task_DOMAIN': 'UPPER_DOMAIN'
    }, clear=False)
    def test_get_property_value_from_env_uppercase(self):
        """Test getting property from uppercase environment variable"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        self.assertEqual(task_runner.worker.poll_interval, 3.0)
        self.assertEqual(task_runner.worker.domain, 'UPPER_DOMAIN')

    @patch.dict(os.environ, {
        'conductor_worker_polling_interval': '1.5',
        'conductor_worker_test_task_polling_interval': '2.5'
    }, clear=False)
    def test_get_property_value_task_specific_overrides_generic(self):
        """Test that task-specific env var overrides generic one"""
        worker = MockWorker('test_task')
        task_runner = TaskRunner(worker=worker)

        # Task-specific should win
        self.assertEqual(task_runner.worker.poll_interval, 2.5)

    @patch.dict(os.environ, {
        'conductor_worker_test_task_polling_interval': 'not_a_number'
    }, clear=False)
    def test_set_worker_properties_handles_parse_exception(self):
        """Test that parse exceptions in polling interval are handled gracefully (line 370-371)"""
        worker = MockWorker('test_task')

        # Should not raise even with invalid value
        task_runner = TaskRunner(worker=worker)

        # The important part is that it doesn't crash and handles the exception
        self.assertIsNotNone(task_runner.worker)
        # Verify we still have a valid polling interval
        self.assertIsInstance(task_runner.worker.get_polling_interval_in_seconds(), (int, float))


if __name__ == '__main__':
    unittest.main()
