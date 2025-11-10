"""
Tests for TaskContext functionality.
"""

import asyncio
import unittest
from unittest.mock import Mock, AsyncMock

from conductor.client.configuration.configuration import Configuration
from conductor.client.context.task_context import (
    TaskContext,
    get_task_context,
    _set_task_context,
    _clear_task_context
)
from conductor.client.http.models import Task, TaskResult
from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.worker.worker import Worker


class TestTaskContext(unittest.TestCase):
    """Test TaskContext basic functionality"""

    def setUp(self):
        self.task = Task()
        self.task.task_id = 'test-task-123'
        self.task.workflow_instance_id = 'test-workflow-456'
        self.task.task_def_name = 'test_task'
        self.task.input_data = {'key': 'value', 'count': 42}
        self.task.retry_count = 2
        self.task.poll_count = 5

        self.task_result = TaskResult(
            task_id='test-task-123',
            workflow_instance_id='test-workflow-456',
            worker_id='test-worker'
        )

    def tearDown(self):
        # Always clear context after each test
        _clear_task_context()

    def test_context_getters(self):
        """Test basic getter methods"""
        ctx = _set_task_context(self.task, self.task_result)

        self.assertEqual(ctx.get_task_id(), 'test-task-123')
        self.assertEqual(ctx.get_workflow_instance_id(), 'test-workflow-456')
        self.assertEqual(ctx.get_task_def_name(), 'test_task')
        self.assertEqual(ctx.get_retry_count(), 2)
        self.assertEqual(ctx.get_poll_count(), 5)
        self.assertEqual(ctx.get_input(), {'key': 'value', 'count': 42})

    def test_add_log(self):
        """Test adding logs via context"""
        ctx = _set_task_context(self.task, self.task_result)

        ctx.add_log("Log message 1")
        ctx.add_log("Log message 2")

        self.assertEqual(len(self.task_result.logs), 2)
        self.assertEqual(self.task_result.logs[0].log, "Log message 1")
        self.assertEqual(self.task_result.logs[1].log, "Log message 2")

    def test_set_callback_after(self):
        """Test setting callback delay"""
        ctx = _set_task_context(self.task, self.task_result)

        ctx.set_callback_after(60)

        self.assertEqual(self.task_result.callback_after_seconds, 60)

    def test_set_output(self):
        """Test setting output data"""
        ctx = _set_task_context(self.task, self.task_result)

        ctx.set_output({'result': 'success', 'value': 123})

        self.assertEqual(self.task_result.output_data, {'result': 'success', 'value': 123})

    def test_get_task_context_without_context_raises(self):
        """Test that get_task_context() raises when no context set"""
        with self.assertRaises(RuntimeError) as cm:
            get_task_context()

        self.assertIn("No task context available", str(cm.exception))

    def test_get_task_context_returns_same_instance(self):
        """Test that get_task_context() returns the same instance"""
        ctx1 = _set_task_context(self.task, self.task_result)
        ctx2 = get_task_context()

        self.assertIs(ctx1, ctx2)

    def test_clear_task_context(self):
        """Test clearing task context"""
        _set_task_context(self.task, self.task_result)

        _clear_task_context()

        with self.assertRaises(RuntimeError):
            get_task_context()

    def test_context_properties(self):
        """Test task and task_result properties"""
        ctx = _set_task_context(self.task, self.task_result)

        self.assertIs(ctx.task, self.task)
        self.assertIs(ctx.task_result, self.task_result)

    def test_repr(self):
        """Test string representation"""
        ctx = _set_task_context(self.task, self.task_result)

        repr_str = repr(ctx)

        self.assertIn('test-task-123', repr_str)
        self.assertIn('test-workflow-456', repr_str)
        self.assertIn('2', repr_str)  # retry count


class TestTaskContextIntegration(unittest.TestCase):
    """Test TaskContext integration with TaskRunner"""

    def setUp(self):
        self.config = Configuration()
        _clear_task_context()

    def tearDown(self):
        _clear_task_context()

    def run_async(self, coro):
        """Helper to run async code in tests"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_context_available_in_worker(self):
        """Test that context is available inside worker execution"""
        context_captured = []

        def worker_func(task):
            ctx = get_task_context()
            context_captured.append({
                'task_id': ctx.get_task_id(),
                'workflow_id': ctx.get_workflow_instance_id()
            })
            return {'result': 'done'}

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker_func
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task-abc'
            task.workflow_instance_id = 'workflow-xyz'
            task.task_def_name = 'test_task'
            task.input_data = {}

            result = await runner._execute_task(task)

            self.assertEqual(len(context_captured), 1)
            self.assertEqual(context_captured[0]['task_id'], 'task-abc')
            self.assertEqual(context_captured[0]['workflow_id'], 'workflow-xyz')

        self.run_async(test())

    def test_context_cleared_after_worker(self):
        """Test that context is cleared after worker execution"""
        def worker_func(task):
            ctx = get_task_context()
            ctx.add_log("Test log")
            return {'result': 'done'}

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker_func
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task-abc'
            task.workflow_instance_id = 'workflow-xyz'
            task.task_def_name = 'test_task'
            task.input_data = {}

            await runner._execute_task(task)

            # Context should be cleared after execution
            with self.assertRaises(RuntimeError):
                get_task_context()

        self.run_async(test())

    def test_logs_merged_into_result(self):
        """Test that logs added via context are merged into result"""
        def worker_func(task):
            ctx = get_task_context()
            ctx.add_log("Log 1")
            ctx.add_log("Log 2")
            return {'result': 'done'}

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker_func
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task-abc'
            task.workflow_instance_id = 'workflow-xyz'
            task.task_def_name = 'test_task'
            task.input_data = {}

            result = await runner._execute_task(task)

            self.assertIsNotNone(result.logs)
            self.assertEqual(len(result.logs), 2)
            self.assertEqual(result.logs[0].log, "Log 1")
            self.assertEqual(result.logs[1].log, "Log 2")

        self.run_async(test())

    def test_callback_after_merged_into_result(self):
        """Test that callback_after is merged into result"""
        def worker_func(task):
            ctx = get_task_context()
            ctx.set_callback_after(120)
            return {'result': 'pending'}

        worker = Worker(
            task_definition_name='test_task',
            execute_function=worker_func
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task-abc'
            task.workflow_instance_id = 'workflow-xyz'
            task.task_def_name = 'test_task'
            task.input_data = {}

            result = await runner._execute_task(task)

            self.assertEqual(result.callback_after_seconds, 120)

        self.run_async(test())

    def test_async_worker_with_context(self):
        """Test TaskContext works with async workers"""
        async def async_worker_func(task):
            ctx = get_task_context()
            ctx.add_log("Async log 1")

            # Simulate async work
            await asyncio.sleep(0.01)

            ctx.add_log("Async log 2")
            return {'result': 'async_done'}

        worker = Worker(
            task_definition_name='test_task',
            execute_function=async_worker_func
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task-async'
            task.workflow_instance_id = 'workflow-async'
            task.task_def_name = 'test_task'
            task.input_data = {}

            result = await runner._execute_task(task)

            self.assertEqual(len(result.logs), 2)
            self.assertEqual(result.logs[0].log, "Async log 1")
            self.assertEqual(result.logs[1].log, "Async log 2")

        self.run_async(test())

    def test_context_with_task_exception(self):
        """Test that context is cleared even when worker raises exception"""
        def failing_worker(task):
            ctx = get_task_context()
            ctx.add_log("Before failure")
            raise RuntimeError("Task failed")

        worker = Worker(
            task_definition_name='test_task',
            execute_function=failing_worker
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task-fail'
            task.workflow_instance_id = 'workflow-fail'
            task.task_def_name = 'test_task'
            task.input_data = {}

            result = await runner._execute_task(task)

            # Task should have failed
            self.assertEqual(result.status, "FAILED")

            # Context should still be cleared
            with self.assertRaises(RuntimeError):
                get_task_context()

        self.run_async(test())


if __name__ == '__main__':
    unittest.main()
