"""
Tests for API request metrics instrumentation in TaskRunnerAsyncIO.

Tests cover:
1. API timing on successful poll requests
2. API timing on failed poll requests
3. API timing on successful update requests
4. API timing on failed update requests
5. API timing on retry requests after auth renewal
6. Status code extraction from various error types
7. Metrics recording with and without metrics collector
"""

import asyncio
import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch, MagicMock, call
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None

from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker import Worker
from conductor.client.telemetry.metrics_collector import MetricsCollector


class TestWorker(Worker):
    """Test worker for API metrics tests"""
    def __init__(self):
        def execute_fn(task):
            return {"result": "success"}
        super().__init__('test_task', execute_fn)


@unittest.skipIf(httpx is None, "httpx not installed")
class TestAPIMetrics(unittest.TestCase):
    """Test API request metrics instrumentation"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = Configuration(server_api_url='http://localhost:8080/api')
        self.worker = TestWorker()

        # Create temporary directory for metrics
        self.metrics_dir = tempfile.mkdtemp()
        self.metrics_settings = MetricsSettings(
            directory=self.metrics_dir,
            file_name='test_metrics.prom',
            update_interval=0.1
        )

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.metrics_dir):
            shutil.rmtree(self.metrics_dir)

    def test_api_timing_successful_poll(self):
        """Test API request timing is recorded on successful poll"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_settings=self.metrics_settings
        )

        # Mock the metrics_collector's record method
        runner.metrics_collector.record_api_request_time = Mock()

        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(return_value=mock_response)

            # Call poll
            await runner.poll_and_execute_task()

            # Verify API timing was recorded
            runner.metrics_collector.record_api_request_time.assert_called()
            call_args = runner.metrics_collector.record_api_request_time.call_args

            # Check parameters
            self.assertEqual(call_args.kwargs['method'], 'GET')
            self.assertIn('/tasks/poll/batch/test_task', call_args.kwargs['uri'])
            self.assertEqual(call_args.kwargs['status'], '200')
            self.assertGreater(call_args.kwargs['time_spent'], 0)
            self.assertLess(call_args.kwargs['time_spent'], 1)  # Should be sub-second

        asyncio.run(run_test())

    def test_api_timing_failed_poll_with_status_code(self):
        """Test API request timing is recorded on failed poll with status code"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        # Mock HTTP error with response
        mock_response = Mock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(side_effect=error)

            # Call poll (should handle exception)
            try:
                await runner.poll_and_execute_task()
            except:
                pass

            # Verify API timing was recorded with error status
            self.metrics_collector.record_api_request_time.assert_called()
            call_args = self.metrics_collector.record_api_request_time.call_args

            self.assertEqual(call_args.kwargs['method'], 'GET')
            self.assertEqual(call_args.kwargs['status'], '500')
            self.assertGreater(call_args.kwargs['time_spent'], 0)

        asyncio.run(run_test())

    def test_api_timing_failed_poll_without_status_code(self):
        """Test API request timing with generic error (no response attribute)"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        # Mock generic network error
        error = httpx.ConnectError("Connection refused")

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(side_effect=error)

            # Call poll
            try:
                await runner.poll_and_execute_task()
            except:
                pass

            # Verify API timing was recorded with "error" status
            self.metrics_collector.record_api_request_time.assert_called()
            call_args = self.metrics_collector.record_api_request_time.call_args

            self.assertEqual(call_args.kwargs['method'], 'GET')
            self.assertEqual(call_args.kwargs['status'], 'error')

        asyncio.run(run_test())

    def test_api_timing_successful_update(self):
        """Test API request timing is recorded on successful task update"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        # Create task and result
        task = Task(task_id='task1', task_def_name='test_task')
        task_result = TaskResult(
            task_id='task1',
            status=TaskResultStatus.COMPLETED,
            output_data={'result': 'success'}
        )

        # Mock successful update response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ''

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.post = AsyncMock(return_value=mock_response)

            # Call update
            await runner._update_task(task, task_result)

            # Verify API timing was recorded
            self.metrics_collector.record_api_request_time.assert_called()
            call_args = self.metrics_collector.record_api_request_time.call_args

            self.assertEqual(call_args.kwargs['method'], 'POST')
            self.assertIn('/tasks/update', call_args.kwargs['uri'])
            self.assertEqual(call_args.kwargs['status'], '200')
            self.assertGreater(call_args.kwargs['time_spent'], 0)

        asyncio.run(run_test())

    def test_api_timing_failed_update(self):
        """Test API request timing is recorded on failed task update"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        task = Task(task_id='task1', task_def_name='test_task')
        task_result = TaskResult(
            task_id='task1',
            status=TaskResultStatus.COMPLETED
        )

        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 503
        error = httpx.HTTPStatusError("Service unavailable", request=Mock(), response=mock_response)

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.post = AsyncMock(side_effect=error)

            # Call update
            try:
                await runner._update_task(task, task_result)
            except:
                pass

            # Verify API timing was recorded
            self.metrics_collector.record_api_request_time.assert_called()
            call_args = self.metrics_collector.record_api_request_time.call_args

            self.assertEqual(call_args.kwargs['method'], 'POST')
            self.assertEqual(call_args.kwargs['status'], '503')

        asyncio.run(run_test())

    def test_api_timing_multiple_requests(self):
        """Test API timing tracks multiple requests correctly"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(return_value=mock_response)

            # Poll 3 times
            await runner.poll_and_execute_task()
            await runner.poll_and_execute_task()
            await runner.poll_and_execute_task()

            # Should have 3 API timing records
            self.assertEqual(self.metrics_collector.record_api_request_time.call_count, 3)

            # All should be successful
            for call in self.metrics_collector.record_api_request_time.call_args_list:
                self.assertEqual(call.kwargs['status'], '200')

        asyncio.run(run_test())

    def test_api_timing_without_metrics_collector(self):
        """Test that API requests work without metrics collector"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=None
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(return_value=mock_response)

            # Should not raise exception
            await runner.poll_and_execute_task()

            # No metrics recorded (metrics_collector is None)
            # Just verify no exception was raised

        asyncio.run(run_test())

    def test_api_timing_precision(self):
        """Test that API timing has sufficient precision"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        # Mock fast response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        async def run_test():
            runner.http_client = AsyncMock()

            # Add tiny delay to simulate fast request
            async def mock_get(*args, **kwargs):
                await asyncio.sleep(0.001)  # 1ms
                return mock_response

            runner.http_client.get = mock_get

            await runner.poll_and_execute_task()

            # Verify timing captured sub-second precision
            call_args = self.metrics_collector.record_api_request_time.call_args
            time_spent = call_args.kwargs['time_spent']

            # Should be at least 1ms, but less than 100ms
            self.assertGreaterEqual(time_spent, 0.001)
            self.assertLess(time_spent, 0.1)

        asyncio.run(run_test())

    def test_api_timing_auth_error_401(self):
        """Test API timing on 401 authentication error"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        mock_response = Mock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(side_effect=error)

            try:
                await runner.poll_and_execute_task()
            except:
                pass

            # Verify 401 status captured
            call_args = self.metrics_collector.record_api_request_time.call_args
            self.assertEqual(call_args.kwargs['status'], '401')

        asyncio.run(run_test())

    def test_api_timing_timeout_error(self):
        """Test API timing on timeout error"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        error = httpx.TimeoutException("Request timeout")

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(side_effect=error)

            try:
                await runner.poll_and_execute_task()
            except:
                pass

            # Verify "error" status for timeout
            call_args = self.metrics_collector.record_api_request_time.call_args
            self.assertEqual(call_args.kwargs['status'], 'error')

        asyncio.run(run_test())

    def test_api_timing_concurrent_requests(self):
        """Test API timing with concurrent requests from multiple coroutines"""
        runner = TaskRunnerAsyncIO(
            worker=self.worker,
            configuration=self.config,
            metrics_collector=self.metrics_collector
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        async def run_test():
            runner.http_client = AsyncMock()
            runner.http_client.get = AsyncMock(return_value=mock_response)

            # Run 5 concurrent polls
            await asyncio.gather(*[
                runner.poll_and_execute_task() for _ in range(5)
            ])

            # Should have 5 timing records
            self.assertEqual(self.metrics_collector.record_api_request_time.call_count, 5)

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
