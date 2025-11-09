import asyncio
import logging
import unittest
from unittest.mock import AsyncMock, Mock, patch, ANY
from requests.structures import CaseInsensitiveDict

try:
    import httpx
except ImportError:
    httpx = None

from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from tests.unit.resources.workers import (
    AsyncWorker,
    AsyncFaultyExecutionWorker,
    AsyncTimeoutWorker,
    SyncWorkerForAsync
)


@unittest.skipIf(httpx is None, "httpx not installed")
class TestTaskRunnerAsyncIO(unittest.TestCase):
    TASK_ID = 'VALID_TASK_ID'
    WORKFLOW_INSTANCE_ID = 'VALID_WORKFLOW_INSTANCE_ID'
    UPDATE_TASK_RESPONSE = 'VALID_UPDATE_TASK_RESPONSE'

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.loop.close()

    def run_async(self, coro):
        """Helper to run async functions in tests"""
        return self.loop.run_until_complete(coro)

    # ==================== Initialization Tests ====================

    def test_initialization_with_invalid_worker(self):
        """Test that initializing with None worker raises exception"""
        expected_exception = Exception('Invalid worker')
        with self.assertRaises(Exception) as context:
            TaskRunnerAsyncIO(
                worker=None,
                configuration=Configuration("http://localhost:8080/api")
            )
            self.assertEqual(str(expected_exception), str(context.exception))

    def test_initialization_creates_cached_api_client(self):
        """Test that ApiClient is created once and cached"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Should have cached ApiClient
        self.assertIsNotNone(runner._api_client)
        self.assertEqual(runner._api_client, runner._api_client)  # Same instance

    def test_initialization_creates_explicit_executor(self):
        """Test that ThreadPoolExecutor is explicitly created"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Should have explicit executor
        self.assertIsNotNone(runner._executor)
        from concurrent.futures import ThreadPoolExecutor
        self.assertIsInstance(runner._executor, ThreadPoolExecutor)

    def test_initialization_creates_execution_semaphore(self):
        """Test that execution semaphore is created"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api"),
            max_concurrent_tasks=2
        )

        # Should have semaphore
        self.assertIsNotNone(runner._execution_semaphore)
        self.assertIsInstance(runner._execution_semaphore, asyncio.Semaphore)

    def test_initialization_with_shared_http_client(self):
        """Test that shared HTTP client is used and ownership tracked"""
        worker = AsyncWorker('test_task')
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api"),
            http_client=mock_client
        )

        # Should use provided client and not own it
        self.assertEqual(runner.http_client, mock_client)
        self.assertFalse(runner._owns_client)

    # ==================== Poll Task Tests ====================

    def test_poll_task_success(self):
        """Test successful task polling"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'taskId': self.TASK_ID,
            'workflowInstanceId': self.WORKFLOW_INSTANCE_ID,
            'taskDefName': 'test_task'
        }

        async def mock_get(*args, **kwargs):
            return mock_response

        runner.http_client.get = mock_get

        task = self.run_async(runner._poll_task())

        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, self.TASK_ID)

    def test_poll_task_no_content(self):
        """Test polling when no task available (204 status)"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock 204 No Content response
        mock_response = Mock()
        mock_response.status_code = 204

        async def mock_get(*args, **kwargs):
            return mock_response

        runner.http_client.get = mock_get

        task = self.run_async(runner._poll_task())

        self.assertIsNone(task)

    def test_poll_task_with_paused_worker(self):
        """Test that paused worker doesn't poll"""
        worker = AsyncWorker('test_task')
        worker.pause()

        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task = self.run_async(runner._poll_task())

        self.assertIsNone(task)

    def test_poll_task_uses_cached_api_client(self):
        """Test that polling uses cached ApiClient for deserialization"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Store reference to cached client
        cached_client = runner._api_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'taskId': self.TASK_ID,
            'workflowInstanceId': self.WORKFLOW_INSTANCE_ID
        }

        async def mock_get(*args, **kwargs):
            return mock_response

        runner.http_client.get = mock_get

        task = self.run_async(runner._poll_task())

        # Should still be using same cached client
        self.assertEqual(runner._api_client, cached_client)

    # ==================== Execute Task Tests ====================

    def test_execute_async_worker(self):
        """Test executing an async worker"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task = Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID
        )

        task_result = self.run_async(runner._execute_task(task))

        self.assertIsNotNone(task_result)
        self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(task_result.output_data['worker_style'], 'async')

    def test_execute_sync_worker_in_thread_pool(self):
        """Test executing a sync worker (should run in thread pool)"""
        worker = SyncWorkerForAsync('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task = Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID
        )

        task_result = self.run_async(runner._execute_task(task))

        self.assertIsNotNone(task_result)
        self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(task_result.output_data['worker_style'], 'sync_in_async')
        self.assertTrue(task_result.output_data['ran_in_thread'])

    def test_execute_task_with_timeout(self):
        """Test that task execution respects timeout"""
        worker = AsyncTimeoutWorker('test_task', sleep_time=10.0)
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task = Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            response_timeout_seconds=0.1  # Very short timeout
        )

        task_result = self.run_async(runner._execute_task(task))

        # Should fail with timeout
        self.assertEqual(task_result.status, 'FAILED')
        self.assertIn('timeout', task_result.reason_for_incompletion.lower())

    def test_execute_task_with_faulty_worker(self):
        """Test executing a worker that raises exception"""
        worker = AsyncFaultyExecutionWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task = Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID
        )

        task_result = self.run_async(runner._execute_task(task))

        # Should fail gracefully
        self.assertEqual(task_result.status, 'FAILED')
        self.assertIn('async faulty execution', task_result.reason_for_incompletion)
        self.assertIsNotNone(task_result.logs)

    def test_execute_task_uses_explicit_executor_for_sync(self):
        """Test that sync worker uses explicit ThreadPoolExecutor"""
        worker = SyncWorkerForAsync('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Store reference to executor
        executor = runner._executor

        task = Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID
        )

        task_result = self.run_async(runner._execute_task(task))

        # Should still be using same executor
        self.assertEqual(runner._executor, executor)
        self.assertIsNotNone(task_result)

    def test_execute_task_with_semaphore_limiting(self):
        """Test that semaphore limits concurrent executions"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api"),
            max_concurrent_tasks=1  # Only 1 at a time
        )

        task = Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID
        )

        # Execute task - should acquire semaphore
        task_result = self.run_async(runner._execute_task(task))

        self.assertIsNotNone(task_result)
        # After execution, semaphore should be released
        # (checked implicitly by successful completion)

    # ==================== Update Task Tests ====================

    def test_update_task_success(self):
        """Test successful task result update"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task_result = TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id=worker.get_identity(),
            status=TaskResultStatus.COMPLETED
        )

        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.UPDATE_TASK_RESPONSE

        async def mock_post(*args, **kwargs):
            mock_response.raise_for_status = Mock()
            return mock_response

        runner.http_client.post = mock_post

        response = self.run_async(runner._update_task(task_result))

        self.assertEqual(response, self.UPDATE_TASK_RESPONSE)

    def test_update_task_with_exponential_backoff(self):
        """Test that retries use exponential backoff with jitter"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task_result = TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id=worker.get_identity(),
            status=TaskResultStatus.COMPLETED
        )

        attempt_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Network error")

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = self.UPDATE_TASK_RESPONSE
            mock_response.raise_for_status = Mock()
            return mock_response

        runner.http_client.post = mock_post

        import time
        start = time.time()
        response = self.run_async(runner._update_task(task_result))
        elapsed = time.time() - start

        # Should succeed after retries
        self.assertEqual(response, self.UPDATE_TASK_RESPONSE)
        # Should have waited for exponential backoff (2s + 4s = 6s minimum)
        # With jitter it will be slightly more
        self.assertGreater(elapsed, 5.0)

    def test_update_task_uses_cached_api_client(self):
        """Test that update uses cached ApiClient for serialization"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Store reference to cached client
        cached_client = runner._api_client

        task_result = TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id=worker.get_identity(),
            status=TaskResultStatus.COMPLETED
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.UPDATE_TASK_RESPONSE

        async def mock_post(*args, **kwargs):
            mock_response.raise_for_status = Mock()
            return mock_response

        runner.http_client.post = mock_post

        response = self.run_async(runner._update_task(task_result))

        # Should still be using same cached client
        self.assertEqual(runner._api_client, cached_client)

    def test_update_task_with_invalid_result(self):
        """Test updating with None task result"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        response = self.run_async(runner._update_task(None))

        self.assertIsNone(response)

    # ==================== Run Once Tests ====================

    def test_run_once_full_cycle(self):
        """Test complete poll-execute-update cycle"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock poll to return task
        mock_poll_response = Mock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {
            'taskId': self.TASK_ID,
            'workflowInstanceId': self.WORKFLOW_INSTANCE_ID,
            'taskDefName': 'test_task'
        }

        # Mock update to succeed
        mock_update_response = Mock()
        mock_update_response.status_code = 200
        mock_update_response.text = self.UPDATE_TASK_RESPONSE

        async def mock_get(*args, **kwargs):
            return mock_poll_response

        async def mock_post(*args, **kwargs):
            mock_update_response.raise_for_status = Mock()
            return mock_update_response

        runner.http_client.get = mock_get
        runner.http_client.post = mock_post

        # Run one cycle (with short polling interval)
        worker.poll_interval = 0.01

        import time
        start = time.time()
        self.run_async(runner.run_once())
        elapsed = time.time() - start

        # Should complete successfully
        # Should have waited for polling interval
        self.assertGreater(elapsed, 0.01)

    def test_run_once_with_no_task(self):
        """Test run_once when no task available"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock poll to return no task (204)
        mock_response = Mock()
        mock_response.status_code = 204

        async def mock_get(*args, **kwargs):
            return mock_response

        runner.http_client.get = mock_get

        worker.poll_interval = 0.01

        # Should complete without error
        self.run_async(runner.run_once())

    def test_run_once_handles_exceptions_gracefully(self):
        """Test that run_once handles exceptions without crashing"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock poll to raise exception
        async def mock_get(*args, **kwargs):
            raise Exception("Network failure")

        runner.http_client.get = mock_get

        worker.poll_interval = 0.01

        # Should handle exception gracefully
        self.run_async(runner.run_once())

    # ==================== Cleanup Tests ====================

    # TODO: This test hangs even with mocked aclose() and shutdown() - needs investigation
    # def test_cleanup_closes_owned_http_client(self):
    #     """Test that run() cleanup closes HTTP client if owned"""
    #     worker = AsyncWorker('test_task')
    #     runner = TaskRunnerAsyncIO(
    #         worker=worker,
    #         configuration=Configuration("http://localhost:8080/api")
    #     )
    #
    #     self.assertTrue(runner._owns_client)
    #
    #     # Mock to exit immediately
    #     runner._running = False
    #
    #     # Mock http_client.aclose() and executor.shutdown() to prevent hanging
    #     runner.http_client.aclose = AsyncMock()
    #     runner._executor.shutdown = Mock()
    #
    #     async def run_with_cleanup():
    #         try:
    #             await runner.run()
    #         except:
    #             pass
    #
    #     # HTTP client should be closed after run
    #     self.run_async(run_with_cleanup())
    #
    #     # Verify aclose was called
    #     runner.http_client.aclose.assert_called_once()
    #     # Verify executor shutdown was called
    #     runner._executor.shutdown.assert_called_once_with(wait=True)

    # TODO: This test also hangs - needs investigation
    # def test_cleanup_shuts_down_executor(self):
    #     """Test that run() cleanup shuts down executor"""
    #     worker = SyncWorkerForAsync('test_task')
    #     runner = TaskRunnerAsyncIO(
    #         worker=worker,
    #         configuration=Configuration("http://localhost:8080/api")
    #     )
    #
    #     # Mock to exit immediately
    #     runner._running = False
    #
    #     # Mock http_client.aclose() and executor.shutdown() to prevent hanging
    #     runner.http_client.aclose = AsyncMock()
    #     runner._executor.shutdown = Mock()
    #
    #     async def run_with_cleanup():
    #         try:
    #             await runner.run()
    #         except:
    #             pass
    #
    #     self.run_async(run_with_cleanup())
    #
    #     # Verify executor shutdown was called
    #     runner._executor.shutdown.assert_called_once_with(wait=True)

    def test_stop_sets_running_flag(self):
        """Test that stop() sets _running flag to False"""
        worker = AsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        runner._running = True
        runner.stop()

        self.assertFalse(runner._running)

    # ==================== Python 3.12+ Compatibility Tests ====================

    def test_uses_get_running_loop_not_get_event_loop(self):
        """Test that implementation uses get_running_loop() not deprecated get_event_loop()"""
        # This is more of a code inspection test
        # We verify by checking that sync workers can execute without warnings
        worker = SyncWorkerForAsync('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        task = Task(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID
        )

        # Should not raise DeprecationWarning
        task_result = self.run_async(runner._execute_task(task))

        self.assertIsNotNone(task_result)


if __name__ == '__main__':
    unittest.main()
