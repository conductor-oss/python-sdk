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

        # Execute multiple times - should reuse the same background loop
        results = []
        for i in range(5):
            result = worker.execute(self.task)
            results.append(result)

        # Verify all executions succeeded
        for result in results:
            self.assertIsInstance(result, TaskResult)
            self.assertEqual(result.status, TaskResultStatus.COMPLETED)
            self.assertEqual(result.output_data["result"], 84)

        # Verify worker has initialized background loop
        self.assertIsNotNone(worker._background_loop)
        self.assertIsInstance(worker._background_loop, BackgroundEventLoop)

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
        """Test that background loop improves performance vs asyncio.run()."""
        async def async_execute(task: Task) -> dict:
            await asyncio.sleep(0.0001)  # Very short async work
            return {"result": "done"}

        worker = Worker("test_task", async_execute)

        # Warm up - initialize the background loop
        worker.execute(self.task)

        # Measure time for multiple executions with background loop
        start = time.time()
        for _ in range(100):
            worker.execute(self.task)
        background_loop_time = time.time() - start

        # Compare with asyncio.run() approach (simulated)
        start = time.time()
        for _ in range(100):
            async def task_coro():
                await asyncio.sleep(0.0001)
                return {"result": "done"}
            asyncio.run(task_coro())
        asyncio_run_time = time.time() - start

        # Background loop should be faster
        # (In practice, asyncio.run() has overhead from creating/destroying event loop)
        speedup = asyncio_run_time / background_loop_time if background_loop_time > 0 else 0
        print(f"\nBackground loop time: {background_loop_time:.3f}s")
        print(f"asyncio.run() time: {asyncio_run_time:.3f}s")
        print(f"Speedup: {speedup:.2f}x")

        # Background loop should be faster than asyncio.run()
        # Note: The exact speedup varies by system, but it should always be faster
        # We use a lenient threshold since system load can affect results
        self.assertLess(background_loop_time, asyncio_run_time,
                       "Background loop should be faster than asyncio.run()")

        # Verify there's at least SOME improvement (even 5% is meaningful)
        # In typical conditions, speedup is 1.5-2x, but we're lenient for CI environments
        self.assertGreater(speedup, 1.0,
                          f"Background loop should provide speedup (got {speedup:.2f}x)")

    def test_background_loop_handles_exceptions(self):
        """Test that background loop properly handles async exceptions."""
        async def failing_async_execute(task: Task) -> dict:
            await asyncio.sleep(0.001)
            raise ValueError("Test exception")

        worker = Worker("test_task", failing_async_execute)
        result = worker.execute(self.task)

        # Should handle exception and return FAILED status
        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.status, TaskResultStatus.FAILED)
        self.assertIn("Test exception", result.reason_for_incompletion or "")

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
            results.append(result)

        threads = [threading.Thread(target=execute_task, args=(w,)) for w in workers]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All executions should succeed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result.status, TaskResultStatus.COMPLETED)

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

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data["result"], 30)


    def test_background_loop_timeout_handling(self):
        """Test that long-running async tasks respect timeout."""
        async def long_running_task(task: Task) -> dict:
            await asyncio.sleep(10)  # Simulate long-running task
            return {"result": "done"}

        worker = Worker("test_task", long_running_task)

        # Initialize the loop first
        async def quick_task(task: Task) -> dict:
            return {"result": "init"}

        worker.execute_function = quick_task
        worker.execute(self.task)
        worker.execute_function = long_running_task

        # Now mock the run_coroutine to simulate timeout
        import unittest.mock
        if worker._background_loop:
            with unittest.mock.patch.object(
                worker._background_loop,
                'run_coroutine'
            ) as mock_run:
                # Simulate timeout
                mock_run.side_effect = TimeoutError("Coroutine execution timed out")

                result = worker.execute(self.task)

                # Should handle timeout gracefully and return failed result
                self.assertEqual(result.status, TaskResultStatus.FAILED)

    def test_background_loop_handles_closed_loop(self):
        """Test graceful fallback when loop is closed."""
        async def async_execute(task: Task) -> dict:
            return {"result": "done"}

        worker = Worker("test_task", async_execute)

        # Initialize the loop
        worker.execute(self.task)

        # Simulate loop being closed
        if worker._background_loop:
            original_is_closed = worker._background_loop._loop.is_closed

            def mock_is_closed():
                return True

            worker._background_loop._loop.is_closed = mock_is_closed

            # Should fall back to asyncio.run()
            result = worker.execute(self.task)
            self.assertEqual(result.status, TaskResultStatus.COMPLETED)

            # Restore
            worker._background_loop._loop.is_closed = original_is_closed

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

        # Exception should be caught and result should be FAILED
        self.assertEqual(result.status, TaskResultStatus.FAILED)
        # The exception message should be in the result
        self.assertIsNotNone(result.reason_for_incompletion)


if __name__ == '__main__':
    unittest.main(verbosity=2)
