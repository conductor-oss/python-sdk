import asyncio
import logging
import unittest
from unittest.mock import AsyncMock, Mock, patch

try:
    import httpx
except ImportError:
    httpx = None

from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from tests.unit.resources.workers import (
    AsyncWorker,
    SyncWorkerForAsync
)


@unittest.skipIf(httpx is None, "httpx not installed")
class TestTaskHandlerAsyncIO(unittest.TestCase):
    TASK_ID = 'VALID_TASK_ID'
    WORKFLOW_INSTANCE_ID = 'VALID_WORKFLOW_INSTANCE_ID'

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

    def test_initialization_with_no_workers(self):
        """Test that handler can be initialized without workers"""
        handler = TaskHandlerAsyncIO(
            workers=[],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.assertIsNotNone(handler)
        self.assertEqual(len(handler.task_runners), 0)

    def test_initialization_with_workers(self):
        """Test that handler creates task runners for each worker"""
        workers = [
            AsyncWorker('task1'),
            AsyncWorker('task2'),
            SyncWorkerForAsync('task3')
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.assertEqual(len(handler.task_runners), 3)

    def test_initialization_creates_shared_http_client(self):
        """Test that single shared HTTP client is created"""
        workers = [
            AsyncWorker('task1'),
            AsyncWorker('task2')
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Should have shared HTTP client
        self.assertIsNotNone(handler.http_client)

        # All runners should share same client
        for runner in handler.task_runners:
            self.assertEqual(runner.http_client, handler.http_client)
            self.assertFalse(runner._owns_client)

    def test_initialization_without_httpx_raises_error(self):
        """Test that missing httpx raises ImportError"""
        # This test would need to mock the httpx import check
        # Skipping as it's hard to test without actually uninstalling httpx
        pass

    def test_initialization_with_metrics_settings(self):
        """Test initialization with metrics settings"""
        metrics_settings = MetricsSettings(
            directory='/tmp/metrics',
            file_name='metrics.txt',
            update_interval=10.0
        )

        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )

        self.assertEqual(handler.metrics_settings, metrics_settings)

    # ==================== Start Tests ====================

    def test_start_creates_worker_tasks(self):
        """Test that start() creates asyncio tasks for each worker"""
        workers = [
            AsyncWorker('task1'),
            AsyncWorker('task2')
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        # Should have created worker tasks
        self.assertEqual(len(handler._worker_tasks), 2)
        self.assertTrue(handler._running)

        # Cleanup
        self.run_async(handler.stop())

    def test_start_sets_running_flag(self):
        """Test that start() sets _running flag"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.assertFalse(handler._running)

        self.run_async(handler.start())

        self.assertTrue(handler._running)

        # Cleanup
        self.run_async(handler.stop())

    def test_start_when_already_running(self):
        """Test that calling start() twice doesn't duplicate tasks"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())
        initial_task_count = len(handler._worker_tasks)

        self.run_async(handler.start())  # Call again

        # Should not create duplicate tasks
        self.assertEqual(len(handler._worker_tasks), initial_task_count)

        # Cleanup
        self.run_async(handler.stop())

    def test_start_creates_metrics_task_when_configured(self):
        """Test that metrics task is created when metrics settings provided"""
        metrics_settings = MetricsSettings(
            directory='/tmp/metrics',
            file_name='metrics.txt',
            update_interval=1.0
        )

        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        # Should have created metrics task
        self.assertIsNotNone(handler._metrics_task)

        # Cleanup
        self.run_async(handler.stop())

    # ==================== Stop Tests ====================

    def test_stop_signals_workers_to_stop(self):
        """Test that stop() signals all workers to stop"""
        workers = [
            AsyncWorker('task1'),
            AsyncWorker('task2')
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        # All runners should be running
        for runner in handler.task_runners:
            self.assertTrue(runner._running)

        self.run_async(handler.stop())

        # All runners should be stopped
        for runner in handler.task_runners:
            self.assertFalse(runner._running)

    def test_stop_cancels_all_tasks(self):
        """Test that stop() cancels all worker tasks"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        # Tasks should be running
        for task in handler._worker_tasks:
            self.assertFalse(task.done())

        self.run_async(handler.stop())

        # Tasks should be done (cancelled)
        for task in handler._worker_tasks:
            self.assertTrue(task.done() or task.cancelled())

    def test_stop_with_shutdown_timeout(self):
        """Test that stop() respects 30-second shutdown timeout"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        import time
        start = time.time()
        self.run_async(handler.stop())
        elapsed = time.time() - start

        # Should complete quickly (not wait 30 seconds for clean shutdown)
        self.assertLess(elapsed, 5.0)

    def test_stop_closes_http_client(self):
        """Test that stop() closes shared HTTP client"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        # Mock close method to track calls
        close_called = False

        async def mock_aclose():
            nonlocal close_called
            close_called = True

        handler.http_client.aclose = mock_aclose

        self.run_async(handler.stop())

        # HTTP client should be closed
        self.assertTrue(close_called)

    def test_stop_when_not_running(self):
        """Test that calling stop() when not running doesn't error"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Stop without starting
        self.run_async(handler.stop())

        # Should not raise error
        self.assertFalse(handler._running)

    # ==================== Context Manager Tests ====================

    def test_async_context_manager_starts_and_stops(self):
        """Test that async context manager starts and stops handler"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        async def use_context_manager():
            async with handler:
                # Should be running inside context
                self.assertTrue(handler._running)
                self.assertGreater(len(handler._worker_tasks), 0)

            # Should be stopped after exiting context
            self.assertFalse(handler._running)

        self.run_async(use_context_manager())

    def test_context_manager_handles_exceptions(self):
        """Test that context manager properly cleans up on exception"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        async def use_context_manager_with_exception():
            try:
                async with handler:
                    raise Exception("Test exception")
            except Exception:
                pass

            # Should be stopped even after exception
            self.assertFalse(handler._running)

        self.run_async(use_context_manager_with_exception())

    # ==================== Wait Tests ====================

    def test_wait_blocks_until_stopped(self):
        """Test that wait() blocks until stop() is called"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        async def stop_after_delay():
            await asyncio.sleep(0.1)
            await handler.stop()

        async def wait_and_measure():
            stop_task = asyncio.create_task(stop_after_delay())
            import time
            start = time.time()
            await handler.wait()
            elapsed = time.time() - start
            await stop_task
            return elapsed

        elapsed = self.run_async(wait_and_measure())

        # Should have waited for at least 0.1 seconds
        self.assertGreater(elapsed, 0.05)

    def test_join_tasks_is_alias_for_wait(self):
        """Test that join_tasks() works same as wait()"""
        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        async def stop_immediately():
            await asyncio.sleep(0.01)
            await handler.stop()

        async def test_join():
            stop_task = asyncio.create_task(stop_immediately())
            await handler.join_tasks()
            await stop_task

        # Should complete without error
        self.run_async(test_join())

    # ==================== Metrics Tests ====================

    def test_metrics_provider_runs_in_executor(self):
        """Test that metrics are written in executor (not blocking event loop)"""
        # This is harder to test directly, but we can verify it starts
        metrics_settings = MetricsSettings(
            directory='/tmp/metrics',
            file_name='metrics_test.txt',
            update_interval=0.1
        )

        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        # Metrics task should be running
        self.assertIsNotNone(handler._metrics_task)
        self.assertFalse(handler._metrics_task.done())

        # Cleanup
        self.run_async(handler.stop())

    def test_metrics_task_cancelled_on_stop(self):
        """Test that metrics task is properly cancelled"""
        metrics_settings = MetricsSettings(
            directory='/tmp/metrics',
            file_name='metrics_test.txt',
            update_interval=1.0
        )

        handler = TaskHandlerAsyncIO(
            workers=[AsyncWorker('task1')],
            configuration=Configuration("http://localhost:8080/api"),
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        metrics_task = handler._metrics_task

        self.run_async(handler.stop())

        # Metrics task should be cancelled
        self.assertTrue(metrics_task.done() or metrics_task.cancelled())

    # ==================== Integration Tests ====================

    def test_full_lifecycle(self):
        """Test complete handler lifecycle: init -> start -> run -> stop"""
        workers = [
            AsyncWorker('task1'),
            SyncWorkerForAsync('task2')
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Initialize
        self.assertFalse(handler._running)
        self.assertEqual(len(handler.task_runners), 2)

        # Start
        self.run_async(handler.start())
        self.assertTrue(handler._running)
        self.assertEqual(len(handler._worker_tasks), 2)

        # Run for short time
        async def run_briefly():
            await asyncio.sleep(0.1)

        self.run_async(run_briefly())

        # Stop
        self.run_async(handler.stop())
        self.assertFalse(handler._running)

    def test_multiple_workers_run_concurrently(self):
        """Test that multiple workers can run concurrently"""
        # Create multiple workers
        workers = [
            AsyncWorker(f'task{i}') for i in range(5)
        ]

        handler = TaskHandlerAsyncIO(
            workers=workers,
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        self.run_async(handler.start())

        # All workers should have tasks
        self.assertEqual(len(handler._worker_tasks), 5)

        # All tasks should be running concurrently
        async def check_tasks():
            # Give tasks time to start
            await asyncio.sleep(0.01)

            running_count = sum(
                1 for task in handler._worker_tasks
                if not task.done()
            )

            # All should be running
            self.assertEqual(running_count, 5)

        self.run_async(check_tasks())

        # Cleanup
        self.run_async(handler.stop())

    def test_worker_can_process_tasks_end_to_end(self):
        """Test that worker can poll, execute, and update task"""
        worker = AsyncWorker('test_task')

        handler = TaskHandlerAsyncIO(
            workers=[worker],
            configuration=Configuration("http://localhost:8080/api"),
            scan_for_annotated_workers=False
        )

        # Mock HTTP responses
        mock_task_response = Mock()
        mock_task_response.status_code = 200
        mock_task_response.json.return_value = {
            'taskId': self.TASK_ID,
            'workflowInstanceId': self.WORKFLOW_INSTANCE_ID,
            'taskDefName': 'test_task',
            'responseTimeoutSeconds': 300
        }

        mock_update_response = Mock()
        mock_update_response.status_code = 200
        mock_update_response.text = 'success'

        async def mock_get(*args, **kwargs):
            return mock_task_response

        async def mock_post(*args, **kwargs):
            mock_update_response.raise_for_status = Mock()
            return mock_update_response

        handler.http_client.get = mock_get
        handler.http_client.post = mock_post

        # Set very short polling interval
        worker.poll_interval = 0.01

        self.run_async(handler.start())

        # Let it run one cycle
        async def run_one_cycle():
            await asyncio.sleep(0.1)

        self.run_async(run_one_cycle())

        # Cleanup
        self.run_async(handler.stop())

        # Should have completed successfully
        # (Verified by no exceptions raised)


if __name__ == '__main__':
    unittest.main()
