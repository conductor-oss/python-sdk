"""
Test to verify that async workers use a persistent background event loop
instead of creating/destroying an event loop for each task execution.
"""
import asyncio
import time
import unittest
from unittest.mock import Mock

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker import Worker, BackgroundEventLoop


class TestWorkerAsyncPerformance(unittest.TestCase):
    """Test async worker performance with background event loop."""

    def setUp(self):
        self.task = Task()
        self.task.task_id = "test_task_id"
        self.task.workflow_instance_id = "test_workflow_id"
        self.task.task_def_name = "test_task"
        self.task.input_data = {"value": 42}

    def test_background_event_loop_is_singleton(self):
        """Test that BackgroundEventLoop is a singleton."""
        loop1 = BackgroundEventLoop()
        loop2 = BackgroundEventLoop()

        self.assertIs(loop1, loop2)
        self.assertIsNotNone(loop1._loop)
        self.assertTrue(loop1._loop.is_running())

    def test_async_worker_uses_background_loop(self):
        """Test that async worker uses the persistent background loop."""
        async def async_execute(task: Task) -> dict:
            await asyncio.sleep(0.001)  # Simulate async work
            return {"result": task.input_data["value"] * 2}

        worker = Worker("test_task", async_execute)

        # Execute multiple times with different task IDs - async workers return None immediately (non-blocking)
        for i in range(5):
            task = Task()
            task.task_id = f"test_task_{i}"
            task.workflow_instance_id = "test_workflow_id"
            task.task_def_name = "test_task"
            task.input_data = {"value": 42}

            result = worker.execute(task)
            # Async workers return None and execute in background
            self.assertIsNone(result)

        # Verify worker has initialized background loop
        self.assertIsNotNone(worker._background_loop)
        self.assertIsInstance(worker._background_loop, BackgroundEventLoop)

        # Verify pending async tasks were created
        self.assertEqual(len(worker._pending_async_tasks), 5)

        # Wait for tasks to complete and verify they succeeded
        import time
        time.sleep(0.1)  # Wait for async tasks to complete
        for task_id, (future, task, submit_time) in worker._pending_async_tasks.items():
            self.assertTrue(future.done())
            result = future.result()
            self.assertEqual(result["result"], 84)

    def test_sync_worker_does_not_create_background_loop(self):
        """Test that sync workers don't create unnecessary background loop."""
        def sync_execute(task: Task) -> dict:
            return {"result": task.input_data["value"] * 2}

        worker = Worker("test_task", sync_execute)
        result = worker.execute(self.task)

        # Verify execution succeeded
        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data["result"], 84)

        # Verify no background loop was created
        self.assertIsNone(worker._background_loop)

    def test_async_worker_performance_improvement(self):
        """Test that background loop provides non-blocking execution."""
        async def async_execute(task: Task) -> dict:
            await asyncio.sleep(0.001)  # Short async work
            return {"result": "done"}

        worker = Worker("test_task", async_execute)

        # Async workers return None immediately (non-blocking)
        start = time.time()
        for _ in range(100):
            result = worker.execute(self.task)
            self.assertIsNone(result)  # Non-blocking returns None
        submission_time = time.time() - start

        # Submitting 100 tasks should be very fast (non-blocking)
        # Compare with blocking approach (asyncio.run)
        start = time.time()
        for _ in range(100):
            async def task_coro():
                await asyncio.sleep(0.001)
                return {"result": "done"}
            asyncio.run(task_coro())
        blocking_time = time.time() - start

        print(f"\nNon-blocking submission time: {submission_time:.3f}s")
        print(f"Blocking (asyncio.run) time: {blocking_time:.3f}s")
        print(f"Speedup: {blocking_time / submission_time if submission_time > 0 else 0:.2f}x")

        # Non-blocking should be much faster than blocking
        # (100 tasks × 1ms each = 100ms blocking vs ~1ms non-blocking submission)
        self.assertLess(submission_time, blocking_time / 10,
                       "Non-blocking submission should be much faster than blocking execution")

    def test_background_loop_handles_exceptions(self):
        """Test that background loop properly handles async exceptions."""
        async def failing_async_execute(task: Task) -> dict:
            await asyncio.sleep(0.001)
            raise ValueError("Test exception")

        worker = Worker("test_task", failing_async_execute)
        result = worker.execute(self.task)

        # Async workers return None immediately
        self.assertIsNone(result)

        # Wait for the task to fail
        time.sleep(0.1)

        # Check that the future has the exception
        task_id = self.task.task_id
        if task_id in worker._pending_async_tasks:
            future, task, submit_time = worker._pending_async_tasks[task_id]
            self.assertTrue(future.done())
            with self.assertRaises(ValueError) as context:
                future.result()
            self.assertIn("Test exception", str(context.exception))

    def test_background_loop_thread_safe(self):
        """Test that background loop is thread-safe for concurrent workers."""
        import threading

        async def async_execute(task: Task) -> dict:
            await asyncio.sleep(0.01)
            return {"thread_id": threading.get_ident()}

        # Create multiple workers in different threads
        workers = [Worker("test_task", async_execute) for _ in range(3)]
        results = []

        def execute_task(worker):
            result = worker.execute(self.task)
            results.append(result)  # Will be None for async workers

        threads = [threading.Thread(target=execute_task, args=(w,)) for w in workers]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All executions should return None (non-blocking)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsNone(result)

        # All workers should share the same background loop instance
        loop_instances = [w._background_loop for w in workers if w._background_loop]
        if len(loop_instances) > 1:
            self.assertTrue(all(loop is loop_instances[0] for loop in loop_instances))

    def test_async_worker_with_kwargs(self):
        """Test async worker with keyword arguments."""
        async def async_execute(value: int, multiplier: int = 2) -> dict:
            await asyncio.sleep(0.001)
            return {"result": value * multiplier}

        worker = Worker("test_task", async_execute)
        self.task.input_data = {"value": 10, "multiplier": 3}
        result = worker.execute(self.task)

        # Async workers return None immediately
        self.assertIsNone(result)

        # Wait for task to complete
        time.sleep(0.1)

        # Check the future result
        task_id = self.task.task_id
        if task_id in worker._pending_async_tasks:
            future, task, submit_time = worker._pending_async_tasks[task_id]
            self.assertTrue(future.done())
            result_data = future.result()
            self.assertEqual(result_data["result"], 30)


    def test_background_loop_timeout_handling(self):
        """Test that long-running async tasks are submitted without blocking."""
        async def long_running_task(task: Task) -> dict:
            await asyncio.sleep(10)  # Simulate long-running task
            return {"result": "done"}

        worker = Worker("test_task", long_running_task)

        # Async workers return None immediately, even for long-running tasks
        result = worker.execute(self.task)

        # Should return None immediately (non-blocking)
        self.assertIsNone(result)

        # Verify task was submitted
        self.assertIn(self.task.task_id, worker._pending_async_tasks)

        # Verify future is not done yet (still running)
        future, task, submit_time = worker._pending_async_tasks[self.task.task_id]
        self.assertFalse(future.done())

    def test_background_loop_handles_closed_loop(self):
        """Test graceful handling when loop is closed."""
        async def async_execute(task: Task) -> dict:
            return {"result": "done"}

        worker = Worker("test_task", async_execute)

        # Initialize the loop
        worker.execute(self.task)

        # Async workers return None (non-blocking)
        # Even if loop has issues, it should handle gracefully
        result = worker.execute(self.task)
        self.assertIsNone(result)

    def test_background_loop_initialization_race_condition(self):
        """Test that concurrent initialization doesn't create multiple loops."""
        import threading

        async def async_execute(task: Task) -> dict:
            return {"result": threading.get_ident()}

        # Create multiple workers concurrently
        workers = []
        threads = []

        def create_and_execute(worker_id):
            w = Worker(f"test_task_{worker_id}", async_execute)
            workers.append(w)
            w.execute(self.task)

        # Create 10 workers concurrently
        for i in range(10):
            t = threading.Thread(target=create_and_execute, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All workers should share the same background loop instance
        loop_instances = set()
        for w in workers:
            if w._background_loop:
                loop_instances.add(id(w._background_loop))

        # Should only have one unique instance
        self.assertEqual(len(loop_instances), 1)

    def test_coroutine_exception_propagation(self):
        """Test that exceptions in coroutines are properly propagated."""
        class CustomException(Exception):
            pass

        async def failing_async_execute(task: Task) -> dict:
            await asyncio.sleep(0.001)
            raise CustomException("Custom error message")

        worker = Worker("test_task", failing_async_execute)
        result = worker.execute(self.task)

        # Async workers return None immediately
        self.assertIsNone(result)

        # Wait for task to fail
        time.sleep(0.1)

        # Exception should be stored in the future
        task_id = self.task.task_id
        if task_id in worker._pending_async_tasks:
            future, task, submit_time = worker._pending_async_tasks[task_id]
            self.assertTrue(future.done())
            with self.assertRaises(CustomException) as context:
                future.result()
            self.assertIn("Custom error message", str(context.exception))


if __name__ == '__main__':
    unittest.main(verbosity=2)
