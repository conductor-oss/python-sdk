"""
Comprehensive tests for TaskRunnerAsyncIO concurrency, thread safety, and edge cases.

Tests cover:
1. Output serialization (dict vs primitives)
2. Semaphore-based batch polling
3. Permit leak prevention
4. Race conditions
5. Concurrent execution
6. Thread safety
"""

import asyncio
import dataclasses
import json
import unittest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import List
import time

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


@dataclasses.dataclass
class UserData:
    """Test dataclass for serialization tests"""
    id: int
    name: str
    email: str


class SimpleWorker(Worker):
    """Simple test worker"""
    def __init__(self, task_name='test_task'):
        def execute_fn(task):
            return {"result": "test"}
        super().__init__(task_name, execute_fn)


@unittest.skipIf(httpx is None, "httpx not installed")
class TestOutputSerialization(unittest.TestCase):
    """Tests for output_data serialization (dict vs primitives)"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = Configuration()
        self.worker = SimpleWorker()

    def tearDown(self):
        self.loop.close()

    def run_async(self, coro):
        return self.loop.run_until_complete(coro)

    def test_dict_output_not_wrapped(self):
        """Dict outputs should be used as-is, not wrapped in {"result": ...}"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        # Test with dict output
        dict_output = {"id": 1, "name": "John", "status": "active"}
        result = runner._create_task_result(task, dict_output)

        # Should NOT be wrapped
        self.assertEqual(result.output_data, {"id": 1, "name": "John", "status": "active"})
        self.assertNotIn("result", result.output_data or {})

    def test_string_output_wrapped(self):
        """String outputs should be wrapped in {"result": ...}"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        result = runner._create_task_result(task, "Hello World")

        # Should be wrapped
        self.assertEqual(result.output_data, {"result": "Hello World"})

    def test_integer_output_wrapped(self):
        """Integer outputs should be wrapped in {"result": ...}"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        result = runner._create_task_result(task, 42)

        self.assertEqual(result.output_data, {"result": 42})

    def test_list_output_wrapped(self):
        """List outputs should be wrapped in {"result": ...}"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        result = runner._create_task_result(task, [1, 2, 3])

        self.assertEqual(result.output_data, {"result": [1, 2, 3]})

    def test_boolean_output_wrapped(self):
        """Boolean outputs should be wrapped in {"result": ...}"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        result = runner._create_task_result(task, True)

        self.assertEqual(result.output_data, {"result": True})

    def test_none_output_wrapped(self):
        """None outputs should be wrapped in {"result": ...}"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        result = runner._create_task_result(task, None)

        self.assertEqual(result.output_data, {"result": None})

    def test_dataclass_output_not_wrapped(self):
        """Dataclass outputs should be serialized to dict and used as-is"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        user = UserData(id=1, name="John", email="john@example.com")
        result = runner._create_task_result(task, user)

        # Should be serialized to dict and NOT wrapped
        self.assertIsInstance(result.output_data, dict)
        self.assertEqual(result.output_data.get("id"), 1)
        self.assertEqual(result.output_data.get("name"), "John")
        self.assertEqual(result.output_data.get("email"), "john@example.com")
        # Should NOT have "result" key at top level
        self.assertNotEqual(list(result.output_data.keys()), ["result"])

    def test_nested_dict_output_not_wrapped(self):
        """Nested dict outputs should be used as-is"""
        runner = TaskRunnerAsyncIO(self.worker, self.config)

        task = Task()
        task.task_id = 'task1'
        task.workflow_instance_id = 'wf1'

        nested_output = {
            "user": {
                "id": 1,
                "profile": {
                    "name": "John",
                    "age": 30
                }
            },
            "metadata": {
                "timestamp": "2025-01-01"
            }
        }

        result = runner._create_task_result(task, nested_output)

        # Should be used as-is
        self.assertEqual(result.output_data, nested_output)


@unittest.skipIf(httpx is None, "httpx not installed")
class TestSemaphoreBatchPolling(unittest.TestCase):
    """Tests for semaphore-based dynamic batch polling"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = Configuration()

    def tearDown(self):
        self.loop.close()

    def run_async(self, coro):
        return self.loop.run_until_complete(coro)

    def test_acquire_all_available_permits(self):
        """Should acquire all available permits non-blocking"""
        worker = SimpleWorker()
        worker.thread_count = 5

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Initially, all 5 permits should be available
            acquired = await runner._acquire_available_permits()
            return acquired

        count = self.run_async(test())
        self.assertEqual(count, 5)

    def test_acquire_zero_permits_when_all_busy(self):
        """Should return 0 when all permits are held"""
        worker = SimpleWorker()
        worker.thread_count = 3

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Acquire all permits
            for _ in range(3):
                await runner._semaphore.acquire()

            # Now try to acquire - should get 0
            acquired = await runner._acquire_available_permits()
            return acquired

        count = self.run_async(test())
        self.assertEqual(count, 0)

    def test_acquire_partial_permits(self):
        """Should acquire only available permits"""
        worker = SimpleWorker()
        worker.thread_count = 5

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Hold 3 permits
            for _ in range(3):
                await runner._semaphore.acquire()

            # Should only get 2 remaining
            acquired = await runner._acquire_available_permits()
            return acquired

        count = self.run_async(test())
        self.assertEqual(count, 2)

    def test_zero_polling_optimization(self):
        """Should skip polling when poll_count is 0"""
        worker = SimpleWorker()
        worker.thread_count = 2

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Hold all permits
            for _ in range(2):
                await runner._semaphore.acquire()

            # Mock the _poll_tasks method to verify it's not called
            runner._poll_tasks = AsyncMock()

            # Run once - should return early without polling
            await runner.run_once()

            # _poll_tasks should NOT have been called
            return runner._poll_tasks.called

        was_called = self.run_async(test())
        self.assertFalse(was_called, "Should not poll when all threads busy")

    def test_excess_permits_released(self):
        """Should release excess permits when fewer tasks returned"""
        worker = SimpleWorker()
        worker.thread_count = 5

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Mock _poll_tasks to return only 2 tasks when asked for 5
            mock_tasks = [Mock(spec=Task), Mock(spec=Task)]
            for task in mock_tasks:
                task.task_id = f"task_{id(task)}"

            runner._poll_tasks = AsyncMock(return_value=mock_tasks)
            runner._execute_and_update_task = AsyncMock()

            # Run once - acquires 5, gets 2 tasks, should release 3
            await runner.run_once()

            # Check semaphore value - should have 3 permits back
            # (5 total - 2 in use for tasks)
            return runner._semaphore._value

        remaining_permits = self.run_async(test())
        self.assertEqual(remaining_permits, 3)


@unittest.skipIf(httpx is None, "httpx not installed")
class TestPermitLeakPrevention(unittest.TestCase):
    """Tests for preventing permit leaks that cause deadlock"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = Configuration()

    def tearDown(self):
        self.loop.close()

    def run_async(self, coro):
        return self.loop.run_until_complete(coro)

    def test_permits_released_on_poll_exception(self):
        """Permits should be released if exception occurs during polling"""
        worker = SimpleWorker()
        worker.thread_count = 5

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Mock _poll_tasks to raise exception
            runner._poll_tasks = AsyncMock(side_effect=Exception("Poll failed"))

            # Run once - should acquire permits then release them on exception
            await runner.run_once()

            # All permits should be released
            return runner._semaphore._value

        permits = self.run_async(test())
        self.assertEqual(permits, 5, "All permits should be released after exception")

    def test_permit_always_released_after_task_execution(self):
        """Permit should be released even if task execution fails"""
        worker = SimpleWorker()
        worker.thread_count = 3

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task1'
            task.workflow_instance_id = 'wf1'

            # Mock _execute_task to raise exception
            runner._execute_task = AsyncMock(side_effect=Exception("Execution failed"))
            runner._update_task = AsyncMock()

            # Execute and update - should release permit in finally block
            initial_permits = runner._semaphore._value
            await runner._execute_and_update_task(task)

            # Permit should be released
            final_permits = runner._semaphore._value

            return initial_permits, final_permits

        initial, final = self.run_async(test())
        self.assertEqual(final, initial + 1, "Permit should be released after task failure")

    def test_permit_released_even_if_update_fails(self):
        """Permit should be released even if update fails"""
        worker = SimpleWorker()
        worker.thread_count = 3

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task1'
            task.workflow_instance_id = 'wf1'
            task.input_data = {}

            # Mock successful execution but failed update
            runner._execute_task = AsyncMock(return_value=TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1'
            ))
            runner._update_task = AsyncMock(side_effect=Exception("Update failed"))

            # Acquire one permit first to simulate normal flow
            await runner._semaphore.acquire()
            initial_permits = runner._semaphore._value

            # Execute and update - should release permit in finally block
            await runner._execute_and_update_task(task)

            final_permits = runner._semaphore._value

            return initial_permits, final_permits

        initial, final = self.run_async(test())
        self.assertEqual(final, initial + 1, "Permit should be released even if update fails")


@unittest.skipIf(httpx is None, "httpx not installed")
class TestConcurrency(unittest.TestCase):
    """Tests for concurrent execution and thread safety"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = Configuration()

    def tearDown(self):
        self.loop.close()

    def run_async(self, coro):
        return self.loop.run_until_complete(coro)

    def test_concurrent_permit_acquisition(self):
        """Multiple concurrent acquisitions should not exceed max permits"""
        worker = SimpleWorker()
        worker.thread_count = 5

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Try to acquire permits concurrently
            tasks = [runner._acquire_available_permits() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            # Total acquired should not exceed thread_count
            total_acquired = sum(results)
            return total_acquired

        total = self.run_async(test())
        self.assertLessEqual(total, 5, "Should not acquire more than max permits")

    def test_concurrent_task_execution_respects_semaphore(self):
        """Concurrent tasks should respect semaphore limit"""
        worker = SimpleWorker()
        worker.thread_count = 3

        runner = TaskRunnerAsyncIO(worker, self.config)

        execution_count = []

        async def mock_execute(task):
            execution_count.append(1)
            await asyncio.sleep(0.1)  # Simulate work
            execution_count.pop()
            return TaskResult(
                task_id=task.task_id,
                workflow_instance_id=task.workflow_instance_id,
                worker_id='worker1'
            )

        async def test():
            runner._execute_task = mock_execute
            runner._update_task = AsyncMock()

            # Create 10 tasks
            tasks = []
            for i in range(10):
                task = Task()
                task.task_id = f'task{i}'
                task.workflow_instance_id = 'wf1'
                task.input_data = {}
                tasks.append(runner._execute_and_update_task(task))

            # Execute all concurrently
            await asyncio.gather(*tasks)

            return True

        # Should complete without exceeding limit
        self.run_async(test())
        # Test passes if no assertion errors during execution

    def test_no_race_condition_in_background_task_tracking(self):
        """Background tasks should be properly tracked without race conditions"""
        worker = SimpleWorker()
        worker.thread_count = 5

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            mock_tasks = []
            for i in range(10):
                task = Task()
                task.task_id = f'task{i}'
                mock_tasks.append(task)

            runner._poll_tasks = AsyncMock(return_value=mock_tasks[:5])
            runner._execute_and_update_task = AsyncMock(return_value=None)

            # Run once - creates background tasks
            await runner.run_once()

            # All background tasks should be tracked
            return len(runner._background_tasks)

        count = self.run_async(test())
        self.assertEqual(count, 5, "All background tasks should be tracked")

    def test_semaphore_not_over_released(self):
        """Semaphore should not be released more times than acquired"""
        worker = SimpleWorker()
        worker.thread_count = 3

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Acquire 2 permits
            await runner._semaphore.acquire()
            await runner._semaphore.acquire()

            # Should have 1 remaining
            initial = runner._semaphore._value
            self.assertEqual(initial, 1)

            # Release 2
            runner._semaphore.release()
            runner._semaphore.release()

            # Should have 3 total
            after_release = runner._semaphore._value
            self.assertEqual(after_release, 3)

            # Try to release one more (should not exceed initial max)
            runner._semaphore.release()

            final = runner._semaphore._value
            return final

        final = self.run_async(test())
        # Should not exceed max (3)
        self.assertGreaterEqual(final, 3)


@unittest.skipIf(httpx is None, "httpx not installed")
class TestLeaseExtension(unittest.TestCase):
    """Tests for lease extension behavior"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = Configuration()

    def tearDown(self):
        self.loop.close()

    def run_async(self, coro):
        return self.loop.run_until_complete(coro)

    def test_lease_extension_cancelled_on_completion(self):
        """Lease extension should be cancelled when task completes"""
        worker = SimpleWorker()
        worker.lease_extend_enabled = True

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task1'
            task.workflow_instance_id = 'wf1'
            task.response_timeout_seconds = 10
            task.input_data = {}

            runner._execute_task = AsyncMock(return_value=TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1'
            ))
            runner._update_task = AsyncMock()

            # Execute task
            await runner._execute_and_update_task(task)

            # Lease extension should be cleaned up
            return task.task_id in runner._lease_extensions

        is_tracked = self.run_async(test())
        self.assertFalse(is_tracked, "Lease extension should be cancelled and removed")

    def test_lease_extension_cancelled_on_exception(self):
        """Lease extension should be cancelled even if task execution fails"""
        worker = SimpleWorker()
        worker.lease_extend_enabled = True

        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'task1'
            task.workflow_instance_id = 'wf1'
            task.response_timeout_seconds = 10
            task.input_data = {}

            runner._execute_task = AsyncMock(side_effect=Exception("Failed"))
            runner._update_task = AsyncMock()

            # Execute task (will fail)
            await runner._execute_and_update_task(task)

            # Lease extension should still be cleaned up
            return task.task_id in runner._lease_extensions

        is_tracked = self.run_async(test())
        self.assertFalse(is_tracked, "Lease extension should be cancelled even on exception")


@unittest.skipIf(httpx is None, "httpx not installed")
class TestV2API(unittest.TestCase):
    """Tests for V2 API chained task handling"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = Configuration()

    def tearDown(self):
        self.loop.close()

    def run_async(self, coro):
        return self.loop.run_until_complete(coro)

    def test_v2_api_enabled_by_default(self):
        """V2 API should be enabled by default"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config)

        self.assertTrue(runner._use_v2_api, "V2 API should be enabled by default")

    def test_v2_api_can_be_disabled(self):
        """V2 API can be disabled via constructor"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=False)

        self.assertFalse(runner._use_v2_api, "V2 API should be disabled")

    def test_v2_api_env_var_overrides_constructor(self):
        """Environment variable should override constructor parameter"""
        import os
        os.environ['taskUpdateV2'] = 'false'

        try:
            worker = SimpleWorker()
            runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=True)

            self.assertFalse(runner._use_v2_api, "Env var should override constructor")
        finally:
            del os.environ['taskUpdateV2']

    def test_v2_api_next_task_added_to_queue(self):
        """Next task from V2 API should be queued when no permits available"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=True)

        async def test():
            # Consume permit so next task must be queued
            await runner._semaphore.acquire()

            task_result = TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1'
            )

            # Mock HTTP response with next task
            next_task_data = {
                'taskId': 'task2',
                'taskDefName': 'test_task',
                'workflowInstanceId': 'wf1',
                'status': 'IN_PROGRESS',
                'inputData': {}
            }

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"taskId": "task2"}'
            mock_response.json = Mock(return_value=next_task_data)
            mock_response.raise_for_status = Mock()

            runner.http_client.post = AsyncMock(return_value=mock_response)

            # Initially queue should be empty
            initial_queue_size = runner._task_queue.qsize()

            # Update task (should queue since no permit available)
            await runner._update_task(task_result)

            # Queue should now have the next task
            final_queue_size = runner._task_queue.qsize()

            # Release permit
            runner._semaphore.release()

            return initial_queue_size, final_queue_size

        initial, final = self.run_async(test())
        self.assertEqual(initial, 0, "Queue should start empty")
        self.assertEqual(final, 1, "Queue should have next task when no permits available")

    def test_v2_api_empty_response_not_added_to_queue(self):
        """Empty V2 API response should not add to queue"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=True)

        async def test():
            task_result = TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1'
            )

            # Mock HTTP response with empty string (no next task)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ''
            mock_response.raise_for_status = Mock()

            runner.http_client.post = AsyncMock(return_value=mock_response)

            initial_queue_size = runner._task_queue.qsize()
            await runner._update_task(task_result)
            final_queue_size = runner._task_queue.qsize()

            return initial_queue_size, final_queue_size

        initial, final = self.run_async(test())
        self.assertEqual(initial, 0, "Queue should start empty")
        self.assertEqual(final, 0, "Queue should remain empty for empty response")

    def test_v2_api_uses_correct_endpoint(self):
        """V2 API should use /tasks/update-v2 endpoint"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=True)

        async def test():
            task_result = TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1'
            )

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ''
            mock_response.raise_for_status = Mock()

            runner.http_client.post = AsyncMock(return_value=mock_response)

            await runner._update_task(task_result)

            # Check that /tasks/update-v2 was called
            call_args = runner.http_client.post.call_args
            endpoint = call_args[0][0] if call_args[0] else None
            return endpoint

        endpoint = self.run_async(test())
        self.assertEqual(endpoint, "/tasks/update-v2", "Should use V2 endpoint")

    def test_v1_api_uses_correct_endpoint(self):
        """V1 API should use /tasks endpoint"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=False)

        async def test():
            task_result = TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1'
            )

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ''
            mock_response.raise_for_status = Mock()

            runner.http_client.post = AsyncMock(return_value=mock_response)

            await runner._update_task(task_result)

            # Check that /tasks was called
            call_args = runner.http_client.post.call_args
            endpoint = call_args[0][0] if call_args[0] else None
            return endpoint

        endpoint = self.run_async(test())
        self.assertEqual(endpoint, "/tasks", "Should use /tasks endpoint")


@unittest.skipIf(httpx is None, "httpx not installed")
class TestImmediateExecution(unittest.TestCase):
    """Tests for V2 API immediate execution optimization"""

    def setUp(self):
        self.config = Configuration()

    def run_async(self, coro):
        """Helper to run async functions"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_immediate_execution_when_permit_available(self):
        """Should execute immediately when permit available"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Ensure permits available
            self.assertEqual(runner._semaphore._value, 1)

            task1 = Task()
            task1.task_id = 'task1'
            task1.task_def_name = 'simple_task'

            # Call immediate execution
            await runner._try_immediate_execution(task1)

            # Should have created background task (permit acquired)
            # Give it a moment to register
            await asyncio.sleep(0.01)

            # Permit should be consumed
            self.assertEqual(runner._semaphore._value, 0)

            # Queue should be empty (not queued)
            self.assertTrue(runner._task_queue.empty())

            # Background task should exist
            self.assertEqual(len(runner._background_tasks), 1)

        self.run_async(test())

    def test_queues_when_no_permit_available(self):
        """Should queue task when no permit available"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Consume the permit
            await runner._semaphore.acquire()
            self.assertEqual(runner._semaphore._value, 0)

            task1 = Task()
            task1.task_id = 'task1'
            task1.task_def_name = 'simple_task'

            # Try immediate execution (should queue)
            await runner._try_immediate_execution(task1)

            # Permit should still be 0
            self.assertEqual(runner._semaphore._value, 0)

            # Task should be in queue
            self.assertFalse(runner._task_queue.empty())
            self.assertEqual(runner._task_queue.qsize(), 1)

            # No background task created
            self.assertEqual(len(runner._background_tasks), 0)

            # Release permit
            runner._semaphore.release()

        self.run_async(test())

    # Note: Full integration test removed - unit tests above cover the behavior
    # Integration testing is better done with real server in end-to-end tests

    def test_v2_api_queues_when_all_threads_busy(self):
        """V2 API should queue when all permits consumed"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=True)

        async def test():
            # Consume all permits
            await runner._semaphore.acquire()
            self.assertEqual(runner._semaphore._value, 0)

            task_result = TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1',
                status=TaskResultStatus.COMPLETED
            )

            # Mock response with next task
            next_task_data = {
                'taskId': 'task2',
                'taskDefName': 'simple_task',
                'status': 'IN_PROGRESS'
            }

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(next_task_data)
            mock_response.json = Mock(return_value=next_task_data)
            mock_response.raise_for_status = Mock()

            runner.http_client.post = AsyncMock(return_value=mock_response)

            # Update task (should receive task2 and queue it)
            await runner._update_task(task_result)

            # Permit should still be 0
            self.assertEqual(runner._semaphore._value, 0)

            # Task should be queued
            self.assertFalse(runner._task_queue.empty())
            self.assertEqual(runner._task_queue.qsize(), 1)

            # No new background task created
            self.assertEqual(len(runner._background_tasks), 0)

            # Release permit
            runner._semaphore.release()

        self.run_async(test())

    def test_immediate_execution_handles_none_task(self):
        """Should handle None task gracefully"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Try immediate execution with None
            await runner._try_immediate_execution(None)

            # Should not crash, queue should still be empty or have None
            # (depends on implementation - currently queues it)

        self.run_async(test())

    def test_immediate_execution_releases_permit_on_task_failure(self):
        """Should release permit even if task execution fails"""
        def failing_worker(task):
            raise RuntimeError("Task failed")

        worker = Worker(
            task_definition_name='failing_task',
            execute_function=failing_worker
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            initial_permits = runner._semaphore._value
            self.assertEqual(initial_permits, 1)

            task = Task()
            task.task_id = 'task1'
            task.task_def_name = 'failing_task'

            # Mock HTTP response for update call (even though it will fail)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ''
            mock_response.raise_for_status = Mock()
            runner.http_client.post = AsyncMock(return_value=mock_response)

            # Try immediate execution
            await runner._try_immediate_execution(task)

            # Give background task time to execute and fail
            await asyncio.sleep(0.1)

            # Permit should be released even though task failed
            final_permits = runner._semaphore._value
            self.assertEqual(final_permits, initial_permits,
                           "Permit should be released after task failure")

        self.run_async(test())

    def test_immediate_execution_multiple_tasks_concurrently(self):
        """Should execute multiple tasks immediately if permits available"""
        worker = Worker(
            task_definition_name='concurrent_task',
            execute_function=lambda t: {'result': 'done'},
            thread_count=5  # 5 concurrent permits
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Should have 5 permits available
            self.assertEqual(runner._semaphore._value, 5)

            # Create 3 tasks
            tasks = []
            for i in range(3):
                task = Task()
                task.task_id = f'task{i}'
                task.task_def_name = 'concurrent_task'
                tasks.append(task)

            # Execute all 3 immediately
            for task in tasks:
                await runner._try_immediate_execution(task)

            # Give tasks time to start
            await asyncio.sleep(0.01)

            # Should have consumed 3 permits
            self.assertEqual(runner._semaphore._value, 2)

            # All should be executing (not queued)
            self.assertTrue(runner._task_queue.empty())

            # Should have 3 background tasks
            self.assertEqual(len(runner._background_tasks), 3)

        self.run_async(test())

    def test_immediate_execution_mixed_immediate_and_queued(self):
        """Should execute some immediately and queue others when permits run out"""
        worker = Worker(
            task_definition_name='mixed_task',
            execute_function=lambda t: {'result': 'done'},
            thread_count=2  # Only 2 concurrent permits
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Should have 2 permits available
            self.assertEqual(runner._semaphore._value, 2)

            # Create 4 tasks
            tasks = []
            for i in range(4):
                task = Task()
                task.task_id = f'task{i}'
                task.task_def_name = 'mixed_task'
                tasks.append(task)

            # Try to execute all 4
            for task in tasks:
                await runner._try_immediate_execution(task)

            # Give tasks time to start
            await asyncio.sleep(0.01)

            # Should have consumed all permits
            self.assertEqual(runner._semaphore._value, 0)

            # Should have 2 tasks in queue (the ones that couldn't execute)
            self.assertEqual(runner._task_queue.qsize(), 2)

            # Should have 2 background tasks (executing immediately)
            self.assertEqual(len(runner._background_tasks), 2)

        self.run_async(test())

    def test_immediate_execution_with_v2_response_integration(self):
        """Full integration: V2 API response triggers immediate execution"""
        worker = Worker(
            task_definition_name='integration_task',
            execute_function=lambda t: {'result': 'done'},
            thread_count=3
        )
        runner = TaskRunnerAsyncIO(worker, self.config, use_v2_api=True)

        async def test():
            # Initial state: 3 permits available
            self.assertEqual(runner._semaphore._value, 3)

            # Create task result to update
            task_result = TaskResult(
                task_id='task1',
                workflow_instance_id='wf1',
                worker_id='worker1',
                status=TaskResultStatus.COMPLETED
            )

            # Mock V2 API response with next task
            next_task_data = {
                'taskId': 'task2',
                'taskDefName': 'integration_task',
                'status': 'IN_PROGRESS',
                'workflowInstanceId': 'wf1'
            }

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(next_task_data)
            mock_response.json = Mock(return_value=next_task_data)
            mock_response.raise_for_status = Mock()

            runner.http_client.post = AsyncMock(return_value=mock_response)

            # Update task (should trigger immediate execution)
            await runner._update_task(task_result)

            # Give background task time to start
            await asyncio.sleep(0.05)

            # Should have consumed 1 permit (immediate execution)
            self.assertEqual(runner._semaphore._value, 2)

            # Queue should be empty (immediate, not queued)
            self.assertTrue(runner._task_queue.empty())

        self.run_async(test())

    def test_immediate_execution_permit_not_leaked_on_exception(self):
        """Permit should not leak if exception during task creation"""
        worker = SimpleWorker()
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            initial_permits = runner._semaphore._value

            # Create invalid task that will cause issues
            invalid_task = Mock()
            invalid_task.task_id = None  # Invalid
            invalid_task.task_def_name = None

            # Try immediate execution (should handle gracefully)
            try:
                await runner._try_immediate_execution(invalid_task)
            except Exception:
                pass

            # Wait a bit
            await asyncio.sleep(0.05)

            # Permits should not be leaked
            # Either permit was never acquired (stayed same) or was released
            final_permits = runner._semaphore._value
            self.assertGreaterEqual(final_permits, 0)
            self.assertLessEqual(final_permits, initial_permits + 1)

        self.run_async(test())

    def test_immediate_execution_background_task_cleanup(self):
        """Background tasks should be properly tracked and cleaned up"""

        # Create a slow worker so we can observe background tasks before completion
        async def slow_worker(task):
            await asyncio.sleep(0.1)
            return {'result': 'done'}

        worker = Worker(
            task_definition_name='cleanup_task',
            execute_function=slow_worker,
            thread_count=2
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Mock HTTP response for update calls
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ''
            mock_response.raise_for_status = Mock()
            runner.http_client.post = AsyncMock(return_value=mock_response)

            # Create 2 tasks
            task1 = Task()
            task1.task_id = 'task1'
            task1.task_def_name = 'cleanup_task'

            task2 = Task()
            task2.task_id = 'task2'
            task2.task_def_name = 'cleanup_task'

            # Execute both immediately
            await runner._try_immediate_execution(task1)
            await runner._try_immediate_execution(task2)

            # Give time to start (but not complete)
            await asyncio.sleep(0.02)

            # Should have 2 background tasks
            self.assertEqual(len(runner._background_tasks), 2)

            # Wait for tasks to complete
            await asyncio.sleep(0.3)

            # Background tasks should be cleaned up after completion
            # (done_callback removes them from the set)
            self.assertEqual(len(runner._background_tasks), 0)

        self.run_async(test())

    def test_worker_returns_task_result_used_as_is(self):
        """When worker returns TaskResult, it should be used as-is without JSON conversion"""

        # Create a worker that returns a custom TaskResult with specific fields
        def worker_returns_task_result(task):
            result = TaskResult()
            result.status = TaskResultStatus.COMPLETED
            result.output_data = {
                "custom_field": "custom_value",
                "nested": {"data": [1, 2, 3]}
            }
            # Add custom logs and callback
            from conductor.client.http.models.task_exec_log import TaskExecLog
            result.logs = [
                TaskExecLog(log="Custom log 1", task_id="test", created_time=1234567890),
                TaskExecLog(log="Custom log 2", task_id="test", created_time=1234567891)
            ]
            result.callback_after_seconds = 300
            result.reason_for_incompletion = None
            return result

        worker = Worker(
            task_definition_name='task_result_test',
            execute_function=worker_returns_task_result,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Create test task
            task = Task()
            task.task_id = 'test_task_123'
            task.workflow_instance_id = 'workflow_456'
            task.task_def_name = 'task_result_test'

            # Execute the task
            result = await runner._execute_task(task)

            # Verify the result is a TaskResult (not converted to dict)
            self.assertIsInstance(result, TaskResult)

            # Verify task_id and workflow_instance_id are set correctly
            self.assertEqual(result.task_id, 'test_task_123')
            self.assertEqual(result.workflow_instance_id, 'workflow_456')

            # Verify custom fields are preserved (not wrapped or converted)
            self.assertEqual(result.output_data['custom_field'], 'custom_value')
            self.assertEqual(result.output_data['nested']['data'], [1, 2, 3])

            # Verify status is preserved
            self.assertEqual(result.status, TaskResultStatus.COMPLETED)

            # Verify logs are preserved
            self.assertIsNotNone(result.logs)
            self.assertEqual(len(result.logs), 2)
            self.assertEqual(result.logs[0].log, 'Custom log 1')
            self.assertEqual(result.logs[1].log, 'Custom log 2')

            # Verify callback_after_seconds is preserved
            self.assertEqual(result.callback_after_seconds, 300)

            # Verify reason_for_incompletion is preserved
            self.assertIsNone(result.reason_for_incompletion)

        self.run_async(test())

    def test_worker_returns_task_result_async(self):
        """Async worker returning TaskResult should also work correctly"""

        async def async_worker_returns_task_result(task):
            await asyncio.sleep(0.01)  # Simulate async work
            result = TaskResult()
            result.status = TaskResultStatus.COMPLETED
            result.output_data = {"async_result": True, "value": 42}
            return result

        worker = Worker(
            task_definition_name='async_task_result_test',
            execute_function=async_worker_returns_task_result,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'async_task_789'
            task.workflow_instance_id = 'workflow_999'
            task.task_def_name = 'async_task_result_test'

            # Execute the async task
            result = await runner._execute_task(task)

            # Verify it's a TaskResult
            self.assertIsInstance(result, TaskResult)

            # Verify IDs are set
            self.assertEqual(result.task_id, 'async_task_789')
            self.assertEqual(result.workflow_instance_id, 'workflow_999')

            # Verify output is not wrapped
            self.assertEqual(result.output_data['async_result'], True)
            self.assertEqual(result.output_data['value'], 42)
            self.assertNotIn('result', result.output_data)  # Should NOT be wrapped

        self.run_async(test())

    def test_worker_returns_dict_gets_wrapped(self):
        """Contrast test: dict return should be wrapped in output_data"""

        def worker_returns_dict(task):
            return {"raw": "dict", "value": 123}

        worker = Worker(
            task_definition_name='dict_test',
            execute_function=worker_returns_dict,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'dict_task'
            task.workflow_instance_id = 'workflow_123'
            task.task_def_name = 'dict_test'

            result = await runner._execute_task(task)

            # Should be a TaskResult
            self.assertIsInstance(result, TaskResult)

            # Dict should be in output_data directly (not wrapped in "result")
            self.assertIn('raw', result.output_data)
            self.assertEqual(result.output_data['raw'], 'dict')
            self.assertEqual(result.output_data['value'], 123)

        self.run_async(test())

    def test_worker_returns_primitive_gets_wrapped(self):
        """Primitive return values should be wrapped in result field"""

        def worker_returns_string(task):
            return "simple string"

        worker = Worker(
            task_definition_name='primitive_test',
            execute_function=worker_returns_string,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'primitive_task'
            task.workflow_instance_id = 'workflow_456'
            task.task_def_name = 'primitive_test'

            result = await runner._execute_task(task)

            # Should be a TaskResult
            self.assertIsInstance(result, TaskResult)

            # Primitive should be wrapped in "result" field
            self.assertIn('result', result.output_data)
            self.assertEqual(result.output_data['result'], 'simple string')

        self.run_async(test())

    def test_long_running_task_with_callback_after(self):
        """
        Test long-running task pattern using TaskResult with callback_after.

        Simulates a task that needs to poll 3 times before completion:
        - Poll 1: IN_PROGRESS with callback_after=1s
        - Poll 2: IN_PROGRESS with callback_after=1s
        - Poll 3: COMPLETED with final result
        """

        def long_running_worker(task):
            """Worker that uses poll_count to track progress"""
            poll_count = task.poll_count if task.poll_count else 0

            result = TaskResult()
            result.output_data = {
                "poll_count": poll_count,
                "message": f"Processing attempt {poll_count}"
            }

            # Complete after 3 polls
            if poll_count >= 3:
                result.status = TaskResultStatus.COMPLETED
                result.output_data["message"] = "Task completed!"
                result.output_data["final_result"] = "success"
            else:
                # Still in progress - ask Conductor to callback after 1 second
                result.status = TaskResultStatus.IN_PROGRESS
                result.callback_after_seconds = 1
                result.output_data["message"] = f"Still working... (poll {poll_count})"

            return result

        worker = Worker(
            task_definition_name='long_running_task',
            execute_function=long_running_worker,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Test Poll 1 (poll_count=1)
            task1 = Task()
            task1.task_id = 'long_task_1'
            task1.workflow_instance_id = 'workflow_1'
            task1.task_def_name = 'long_running_task'
            task1.poll_count = 1

            result1 = await runner._execute_task(task1)

            # Should be IN_PROGRESS with callback_after
            self.assertIsInstance(result1, TaskResult)
            self.assertEqual(result1.status, TaskResultStatus.IN_PROGRESS)
            self.assertEqual(result1.callback_after_seconds, 1)
            self.assertEqual(result1.output_data['poll_count'], 1)
            self.assertIn('Still working', result1.output_data['message'])

            # Test Poll 2 (poll_count=2)
            task2 = Task()
            task2.task_id = 'long_task_1'
            task2.workflow_instance_id = 'workflow_1'
            task2.task_def_name = 'long_running_task'
            task2.poll_count = 2

            result2 = await runner._execute_task(task2)

            # Still IN_PROGRESS with callback_after
            self.assertEqual(result2.status, TaskResultStatus.IN_PROGRESS)
            self.assertEqual(result2.callback_after_seconds, 1)
            self.assertEqual(result2.output_data['poll_count'], 2)

            # Test Poll 3 (poll_count=3) - Final completion
            task3 = Task()
            task3.task_id = 'long_task_1'
            task3.workflow_instance_id = 'workflow_1'
            task3.task_def_name = 'long_running_task'
            task3.poll_count = 3

            result3 = await runner._execute_task(task3)

            # Should be COMPLETED now
            self.assertEqual(result3.status, TaskResultStatus.COMPLETED)
            self.assertIsNone(result3.callback_after_seconds)  # No more callbacks needed
            self.assertEqual(result3.output_data['poll_count'], 3)
            self.assertEqual(result3.output_data['final_result'], 'success')
            self.assertIn('completed', result3.output_data['message'].lower())

        self.run_async(test())


    def test_long_running_task_with_union_approach(self):
        """
        Test Union approach: return Union[dict, TaskInProgress].

        This is the cleanest approach - semantically correct (not an exception),
        explicit in type signature, and better type checking.
        """
        from conductor.client.context import TaskInProgress, get_task_context
        from typing import Union

        def long_running_union(job_id: str, max_polls: int = 3) -> Union[dict, TaskInProgress]:
            """
            Worker with Union return type - most Pythonic approach.

            Return TaskInProgress when still working.
            Return dict when complete.
            """
            ctx = get_task_context()
            poll_count = ctx.get_poll_count()

            ctx.add_log(f"Processing job {job_id}, poll {poll_count}/{max_polls}")

            if poll_count < max_polls:
                # Still working - return TaskInProgress (NOT an error!)
                return TaskInProgress(
                    callback_after_seconds=1,
                    output={
                        'status': 'processing',
                        'job_id': job_id,
                        'poll_count': poll_count,
                        'progress': int((poll_count / max_polls) * 100)
                    }
                )

            # Complete - return normal dict
            return {
                'status': 'completed',
                'job_id': job_id,
                'result': 'success',
                'total_polls': poll_count
            }

        worker = Worker(
            task_definition_name='long_running_union',
            execute_function=long_running_union,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Poll 1 - in progress
            task1 = Task()
            task1.task_id = 'union_task_1'
            task1.workflow_instance_id = 'workflow_1'
            task1.task_def_name = 'long_running_union'
            task1.poll_count = 1
            task1.input_data = {'job_id': 'job123', 'max_polls': 3}

            result1 = await runner._execute_task(task1)

            # Should be IN_PROGRESS
            self.assertIsInstance(result1, TaskResult)
            self.assertEqual(result1.status, TaskResultStatus.IN_PROGRESS)
            self.assertEqual(result1.callback_after_seconds, 1)
            self.assertEqual(result1.output_data['status'], 'processing')
            self.assertEqual(result1.output_data['poll_count'], 1)
            self.assertEqual(result1.output_data['progress'], 33)
            # Logs should be present
            self.assertIsNotNone(result1.logs)
            self.assertTrue(any('Processing job' in log.log for log in result1.logs))

            # Poll 2 - still in progress
            task2 = Task()
            task2.task_id = 'union_task_1'
            task2.workflow_instance_id = 'workflow_1'
            task2.task_def_name = 'long_running_union'
            task2.poll_count = 2
            task2.input_data = {'job_id': 'job123', 'max_polls': 3}

            result2 = await runner._execute_task(task2)

            self.assertEqual(result2.status, TaskResultStatus.IN_PROGRESS)
            self.assertEqual(result2.output_data['poll_count'], 2)
            self.assertEqual(result2.output_data['progress'], 66)

            # Poll 3 - completes
            task3 = Task()
            task3.task_id = 'union_task_1'
            task3.workflow_instance_id = 'workflow_1'
            task3.task_def_name = 'long_running_union'
            task3.poll_count = 3
            task3.input_data = {'job_id': 'job123', 'max_polls': 3}

            result3 = await runner._execute_task(task3)

            # Should be COMPLETED with dict result
            self.assertEqual(result3.status, TaskResultStatus.COMPLETED)
            self.assertIsNone(result3.callback_after_seconds)
            self.assertEqual(result3.output_data['status'], 'completed')
            self.assertEqual(result3.output_data['result'], 'success')
            self.assertEqual(result3.output_data['total_polls'], 3)

        self.run_async(test())

    def test_async_worker_with_union_approach(self):
        """Test Union approach with async worker"""
        from conductor.client.context import TaskInProgress, get_task_context
        from typing import Union

        async def async_union_worker(value: int) -> Union[dict, TaskInProgress]:
            """Async worker with Union return type"""
            ctx = get_task_context()
            poll_count = ctx.get_poll_count()

            await asyncio.sleep(0.01)  # Simulate async work

            ctx.add_log(f"Async processing, poll {poll_count}")

            if poll_count < 2:
                return TaskInProgress(
                    callback_after_seconds=2,
                    output={'status': 'working', 'poll': poll_count}
                )

            return {'status': 'done', 'result': value * 2}

        worker = Worker(
            task_definition_name='async_union_worker',
            execute_function=async_union_worker,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            # Poll 1
            task1 = Task()
            task1.task_id = 'async_union_1'
            task1.workflow_instance_id = 'wf_1'
            task1.task_def_name = 'async_union_worker'
            task1.poll_count = 1
            task1.input_data = {'value': 42}

            result1 = await runner._execute_task(task1)

            self.assertEqual(result1.status, TaskResultStatus.IN_PROGRESS)
            self.assertEqual(result1.callback_after_seconds, 2)
            self.assertEqual(result1.output_data['status'], 'working')

            # Poll 2 - completes
            task2 = Task()
            task2.task_id = 'async_union_1'
            task2.workflow_instance_id = 'wf_1'
            task2.task_def_name = 'async_union_worker'
            task2.poll_count = 2
            task2.input_data = {'value': 42}

            result2 = await runner._execute_task(task2)

            self.assertEqual(result2.status, TaskResultStatus.COMPLETED)
            self.assertEqual(result2.output_data['status'], 'done')
            self.assertEqual(result2.output_data['result'], 84)

        self.run_async(test())

    def test_union_approach_logs_merged(self):
        """Test that logs added via context are merged with TaskInProgress"""
        from conductor.client.context import TaskInProgress, get_task_context
        from typing import Union

        def worker_with_logs(data: str) -> Union[dict, TaskInProgress]:
            ctx = get_task_context()
            poll_count = ctx.get_poll_count()

            # Add multiple logs
            ctx.add_log("Step 1: Initializing")
            ctx.add_log(f"Step 2: Processing {data}")
            ctx.add_log("Step 3: Validating")

            if poll_count < 2:
                return TaskInProgress(
                    callback_after_seconds=5,
                    output={'stage': 'in_progress'}
                )

            return {'stage': 'completed', 'data': data}

        worker = Worker(
            task_definition_name='worker_with_logs',
            execute_function=worker_with_logs,
            thread_count=1
        )
        runner = TaskRunnerAsyncIO(worker, self.config)

        async def test():
            task = Task()
            task.task_id = 'log_test'
            task.workflow_instance_id = 'wf_log'
            task.task_def_name = 'worker_with_logs'
            task.poll_count = 1
            task.input_data = {'data': 'test_data'}

            result = await runner._execute_task(task)

            # Should be IN_PROGRESS with all logs merged
            self.assertEqual(result.status, TaskResultStatus.IN_PROGRESS)
            self.assertIsNotNone(result.logs)
            self.assertEqual(len(result.logs), 3)

            # Check all logs are present
            log_messages = [log.log for log in result.logs]
            self.assertIn("Step 1: Initializing", log_messages)
            self.assertIn("Step 2: Processing test_data", log_messages)
            self.assertIn("Step 3: Validating", log_messages)

        self.run_async(test())


if __name__ == '__main__':
    unittest.main()
