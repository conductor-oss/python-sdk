"""Tests for async task execution flow in TaskRunner."""
import asyncio
import logging
import time
import unittest
from unittest.mock import patch, Mock

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker import Worker


class TestTaskRunnerAsync(unittest.TestCase):
    """Test async task execution in TaskRunner."""

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_async_task_execution_and_completion(self):
        """Test that async tasks are executed and their results are captured."""

        # Define an async worker function
        async def async_worker_func(message: str = 'test') -> dict:
            """Simple async worker for testing."""
            await asyncio.sleep(0.1)  # Simulate async work
            return {'result': message.upper()}

        # Create worker with async function
        worker = Worker(
            task_definition_name='async_test_task',
            execute_function=async_worker_func,
            domain=None,
            poll_interval=100,
            thread_count=2
        )

        # Create mock task client
        mock_task_client = Mock()
        mock_task_client.batch_poll.return_value = []
        mock_task_client.update_task.return_value = "OK"

        # Create task runner
        task_runner = TaskRunner(
            configuration=Configuration(),
            worker=worker
        )
        # Override task_client with mock
        task_runner.task_client = mock_task_client

        # Create a test task
        test_task = Task(
            task_id='test-async-123',
            task_def_name='async_test_task',
            workflow_instance_id='workflow-456',
            input_data={'message': 'hello'}
        )

        # Execute the task - should return None for async tasks
        result = worker.execute(test_task)
        self.assertIsNone(result, "Async task should return None immediately")

        # Verify task is tracked as pending
        self.assertEqual(len(worker._pending_async_tasks), 1)
        self.assertIn('test-async-123', worker._pending_async_tasks)

        # Wait for async task to complete
        time.sleep(0.2)

        # Check for completed async tasks
        completed = worker.check_completed_async_tasks()
        self.assertEqual(len(completed), 1, "Should have 1 completed async task")

        # Verify completed task structure
        task_id, task_result, submit_time, original_task = completed[0]
        self.assertEqual(task_id, 'test-async-123')
        self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(task_result.output_data, {'result': 'HELLO'})
        self.assertEqual(task_result.task_id, 'test-async-123')
        self.assertIsInstance(submit_time, float)
        self.assertEqual(original_task.task_id, 'test-async-123')

        # Verify execution time is reasonable (should be ~0.1s + overhead)
        execution_time = time.time() - submit_time
        self.assertGreater(execution_time, 0.1, "Execution time should be at least 0.1s")
        self.assertLess(execution_time, 1.0, "Execution time should be less than 1s")

        # Verify pending tasks list is now empty
        self.assertEqual(len(worker._pending_async_tasks), 0)

    def test_async_task_completion_via_run_once(self):
        """Test that TaskRunner.run_once() properly checks and updates completed async tasks."""

        # Define an async worker function
        async def async_worker_func(value: int = 1) -> dict:
            """Simple async worker for testing."""
            await asyncio.sleep(0.05)
            return {'result': value * 2}

        # Create worker with async function
        worker = Worker(
            task_definition_name='async_calc_task',
            execute_function=async_worker_func,
            domain=None,
            poll_interval=100,
            thread_count=2
        )

        # Create mock task client
        mock_task_client = Mock()
        mock_task_client.batch_poll.return_value = []
        mock_task_client.update_task.return_value = "OK"

        # Create task runner
        task_runner = TaskRunner(
            configuration=Configuration(),
            worker=worker
        )
        task_runner.task_client = mock_task_client

        # Create and execute a test task
        test_task = Task(
            task_id='calc-task-789',
            task_def_name='async_calc_task',
            workflow_instance_id='workflow-999',
            input_data={'value': 21}
        )

        # Execute the task
        result = worker.execute(test_task)
        self.assertIsNone(result)

        # Wait for async task to complete
        time.sleep(0.1)

        # Call run_once - should check for completed async tasks and update them
        task_runner.run_once()

        # Verify update_task was called with correct result
        self.assertTrue(mock_task_client.update_task.called)

        # Get the TaskResult that was passed to update_task
        call_args = mock_task_client.update_task.call_args
        task_result = call_args.kwargs['body']

        self.assertEqual(task_result.task_id, 'calc-task-789')
        self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(task_result.output_data, {'result': 42})

    def test_multiple_async_tasks_concurrent_execution(self):
        """Test that multiple async tasks can be executed concurrently."""

        # Define an async worker function
        async def async_worker_func(delay: float = 0.1) -> dict:
            """Async worker with configurable delay."""
            start = time.time()
            await asyncio.sleep(delay)
            return {'delay': delay, 'elapsed': time.time() - start}

        # Create worker with async function
        worker = Worker(
            task_definition_name='async_delay_task',
            execute_function=async_worker_func,
            domain=None,
            poll_interval=100,
            thread_count=5
        )

        # Execute 3 tasks with different delays
        tasks = []
        for i in range(3):
            task = Task(
                task_id=f'task-{i}',
                task_def_name='async_delay_task',
                workflow_instance_id='workflow-123',
                input_data={'delay': 0.1}
            )
            result = worker.execute(task)
            self.assertIsNone(result)
            tasks.append(task)

        # Verify all tasks are pending
        self.assertEqual(len(worker._pending_async_tasks), 3)

        # Wait for all tasks to complete
        time.sleep(0.2)

        # Check for completed tasks
        completed = worker.check_completed_async_tasks()
        self.assertEqual(len(completed), 3, "All 3 tasks should be completed")

        # Verify all tasks completed successfully
        for task_id, task_result, submit_time, original_task in completed:
            self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
            self.assertIn('elapsed', task_result.output_data)
            self.assertGreater(task_result.output_data['elapsed'], 0.1)

    def test_sync_task_not_affected_by_async_logic(self):
        """Test that synchronous tasks still work correctly."""

        # Define a sync worker function
        def sync_worker_func(value: int = 1) -> dict:
            """Simple sync worker for testing."""
            return {'result': value * 3}

        # Create worker with sync function
        worker = Worker(
            task_definition_name='sync_calc_task',
            execute_function=sync_worker_func,
            domain=None,
            poll_interval=100,
            thread_count=2
        )

        # Create a test task
        test_task = Task(
            task_id='sync-task-123',
            task_def_name='sync_calc_task',
            workflow_instance_id='workflow-456',
            input_data={'value': 7}
        )

        # Execute the task - should return TaskResult immediately
        result = worker.execute(test_task)
        self.assertIsNotNone(result, "Sync task should return result immediately")
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {'result': 21})

        # Verify no pending async tasks
        self.assertEqual(len(worker._pending_async_tasks), 0)

        # Check for completed async tasks should return empty list
        completed = worker.check_completed_async_tasks()
        self.assertEqual(len(completed), 0)


if __name__ == '__main__':
    unittest.main()
