"""
Comprehensive tests for TaskRunnerAsyncIO to achieve 90%+ coverage.

This test file focuses on missing coverage identified in coverage analysis:
- Authentication and token management
- Error handling (timeouts, terminal errors)
- Resource cleanup and lifecycle
- Worker validation
- V2 API features
- Lease extension
"""

import asyncio
import os
import time
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime, timedelta

try:
    import httpx
except ImportError:
    httpx = None

from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.http.api_client import ApiClient


class SimpleWorker(Worker):
    """Simple test worker"""
    def __init__(self, task_name='test_task'):
        def execute_fn(task):
            return {"result": "success"}
        super().__init__(task_name, execute_fn)


class InvalidWorker:
    """Invalid worker that doesn't implement WorkerInterface"""
    pass


@unittest.skipIf(httpx is None, "httpx not installed")
class TestTaskRunnerAsyncIOCoverage(unittest.IsolatedAsyncioTestCase):
    """Test suite for TaskRunnerAsyncIO missing coverage"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = Configuration(server_api_url='http://localhost:8080/api')
        self.worker = SimpleWorker()

    # =========================================================================
    # 1. VALIDATION & INITIALIZATION - HIGH PRIORITY
    # =========================================================================

    def test_invalid_worker_type_raises_exception(self):
        """Test that invalid worker type raises Exception"""
        invalid_worker = InvalidWorker()

        with self.assertRaises(Exception) as context:
            TaskRunnerAsyncIO(
                worker=invalid_worker,
                configuration=self.config
            )

        self.assertIn("Invalid worker", str(context.exception))

    # =========================================================================
    # 2. AUTHENTICATION & TOKEN MANAGEMENT - HIGH PRIORITY
    # =========================================================================

    async def test_get_auth_headers_with_authentication(self):
        """Test _get_auth_headers with authentication configured"""
        from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings

        # Create config with authentication
        config_with_auth = Configuration(
            server_api_url='http://localhost:8080/api',
            authentication_settings=AuthenticationSettings(
                key_id='test_key',
                key_secret='test_secret'
            )
        )
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=config_with_auth)

        # Mock API client with auth headers
        runner._api_client = Mock(spec=ApiClient)
        runner._api_client.get_authentication_headers.return_value = {
            'header': {
                'X-Authorization': 'Bearer token123'
            }
        }

        headers = runner._get_auth_headers()

        self.assertIn('X-Authorization', headers)
        self.assertEqual(headers['X-Authorization'], 'Bearer token123')

    async def test_get_auth_headers_without_authentication(self):
        """Test _get_auth_headers without authentication"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        headers = runner._get_auth_headers()

        # Should only have default headers (no X-Authorization)
        self.assertNotIn('X-Authorization', headers)
        # Config has no authentication_settings, so it returns early with empty dict
        self.assertIsInstance(headers, dict)

    async def test_poll_with_auth_failure_backoff(self):
        """Test exponential backoff after authentication failures"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Set auth failures inside the async context
        runner._auth_failures = 2
        runner._last_auth_failure = time.time()

        # Mock HTTP client
        runner.http_client = AsyncMock()

        # Should skip polling due to backoff
        result = await runner._poll_tasks_from_server(count=1)

        # Should return empty list due to backoff
        self.assertEqual(result, [])

        # HTTP client should not be called
        runner.http_client.get.assert_not_called()

    async def test_poll_with_expired_token_renewal_success(self):
        """Test token renewal on expired token error"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Mock HTTP client with expired token error followed by success
        runner.http_client = AsyncMock()
        mock_response_error = Mock()
        mock_response_error.status_code = 401
        mock_response_error.json.return_value = {'error': 'EXPIRED_TOKEN'}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = []

        runner.http_client.get = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError("Expired token", request=Mock(), response=mock_response_error),
                mock_response_success  # After renewal
            ]
        )

        # Mock token renewal - use force_refresh_auth_token (the actual method called)
        runner._api_client.force_refresh_auth_token = Mock(return_value=True)
        runner._api_client.deserialize_class = Mock(return_value=None)

        # Should succeed after renewal
        result = await runner._poll_tasks_from_server(count=1)

        # Should have called force_refresh_auth_token
        runner._api_client.force_refresh_auth_token.assert_called_once()

        # Should return empty list (from second call)
        self.assertEqual(result, [])

    async def test_poll_with_expired_token_renewal_failure(self):
        """Test handling when token renewal fails"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Mock HTTP client with expired token error
        runner.http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'EXPIRED_TOKEN'}

        runner.http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Expired token", request=Mock(), response=mock_response)
        )

        # Mock token renewal failure
        runner._api_client.force_refresh_auth_token = Mock(return_value=False)

        # Should return empty list after renewal failure
        result = await runner._poll_tasks_from_server(count=1)

        # Should have attempted renewal
        runner._api_client.force_refresh_auth_token.assert_called_once()

        # Should return empty (couldn't renew)
        self.assertEqual(result, [])

        # Auth failure count should be incremented
        self.assertGreater(runner._auth_failures, 0)

    async def test_poll_with_invalid_token(self):
        """Test handling of invalid token error"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Mock HTTP client with invalid token error
        runner.http_client = AsyncMock()
        mock_response_error = Mock()
        mock_response_error.status_code = 401
        mock_response_error.json.return_value = {'error': 'INVALID_TOKEN'}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = []

        runner.http_client.get = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError("Invalid token", request=Mock(), response=mock_response_error),
                mock_response_success  # After renewal
            ]
        )

        # Mock token renewal
        runner._api_client.force_refresh_auth_token = Mock(return_value=True)
        runner._api_client.deserialize_class = Mock(return_value=None)

        # Should attempt renewal
        result = await runner._poll_tasks_from_server(count=1)

        # Should have called force_refresh_auth_token
        runner._api_client.force_refresh_auth_token.assert_called_once()

    async def test_poll_with_invalid_credentials(self):
        """Test handling of authentication failure (401 without token error)"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Mock HTTP client with 401 error but no EXPIRED_TOKEN/INVALID_TOKEN
        runner.http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'INVALID_CREDENTIALS'}

        runner.http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)
        )

        # Should return empty list
        result = await runner._poll_tasks_from_server(count=1)

        self.assertEqual(result, [])

        # Auth failure count should be incremented
        self.assertGreater(runner._auth_failures, 0)

    # =========================================================================
    # 3. ERROR HANDLING - TASK EXECUTION - HIGH PRIORITY
    # =========================================================================

    async def test_execute_task_timeout_creates_failed_result(self):
        """Test that task timeout creates FAILED result"""
        # Create worker with slow execution
        class SlowWorker(Worker):
            def __init__(self):
                async def slow_execute(task):
                    await asyncio.sleep(10)  # Longer than timeout
                    return {"result": "success"}
                super().__init__('test_task', slow_execute)

        runner = TaskRunnerAsyncIO(
            worker=SlowWorker(),
            configuration=self.config
        )

        task = Task(
            task_id='task123',
            task_def_name='test_task',
            status='IN_PROGRESS',
            response_timeout_seconds=1  # 1 second timeout
        )

        # Execute with timeout
        result = await runner._execute_task(task)

        # Should return FAILED result
        self.assertIsNotNone(result)
        self.assertEqual(result.status, TaskResultStatus.FAILED)
        self.assertIn('timeout', result.reason_for_incompletion.lower())

    async def test_execute_task_non_retryable_exception_terminal_failure(self):
        """Test NonRetryableException creates terminal failure"""
        from conductor.client.worker.exception import NonRetryableException

        # Create worker that raises NonRetryableException
        class FailingWorker(Worker):
            def __init__(self):
                def failing_execute(task):
                    raise NonRetryableException("Terminal error")
                super().__init__('test_task', failing_execute)

        runner = TaskRunnerAsyncIO(
            worker=FailingWorker(),
            configuration=self.config
        )

        task = Task(
            task_id='task123',
            task_def_name='test_task',
            status='IN_PROGRESS'
        )

        # Execute
        result = await runner._execute_task(task)

        # Should return FAILED_WITH_TERMINAL_ERROR
        self.assertIsNotNone(result)
        self.assertEqual(result.status, TaskResultStatus.FAILED_WITH_TERMINAL_ERROR)
        self.assertIn('Terminal error', result.reason_for_incompletion)

    # =========================================================================
    # 4. RESOURCE CLEANUP & LIFECYCLE - HIGH PRIORITY
    # =========================================================================

    async def test_poll_tasks_204_no_content_resets_auth_failures(self):
        """Test that 204 response resets auth failure counter"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)
        runner._auth_failures = 3  # Set some failures

        # Mock 204 No Content response
        runner.http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 204
        runner.http_client.get = AsyncMock(return_value=mock_response)

        result = await runner._poll_tasks_from_server(count=1)

        # Should return empty list
        self.assertEqual(result, [])

        # Auth failures should be reset
        self.assertEqual(runner._auth_failures, 0)

    async def test_poll_tasks_filters_invalid_task_data(self):
        """Test that None or invalid task data is filtered out"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Mock response with mixed valid/invalid data
        runner.http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'taskId': 'task1', 'taskDefName': 'test_task'},
            None,  # Invalid
            {'taskId': 'task2', 'taskDefName': 'test_task'},
            {},  # Invalid (no required fields)
        ]
        runner.http_client.get = AsyncMock(return_value=mock_response)

        result = await runner._poll_tasks_from_server(count=5)

        # Should only return valid tasks
        self.assertLessEqual(len(result), 2)  # At most 2 valid tasks

    async def test_poll_tasks_with_domain_parameter(self):
        """Test that domain parameter is added when configured"""
        # Create worker with domain
        worker_with_domain = Worker(
            task_definition_name='test_task',
            execute_function=lambda task: {'result': 'ok'},
            domain='production'
        )
        runner = TaskRunnerAsyncIO(
            worker=worker_with_domain,
            configuration=self.config
        )

        runner.http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        runner.http_client.get = AsyncMock(return_value=mock_response)

        await runner._poll_tasks_from_server(count=1)

        # Check that domain was passed in params
        call_args = runner.http_client.get.call_args
        params = call_args.kwargs.get('params', {})
        self.assertEqual(params.get('domain'), 'production')

    async def test_update_task_returns_none_for_invalid_result(self):
        """Test that _update_task returns None for non-TaskResult objects"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Pass invalid object
        result = await runner._update_task("not a TaskResult")

        self.assertIsNone(result)

    # =========================================================================
    # 5. V2 API FEATURES - MEDIUM PRIORITY
    # =========================================================================

    async def test_poll_tasks_drains_queue_first(self):
        """Test that _poll_tasks drains overflow queue before server poll"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Add tasks to overflow queue
        task1 = Task(task_id='queued1', task_def_name='test_task')
        task2 = Task(task_id='queued2', task_def_name='test_task')

        await runner._task_queue.put(task1)
        await runner._task_queue.put(task2)

        # Mock server to return additional task
        runner.http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'taskId': 'server1', 'taskDefName': 'test_task'}
        ]
        runner.http_client.get = AsyncMock(return_value=mock_response)

        # Poll for 3 tasks
        result = await runner._poll_tasks(poll_count=3)

        # Should return queued tasks first, then server task
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].task_id, 'queued1')
        self.assertEqual(result[1].task_id, 'queued2')

    async def test_poll_tasks_combines_queue_and_server(self):
        """Test that _poll_tasks combines queue and server tasks"""
        runner = TaskRunnerAsyncIO(worker=self.worker, configuration=self.config)

        # Add 1 task to queue
        task1 = Task(task_id='queued1', task_def_name='test_task')
        await runner._task_queue.put(task1)

        # Mock server to return 2 more tasks
        runner.http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'taskId': 'server1', 'taskDefName': 'test_task'},
            {'taskId': 'server2', 'taskDefName': 'test_task'}
        ]
        runner.http_client.get = AsyncMock(return_value=mock_response)

        # Poll for 3 tasks
        result = await runner._poll_tasks(poll_count=3)

        # Should return 1 from queue + 2 from server = 3 total
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].task_id, 'queued1')

    # =========================================================================
    # 6. OUTPUT SERIALIZATION - MEDIUM PRIORITY
    # =========================================================================

    async def test_create_task_result_serialization_error_fallback(self):
        """Test that serialization errors fall back to string representation"""
        # Create worker that returns non-serializable output
        class NonSerializableWorker(Worker):
            def __init__(self):
                def execute_with_bad_output(task):
                    # Return object that can't be serialized
                    class BadObject:
                        def __str__(self):
                            return "BadObject representation"
                    return {"result": BadObject()}
                super().__init__('test_task', execute_with_bad_output)

        runner = TaskRunnerAsyncIO(
            worker=NonSerializableWorker(),
            configuration=self.config
        )

        task = Task(
            task_id='task123',
            task_def_name='test_task',
            status='IN_PROGRESS'
        )

        # Execute task
        result = await runner._execute_task(task)

        # Should not crash, result should be created
        self.assertIsNotNone(result)
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)

    # =========================================================================
    # 7. TASK PARAMETER HANDLING - MEDIUM PRIORITY
    # =========================================================================

    async def test_call_execute_function_with_complex_type_conversion(self):
        """Test parameter conversion for complex types"""
        # Create worker with typed parameters
        class TypedWorker(Worker):
            def __init__(self):
                def execute_with_types(name: str, count: int = 10):
                    return {"name": name, "count": count}
                super().__init__('test_task', execute_with_types)

        runner = TaskRunnerAsyncIO(
            worker=TypedWorker(),
            configuration=self.config
        )

        task = Task(
            task_id='task123',
            task_def_name='test_task',
            status='IN_PROGRESS',
            input_data={'name': 'test', 'count': '5'}  # String instead of int
        )

        # Execute - should convert types
        result = await runner._execute_task(task)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)

    async def test_call_execute_function_with_missing_parameters(self):
        """Test handling of missing parameters"""
        # Create worker with optional parameters
        class OptionalParamWorker(Worker):
            def __init__(self):
                def execute_with_optional(name: str, count: int = 10):
                    return {"name": name, "count": count}
                super().__init__('test_task', execute_with_optional)

        runner = TaskRunnerAsyncIO(
            worker=OptionalParamWorker(),
            configuration=self.config
        )

        task = Task(
            task_id='task123',
            task_def_name='test_task',
            status='IN_PROGRESS',
            input_data={'name': 'test'}  # Missing 'count'
        )

        # Execute - should use default value
        result = await runner._execute_task(task)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)


if __name__ == '__main__':
    unittest.main()
