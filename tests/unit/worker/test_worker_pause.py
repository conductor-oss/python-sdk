"""
Tests for worker pause functionality via environment variables.

Tests cover:
1. Global pause (conductor.worker.all.paused)
2. Task-specific pause (conductor.worker.<taskType>.paused)
3. Boolean value parsing (_get_env_bool)
4. Pause precedence (task-specific over global)
5. Pause metrics tracking
6. Edge cases and invalid values
"""

import os
import unittest
from unittest.mock import Mock, patch

from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_interface import _get_env_bool
from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.configuration.configuration import Configuration

try:
    import httpx
except ImportError:
    httpx = None


class TestWorkerPause(unittest.TestCase):
    """Test worker pause functionality"""

    def setUp(self):
        """Clean up environment variables before each test"""
        # Remove any pause-related env vars
        for key in list(os.environ.keys()):
            if 'conductor.worker' in key and 'paused' in key:
                del os.environ[key]

    def tearDown(self):
        """Clean up environment variables after each test"""
        for key in list(os.environ.keys()):
            if 'conductor.worker' in key and 'paused' in key:
                del os.environ[key]

    # =========================================================================
    # Boolean Parsing Tests
    # =========================================================================

    def test_get_env_bool_true_values(self):
        """Test _get_env_bool recognizes true values"""
        true_values = ['true', '1', 'yes']

        for value in true_values:
            with self.subTest(value=value):
                os.environ['test_bool'] = value
                result = _get_env_bool('test_bool')
                self.assertTrue(result, f"'{value}' should be True")
                del os.environ['test_bool']

    def test_get_env_bool_false_values(self):
        """Test _get_env_bool recognizes false values"""
        false_values = ['false', '0', 'no']

        for value in false_values:
            with self.subTest(value=value):
                os.environ['test_bool'] = value
                result = _get_env_bool('test_bool')
                self.assertFalse(result, f"'{value}' should be False")
                del os.environ['test_bool']

    def test_get_env_bool_case_insensitive(self):
        """Test _get_env_bool is case insensitive"""
        # True variations
        for value in ['TRUE', 'True', 'TrUe', 'YES', 'Yes']:
            with self.subTest(value=value):
                os.environ['test_bool'] = value
                result = _get_env_bool('test_bool')
                self.assertTrue(result, f"'{value}' should be True")
                del os.environ['test_bool']

        # False variations
        for value in ['FALSE', 'False', 'FaLsE', 'NO', 'No']:
            with self.subTest(value=value):
                os.environ['test_bool'] = value
                result = _get_env_bool('test_bool')
                self.assertFalse(result, f"'{value}' should be False")
                del os.environ['test_bool']

    def test_get_env_bool_invalid_values(self):
        """Test _get_env_bool returns default for invalid values"""
        invalid_values = ['2', 'invalid', 'yes!', 'nope', '']

        for value in invalid_values:
            with self.subTest(value=value):
                os.environ['test_bool'] = value
                result = _get_env_bool('test_bool', default=False)
                self.assertFalse(result, f"'{value}' should return default (False)")

                result = _get_env_bool('test_bool', default=True)
                self.assertTrue(result, f"'{value}' should return default (True)")

                del os.environ['test_bool']

    def test_get_env_bool_not_set(self):
        """Test _get_env_bool returns default when env var not set"""
        result = _get_env_bool('nonexistent_key')
        self.assertFalse(result, "Should return default False")

        result = _get_env_bool('nonexistent_key', default=True)
        self.assertTrue(result, "Should return default True")

    def test_get_env_bool_empty_string(self):
        """Test _get_env_bool with empty string"""
        os.environ['test_bool'] = ''
        result = _get_env_bool('test_bool')
        self.assertFalse(result, "Empty string should return default False")

    def test_get_env_bool_whitespace(self):
        """Test _get_env_bool with whitespace"""
        # Note: .lower() is called but no .strip(), so whitespace matters
        os.environ['test_bool'] = '  true  '
        result = _get_env_bool('test_bool')
        self.assertFalse(result, "Whitespace should cause default return")

    # =========================================================================
    # Worker Pause Tests
    # =========================================================================

    def test_worker_not_paused_by_default(self):
        """Test worker is not paused when no env vars set"""
        worker = Worker('test_task', lambda task: {'result': 'ok'})
        self.assertFalse(worker.paused())

    def test_worker_paused_globally(self):
        """Test worker is paused when conductor.worker.all.paused=true"""
        os.environ['conductor.worker.all.paused'] = 'true'

        worker = Worker('test_task', lambda task: {'result': 'ok'})
        self.assertTrue(worker.paused())

    def test_worker_paused_task_specific(self):
        """Test worker is paused when conductor.worker.<taskType>.paused=true"""
        os.environ['conductor.worker.test_task.paused'] = 'true'

        worker = Worker('test_task', lambda task: {'result': 'ok'})
        self.assertTrue(worker.paused())

    def test_worker_pause_task_specific_takes_precedence(self):
        """Test task-specific pause adds on top of global pause"""
        # Global says not paused, task-specific says paused
        os.environ['conductor.worker.all.paused'] = 'false'
        os.environ['conductor.worker.test_task.paused'] = 'true'

        worker = Worker('test_task', lambda task: {'result': 'ok'})
        self.assertTrue(worker.paused(), "Task-specific pause should pause the worker")

        # Both paused
        os.environ['conductor.worker.all.paused'] = 'true'
        os.environ['conductor.worker.test_task.paused'] = 'true'

        worker = Worker('test_task', lambda task: {'result': 'ok'})
        self.assertTrue(worker.paused(), "Worker should be paused when both set to true")

        # Note: Task-specific cannot override global pause to unpause
        # This is by design - only pause can be added, not removed

    def test_worker_pause_different_task_types(self):
        """Test different task types can have different pause states"""
        os.environ['conductor.worker.task1.paused'] = 'true'
        os.environ['conductor.worker.task2.paused'] = 'false'

        worker1 = Worker('task1', lambda task: {'result': 'ok'})
        worker2 = Worker('task2', lambda task: {'result': 'ok'})
        worker3 = Worker('task3', lambda task: {'result': 'ok'})

        self.assertTrue(worker1.paused())
        self.assertFalse(worker2.paused())
        self.assertFalse(worker3.paused())

    def test_worker_global_pause_affects_all_tasks(self):
        """Test global pause affects all task types"""
        os.environ['conductor.worker.all.paused'] = 'true'

        worker1 = Worker('task1', lambda task: {'result': 'ok'})
        worker2 = Worker('task2', lambda task: {'result': 'ok'})
        worker3 = Worker('task3', lambda task: {'result': 'ok'})

        self.assertTrue(worker1.paused())
        self.assertTrue(worker2.paused())
        self.assertTrue(worker3.paused())

    def test_worker_pause_with_list_of_task_names(self):
        """Test pause works with worker handling multiple task types"""
        os.environ['conductor.worker.task1.paused'] = 'true'

        worker = Worker(['task1', 'task2'], lambda task: {'result': 'ok'})

        # First task in list should be checked
        task_name = worker.get_task_definition_name()
        self.assertIn(task_name, ['task1', 'task2'])

        # If task1 is returned, should be paused
        if task_name == 'task1':
            self.assertTrue(worker.paused())

    def test_worker_unpause(self):
        """Test worker can be unpaused by removing/changing env var"""
        os.environ['conductor.worker.all.paused'] = 'true'
        worker = Worker('test_task', lambda task: {'result': 'ok'})
        self.assertTrue(worker.paused())

        # Unpause
        os.environ['conductor.worker.all.paused'] = 'false'
        self.assertFalse(worker.paused())

        # Or delete entirely
        del os.environ['conductor.worker.all.paused']
        self.assertFalse(worker.paused())

    # =========================================================================
    # Integration Tests with TaskRunner
    # =========================================================================

    @unittest.skipIf(httpx is None, "httpx not installed")
    def test_paused_worker_skips_polling(self):
        """Test paused worker returns empty list without polling"""
        os.environ['conductor.worker.test_task.paused'] = 'true'

        config = Configuration(server_api_url='http://localhost:8080/api')
        worker = Worker('test_task', lambda task: {'result': 'ok'})

        # Create metrics settings so metrics_collector gets created
        import tempfile
        metrics_dir = tempfile.mkdtemp()
        from conductor.client.configuration.settings.metrics_settings import MetricsSettings
        metrics_settings = MetricsSettings(directory=metrics_dir, file_name='test.prom')

        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=config,
            metrics_settings=metrics_settings
        )

        # Mock the metrics_collector's method
        runner.metrics_collector.increment_task_paused = Mock()

        import asyncio

        async def run_test():
            # Mock HTTP client (should not be called)
            runner.http_client = Mock()
            runner.http_client.get = Mock()

            # Poll should return empty without HTTP call
            tasks = await runner.poll_and_execute_task()

            # Should return empty list
            self.assertEqual(tasks, [])

            # HTTP client should not be called
            runner.http_client.get.assert_not_called()

            # Metrics should record pause
            runner.metrics_collector.increment_task_paused.assert_called_once_with('test_task')

            # Cleanup
            import shutil
            shutil.rmtree(metrics_dir, ignore_errors=True)

        asyncio.run(run_test())

    @unittest.skipIf(httpx is None, "httpx not installed")
    def test_active_worker_polls_normally(self):
        """Test active (not paused) worker polls normally"""
        # No pause env vars set
        config = Configuration(server_api_url='http://localhost:8080/api')
        worker = Worker('test_task', lambda task: {'result': 'ok'})

        # Create metrics settings so metrics_collector gets created
        import tempfile
        metrics_dir = tempfile.mkdtemp()
        from conductor.client.configuration.settings.metrics_settings import MetricsSettings
        metrics_settings = MetricsSettings(directory=metrics_dir, file_name='test.prom')

        runner = TaskRunnerAsyncIO(
            worker=worker,
            configuration=config,
            metrics_settings=metrics_settings
        )

        # Mock the metrics_collector's method
        runner.metrics_collector.increment_task_paused = Mock()
        runner.metrics_collector.record_api_request_time = Mock()

        import asyncio
        from unittest.mock import AsyncMock

        async def run_test():
            # Mock HTTP client
            runner.http_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            runner.http_client.get = AsyncMock(return_value=mock_response)

            # Poll should make HTTP call
            await runner.poll_and_execute_task()

            # HTTP client should be called
            runner.http_client.get.assert_called()

            # Pause metric should NOT be called
            runner.metrics_collector.increment_task_paused.assert_not_called()

            # Cleanup
            import shutil
            shutil.rmtree(metrics_dir, ignore_errors=True)

        asyncio.run(run_test())

    def test_worker_pause_custom_logic(self):
        """Test custom pause logic can be implemented by subclassing"""
        class CustomWorker(Worker):
            def __init__(self, task_name, execute_fn):
                super().__init__(task_name, execute_fn)
                self.custom_pause = False

            def paused(self):
                # Custom logic: pause if custom flag OR env var
                return self.custom_pause or super().paused()

        worker = CustomWorker('test_task', lambda task: {'result': 'ok'})

        # Not paused initially
        self.assertFalse(worker.paused())

        # Custom pause
        worker.custom_pause = True
        self.assertTrue(worker.paused())

        # Env var also works
        worker.custom_pause = False
        os.environ['conductor.worker.all.paused'] = 'true'
        self.assertTrue(worker.paused())


if __name__ == '__main__':
    unittest.main()
