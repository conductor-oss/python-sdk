"""
Unit tests for update-task-v2 graceful degradation to v1.

Tests both sync TaskRunner and async AsyncTaskRunner to verify:
- On 404/501 from update_task_v2, falls back to update_task (v1)
- The _v2_available flag is set to False after first fallback
- Subsequent calls go directly to v1 (skip v2)
- The current task result is still persisted via v1 during fallback
"""

import asyncio
import logging
import unittest
from unittest.mock import patch, Mock, AsyncMock

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.automator.async_task_runner import AsyncTaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.http.rest import ApiException
from conductor.client.worker.worker import Worker
from tests.unit.resources.workers import ClassWorker


class TestTaskRunnerV2Fallback(unittest.TestCase):
    """Tests for sync TaskRunner v2 -> v1 fallback."""

    TASK_ID = 'test_task_id'
    WORKFLOW_INSTANCE_ID = 'test_workflow_id'

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @patch('time.sleep', Mock(return_value=None))
    def test_fallback_on_404(self):
        """On 404 from update_task_v2, should fall back to update_task and return None."""
        with patch.object(
            TaskResourceApi, 'update_task_v2',
            side_effect=ApiException(status=404, reason="Not Found")
        ):
            with patch.object(
                TaskResourceApi, 'update_task',
                return_value='task_id_confirmation'
            ) as mock_v1:
                runner = self._create_runner()
                self.assertTrue(runner._v2_available)

                result = runner._TaskRunner__update_task(self._create_task_result())

                self.assertIsNone(result)
                self.assertFalse(runner._v2_available)
                mock_v1.assert_called_once()

    @patch('time.sleep', Mock(return_value=None))
    def test_fallback_on_501(self):
        """On 501 from update_task_v2, should fall back to update_task and return None."""
        with patch.object(
            TaskResourceApi, 'update_task_v2',
            side_effect=ApiException(status=501, reason="Not Implemented")
        ):
            with patch.object(
                TaskResourceApi, 'update_task',
                return_value='task_id_confirmation'
            ) as mock_v1:
                runner = self._create_runner()
                result = runner._TaskRunner__update_task(self._create_task_result())

                self.assertIsNone(result)
                self.assertFalse(runner._v2_available)
                mock_v1.assert_called_once()

    @patch('time.sleep', Mock(return_value=None))
    def test_subsequent_calls_use_v1_directly(self):
        """After fallback, subsequent calls should go to v1 directly, skipping v2."""
        with patch.object(
            TaskResourceApi, 'update_task_v2',
            side_effect=ApiException(status=404, reason="Not Found")
        ) as mock_v2:
            with patch.object(
                TaskResourceApi, 'update_task',
                return_value='ok'
            ) as mock_v1:
                runner = self._create_runner()

                # First call triggers fallback
                runner._TaskRunner__update_task(self._create_task_result())
                self.assertEqual(mock_v2.call_count, 1)
                self.assertEqual(mock_v1.call_count, 1)

                # Second call should skip v2 entirely
                runner._TaskRunner__update_task(self._create_task_result())
                self.assertEqual(mock_v2.call_count, 1)  # Still 1 — not called again
                self.assertEqual(mock_v1.call_count, 2)

    @patch('time.sleep', Mock(return_value=None))
    def test_v2_success_no_fallback(self):
        """When v2 succeeds, should return next task and not touch v1."""
        next_task = Task(task_id='next_task', workflow_instance_id='wf_2')
        with patch.object(
            TaskResourceApi, 'update_task_v2',
            return_value=next_task
        ):
            with patch.object(
                TaskResourceApi, 'update_task',
                return_value='ok'
            ) as mock_v1:
                runner = self._create_runner()
                result = runner._TaskRunner__update_task(self._create_task_result())

                self.assertEqual(result, next_task)
                self.assertTrue(runner._v2_available)
                mock_v1.assert_not_called()

    @patch('time.sleep', Mock(return_value=None))
    def test_non_404_error_does_not_trigger_fallback(self):
        """A 500 error should retry normally, not trigger v1 fallback."""
        with patch.object(
            TaskResourceApi, 'update_task_v2',
            side_effect=ApiException(status=500, reason="Internal Server Error")
        ):
            runner = self._create_runner()
            result = runner._TaskRunner__update_task(self._create_task_result())

            # All retries exhausted, still v2_available (not a 404/501)
            self.assertTrue(runner._v2_available)
            self.assertIsNone(result)

    @patch('time.sleep', Mock(return_value=None))
    def test_v1_fallback_failure_retries(self):
        """If v1 also fails during fallback, should retry with backoff."""
        call_count = {'v1': 0}

        def v1_side_effect(**kwargs):
            call_count['v1'] += 1
            if call_count['v1'] <= 2:
                raise Exception("v1 also down")
            return 'ok'

        with patch.object(
            TaskResourceApi, 'update_task_v2',
            side_effect=ApiException(status=404, reason="Not Found")
        ):
            with patch.object(
                TaskResourceApi, 'update_task',
                side_effect=v1_side_effect
            ):
                runner = self._create_runner()
                result = runner._TaskRunner__update_task(self._create_task_result())

                self.assertFalse(runner._v2_available)
                # First v1 call fails (immediate fallback), then retries succeed
                self.assertIsNone(result)

    def _create_runner(self):
        return TaskRunner(
            configuration=Configuration(),
            worker=ClassWorker('task')
        )

    def _create_task_result(self):
        return TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id='test_worker',
            status=TaskResultStatus.COMPLETED,
            output_data={'result': 42}
        )


class TestAsyncTaskRunnerV2Fallback(unittest.TestCase):
    """Tests for async AsyncTaskRunner v2 -> v1 fallback."""

    TASK_ID = 'test_task_id'
    WORKFLOW_INSTANCE_ID = 'test_workflow_id'
    AUTH_TOKEN = 'test_token'

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_fallback_on_404(self):
        """On 404 from async update_task_v2, should fall back to update_task."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_v2_fallback',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN
        runner = AsyncTaskRunner(worker=worker, configuration=config)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.update_task_v2 = AsyncMock(
                side_effect=ApiException(status=404, reason="Not Found")
            )
            runner.async_task_client.update_task = AsyncMock(return_value='ok')

            self.assertTrue(runner._v2_available)

            result = await runner._AsyncTaskRunner__async_update_task(self._create_task_result())

            self.assertIsNone(result)
            self.assertFalse(runner._v2_available)
            runner.async_task_client.update_task.assert_called_once()

        asyncio.run(run_test())

    def test_fallback_on_501(self):
        """On 501 from async update_task_v2, should fall back to update_task."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_v2_fallback_501',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN
        runner = AsyncTaskRunner(worker=worker, configuration=config)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.update_task_v2 = AsyncMock(
                side_effect=ApiException(status=501, reason="Not Implemented")
            )
            runner.async_task_client.update_task = AsyncMock(return_value='ok')

            result = await runner._AsyncTaskRunner__async_update_task(self._create_task_result())

            self.assertIsNone(result)
            self.assertFalse(runner._v2_available)
            runner.async_task_client.update_task.assert_called_once()

        asyncio.run(run_test())

    def test_subsequent_calls_use_v1_directly(self):
        """After fallback, subsequent async calls should go to v1 directly."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_v2_subsequent',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN
        runner = AsyncTaskRunner(worker=worker, configuration=config)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.update_task_v2 = AsyncMock(
                side_effect=ApiException(status=404, reason="Not Found")
            )
            runner.async_task_client.update_task = AsyncMock(return_value='ok')

            # First call triggers fallback
            await runner._AsyncTaskRunner__async_update_task(self._create_task_result())
            self.assertEqual(runner.async_task_client.update_task_v2.call_count, 1)
            self.assertEqual(runner.async_task_client.update_task.call_count, 1)

            # Second call skips v2
            await runner._AsyncTaskRunner__async_update_task(self._create_task_result())
            self.assertEqual(runner.async_task_client.update_task_v2.call_count, 1)  # Still 1
            self.assertEqual(runner.async_task_client.update_task.call_count, 2)

        asyncio.run(run_test())

    def test_v2_success_no_fallback(self):
        """When async v2 succeeds, should return next task and not touch v1."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_v2_success',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN
        runner = AsyncTaskRunner(worker=worker, configuration=config)

        next_task = Task(task_id='next_task', workflow_instance_id='wf_2')

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.update_task_v2 = AsyncMock(return_value=next_task)
            runner.async_task_client.update_task = AsyncMock(return_value='ok')

            result = await runner._AsyncTaskRunner__async_update_task(self._create_task_result())

            self.assertEqual(result, next_task)
            self.assertTrue(runner._v2_available)
            runner.async_task_client.update_task.assert_not_called()

        asyncio.run(run_test())

    def test_end_to_end_with_fallback(self):
        """Full end-to-end: poll -> execute -> update_v2 fails -> fallback to v1."""

        async def async_worker_fn(value: int) -> dict:
            return {'result': value * 2}

        worker = Worker(
            task_definition_name='test_e2e_fallback',
            execute_function=async_worker_fn,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN
        runner = AsyncTaskRunner(worker=worker, configuration=config)

        mock_task = Task()
        mock_task.task_id = self.TASK_ID
        mock_task.workflow_instance_id = self.WORKFLOW_INSTANCE_ID
        mock_task.task_def_name = 'test_e2e_fallback'
        mock_task.input_data = {'value': 10}
        mock_task.status = 'SCHEDULED'

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task_v2 = AsyncMock(
                side_effect=ApiException(status=404, reason="Not Found")
            )
            runner.async_task_client.update_task = AsyncMock(return_value='ok')

            await runner.run_once()
            await asyncio.sleep(0.1)

            # v2 was attempted, then fell back to v1
            runner.async_task_client.update_task_v2.assert_called_once()
            runner.async_task_client.update_task.assert_called_once()

            # Task result should have correct output
            v1_call = runner.async_task_client.update_task.call_args
            task_result = v1_call.kwargs['body']
            self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
            self.assertEqual(task_result.output_data, {'result': 20})

            # Flag should be flipped
            self.assertFalse(runner._v2_available)

        asyncio.run(run_test())

    def _create_task_result(self):
        return TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id='test_worker',
            status=TaskResultStatus.COMPLETED,
            output_data={'result': 42}
        )


if __name__ == '__main__':
    unittest.main()
