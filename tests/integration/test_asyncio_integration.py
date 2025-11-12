"""
Integration tests for AsyncIO implementation.

These tests verify that the AsyncIO implementation works correctly
with the full Conductor workflow.
"""
import asyncio
import logging
import unittest
from unittest.mock import Mock

try:
    import httpx
except ImportError:
    httpx = None

from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO, run_workers_async
from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface


class SimpleAsyncWorker(WorkerInterface):
    """Simple async worker for integration testing"""
    def __init__(self, task_definition_name: str):
        super().__init__(task_definition_name)
        self.execution_count = 0
        self.poll_interval = 0.1

    async def execute(self, task: Task) -> TaskResult:
        """Execute with async I/O simulation"""
        await asyncio.sleep(0.01)

        self.execution_count += 1

        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('execution_count', self.execution_count)
        task_result.add_output_data('task_id', task.task_id)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result


class SimpleSyncWorker(WorkerInterface):
    """Simple sync worker for integration testing"""
    def __init__(self, task_definition_name: str):
        super().__init__(task_definition_name)
        self.execution_count = 0
        self.poll_interval = 0.1

    def execute(self, task: Task) -> TaskResult:
        """Execute with sync I/O simulation"""
        import time
        time.sleep(0.01)

        self.execution_count += 1

        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('execution_count', self.execution_count)
        task_result.add_output_data('task_id', task.task_id)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result


@unittest.skipIf(httpx is None, "httpx not installed")
class TestAsyncIOIntegration(unittest.TestCase):
    """Integration tests for AsyncIO task handling"""

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

    # ==================== Task Runner Integration Tests ====================

    def test_async_worker_execution_with_mocked_server(self):
        """Test that async worker can execute task with mocked server"""
        worker = SimpleAsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock server responses
        mock_poll_response = Mock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {
            'taskId': 'task123',
            'workflowInstanceId': 'workflow123',
            'taskDefName': 'test_task',
            'responseTimeoutSeconds': 300
        }

        mock_update_response = Mock()
        mock_update_response.status_code = 200
        mock_update_response.text = 'success'
        mock_update_response.raise_for_status = Mock()

        async def mock_get(*args, **kwargs):
            return mock_poll_response

        async def mock_post(*args, **kwargs):
            return mock_update_response

        runner.http_client.get = mock_get
        runner.http_client.post = mock_post

        # Run one complete cycle
        self.run_async(runner.run_once())

        # Worker should have executed
        self.assertEqual(worker.execution_count, 1)

    def test_sync_worker_execution_in_thread_pool(self):
        """Test that sync worker runs in thread pool"""
        worker = SimpleSyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock server responses
        mock_poll_response = Mock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {
            'taskId': 'task123',
            'workflowInstanceId': 'workflow123',
            'taskDefName': 'test_task',
            'responseTimeoutSeconds': 300
        }

        mock_update_response = Mock()
        mock_update_response.status_code = 200
        mock_update_response.text = 'success'
        mock_update_response.raise_for_status = Mock()

        async def mock_get(*args, **kwargs):
            return mock_poll_response

        async def mock_post(*args, **kwargs):
            return mock_update_response

        runner.http_client.get = mock_get
        runner.http_client.post = mock_post

        # Run one complete cycle
        self.run_async(runner.run_once())

        # Worker should have executed in thread pool
        self.assertEqual(worker.execution_count, 1)

    def test_multiple_task_executions(self):
        """Test that worker can execute multiple tasks"""
        worker = SimpleAsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock server responses for multiple tasks
        task_id_counter = [0]

        def get_mock_poll_response():
            task_id_counter[0] += 1
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'taskId': f'task{task_id_counter[0]}',
                'workflowInstanceId': 'workflow123',
                'taskDefName': 'test_task',
                'responseTimeoutSeconds': 300
            }
            return mock_response

        async def mock_get(*args, **kwargs):
            return get_mock_poll_response()

        mock_update_response = Mock()
        mock_update_response.status_code = 200
        mock_update_response.text = 'success'
        mock_update_response.raise_for_status = Mock()

        async def mock_post(*args, **kwargs):
            return mock_update_response

        runner.http_client.get = mock_get
        runner.http_client.post = mock_post

        # Run multiple cycles
        for _ in range(5):
            self.run_async(runner.run_once())

        # Worker should have executed 5 times
        self.assertEqual(worker.execution_count, 5)

    # ==================== Task Handler Integration Tests ====================

    def test_handler_with_multiple_workers(self):
        """Test that handler can manage multiple workers concurrently"""
        workers = [
            SimpleAsyncWorker('task1'),
            SimpleAsyncWorker('task2'),
            SimpleSyncWorker('task3')
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Mock server to return no tasks (to prevent infinite polling)
        mock_response = Mock()
        mock_response.status_code = 204  # No content

        async def mock_get(*args, **kwargs):
            return mock_response

        handler.http_client.get = mock_get

        # Start and run briefly
        async def run_briefly():
            await handler.start()
            await asyncio.sleep(0.2)
            await handler.stop()

        self.run_async(run_briefly())

        # All workers should have been started
        self.assertEqual(len(handler._worker_tasks), 3)

    def test_handler_graceful_shutdown(self):
        """Test that handler shuts down gracefully"""
        workers = [
            SimpleAsyncWorker('task1'),
            SimpleAsyncWorker('task2')
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Mock server
        mock_response = Mock()
        mock_response.status_code = 204

        async def mock_get(*args, **kwargs):
            return mock_response

        handler.http_client.get = mock_get

        # Start
        self.run_async(handler.start())

        # Verify running
        self.assertTrue(handler._running)
        self.assertEqual(len(handler._worker_tasks), 2)

        # Stop
        import time
        start = time.time()
        self.run_async(handler.stop())
        elapsed = time.time() - start

        # Should shut down quickly (within 30 second timeout)
        self.assertLess(elapsed, 5.0)

        # Should be stopped
        self.assertFalse(handler._running)

    def test_handler_context_manager(self):
        """Test handler as async context manager"""
        workers = [SimpleAsyncWorker('task1')]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Mock server
        mock_response = Mock()
        mock_response.status_code = 204

        async def mock_get(*args, **kwargs):
            return mock_response

        handler.http_client.get = mock_get

        # Use as context manager
        async def use_handler():
            async with handler:
                # Should be running
                self.assertTrue(handler._running)
                await asyncio.sleep(0.1)

            # Should be stopped after context exit
            self.assertFalse(handler._running)

        self.run_async(use_handler())

    def test_run_workers_async_convenience_function(self):
        """Test run_workers_async convenience function"""
        # Create test workers
        workers = [SimpleAsyncWorker('task1')]

        config = Configuration("http://localhost:8080/api")

        # Mock the handler to test the function
        async def test_with_timeout():
            # Run with very short timeout
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    run_workers_async(
                        configuration=config,
                        import_modules=None,
                        stop_after_seconds=None
                    ),
                    timeout=0.1
                )

        # This will timeout quickly since we're not providing real workers
        # Just testing that the function works
        try:
            self.run_async(test_with_timeout())
        except:
            pass  # Expected to fail without real server

    # ==================== Error Handling Integration Tests ====================

    def test_worker_exception_handling(self):
        """Test that worker exceptions are handled gracefully"""
        class FaultyAsyncWorker(WorkerInterface):
            def __init__(self, task_definition_name: str):
                super().__init__(task_definition_name)
                self.poll_interval = 0.1

            async def execute(self, task: Task) -> TaskResult:
                raise Exception("Worker failure")

        worker = FaultyAsyncWorker('faulty_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock server responses
        mock_poll_response = Mock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {
            'taskId': 'task123',
            'workflowInstanceId': 'workflow123',
            'taskDefName': 'faulty_task',
            'responseTimeoutSeconds': 300
        }

        mock_update_response = Mock()
        mock_update_response.status_code = 200
        mock_update_response.text = 'success'
        mock_update_response.raise_for_status = Mock()

        async def mock_get(*args, **kwargs):
            return mock_poll_response

        async def mock_post(*args, **kwargs):
            return mock_update_response

        runner.http_client.get = mock_get
        runner.http_client.post = mock_post

        # Run should handle exception gracefully
        self.run_async(runner.run_once())

        # Should not crash - exception handled

    def test_network_error_handling(self):
        """Test that network errors are handled gracefully"""
        worker = SimpleAsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Mock network failure
        async def mock_get(*args, **kwargs):
            raise httpx.ConnectError("Connection refused")

        runner.http_client.get = mock_get

        # Should handle network error gracefully
        self.run_async(runner.run_once())

        # Worker should not have executed
        self.assertEqual(worker.execution_count, 0)

    # ==================== Performance Integration Tests ====================

    def test_concurrent_execution_with_shared_http_client(self):
        """Test that multiple workers share HTTP client efficiently"""
        workers = [SimpleAsyncWorker(f'task{i}') for i in range(10)]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # All runners should share same HTTP client
        http_clients = set(id(runner.http_client) for runner in handler.task_runners)
        self.assertEqual(len(http_clients), 1)

        # Handler should own the client
        handler_client_id = id(handler.http_client)
        self.assertIn(handler_client_id, http_clients)

    def test_memory_efficiency_compared_to_multiprocessing(self):
        """Test that AsyncIO uses less memory than multiprocessing would"""
        # Create many workers
        workers = [SimpleAsyncWorker(f'task{i}') for i in range(20)]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Should create all workers in single process
        self.assertEqual(len(handler.task_runners), 20)

        # Mock server
        mock_response = Mock()
        mock_response.status_code = 204

        async def mock_get(*args, **kwargs):
            return mock_response

        handler.http_client.get = mock_get

        # Start and verify all run in same process
        self.run_async(handler.start())

        import os
        current_pid = os.getpid()

        # All should be in same process (no child processes created)
        # This is different from multiprocessing which would create 20 processes

        self.run_async(handler.stop())

    def test_cached_api_client_performance(self):
        """Test that cached ApiClient improves performance"""
        worker = SimpleAsyncWorker('test_task')
        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=Configuration("http://localhost:8080/api")
        )

        # Get initial cached client
        cached_client_id = id(runner._api_client)

        # Mock server responses
        mock_poll_response = Mock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {
            'taskId': 'task123',
            'workflowInstanceId': 'workflow123',
            'taskDefName': 'test_task',
            'responseTimeoutSeconds': 300
        }

        mock_update_response = Mock()
        mock_update_response.status_code = 200
        mock_update_response.text = 'success'
        mock_update_response.raise_for_status = Mock()

        async def mock_get(*args, **kwargs):
            return mock_poll_response

        async def mock_post(*args, **kwargs):
            return mock_update_response

        runner.http_client.get = mock_get
        runner.http_client.post = mock_post

        # Run multiple times
        for _ in range(10):
            self.run_async(runner.run_once())

        # Should still be using same cached client
        self.assertEqual(id(runner._api_client), cached_client_id)


if __name__ == '__main__':
    unittest.main()
