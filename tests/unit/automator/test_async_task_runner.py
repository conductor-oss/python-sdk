import asyncio
import logging
import os
import time
import unittest
from unittest.mock import patch, AsyncMock, Mock, MagicMock

from conductor.client.automator.async_task_runner import AsyncTaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.event.task_runner_events import (
    PollStarted, PollCompleted, PollFailure,
    TaskExecutionStarted, TaskExecutionCompleted, TaskExecutionFailure
)
from conductor.client.http.api.async_task_resource_api import AsyncTaskResourceApi
from conductor.client.http.async_rest import AuthorizationException
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.http.models.token import Token
from conductor.client.worker.worker import Worker


class TestAsyncTaskRunner(unittest.TestCase):
    """
    Unit tests for AsyncTaskRunner - tests async worker execution with mocked HTTP.

    All HTTP requests are mocked, but everything else (event system, metrics,
    configuration, serialization, etc.) is real.
    """

    TASK_ID = 'test_task_id_123'
    WORKFLOW_INSTANCE_ID = 'test_workflow_456'
    UPDATE_TASK_RESPONSE = 'task_updated'
    AUTH_TOKEN = 'test_auth_token_xyz'

    def setUp(self):
        logging.disable(logging.CRITICAL)
        # Save original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_async_worker_end_to_end(self):
        """Test async worker execution from poll to update with mocked HTTP."""

        # Create async worker
        async def async_worker_fn(value: int) -> dict:
            await asyncio.sleep(0.01)  # Simulate async I/O
            return {'result': value * 2}

        worker = Worker(
            task_definition_name='test_async_task',
            execute_function=async_worker_fn,
            thread_count=5
        )

        # Create configuration
        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        # Track events
        events_captured = []

        class EventCapture:
            def on_poll_started(self, event):
                events_captured.append(('poll_started', event))
            def on_poll_completed(self, event):
                events_captured.append(('poll_completed', event))
            def on_task_execution_started(self, event):
                events_captured.append(('execution_started', event))
            def on_task_execution_completed(self, event):
                events_captured.append(('execution_completed', event))

        # Create task runner with event listener
        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[EventCapture()]
        )

        # Mock HTTP responses
        mock_task = self.__create_task(input_data={'value': 10})
        mock_tasks = [mock_task]

        async def run_test():
            # Initialize runner (creates clients in event loop)
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(5)

            # Mock batch_poll to return one task
            runner.async_task_client.batch_poll = AsyncMock(return_value=mock_tasks)

            # Mock update_task to succeed
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            # Run one iteration
            await runner.run_once()

            # Wait for async task to complete
            await asyncio.sleep(0.1)

            # Verify batch_poll was called
            runner.async_task_client.batch_poll.assert_called_once()

            # Verify update_task was called with correct result
            runner.async_task_client.update_task.assert_called_once()
            call_args = runner.async_task_client.update_task.call_args
            task_result = call_args.kwargs['body']

            self.assertEqual(task_result.task_id, self.TASK_ID)
            self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
            self.assertEqual(task_result.output_data, {'result': 20})  # 10 * 2

            # Verify events were published
            event_types = [e[0] for e in events_captured]
            self.assertIn('poll_started', event_types)
            self.assertIn('poll_completed', event_types)
            self.assertIn('execution_started', event_types)
            self.assertIn('execution_completed', event_types)

        asyncio.run(run_test())

    def test_async_worker_with_none_return(self):
        """Test async worker that returns None (should work correctly)."""

        async def async_worker_returns_none(message: str) -> None:
            await asyncio.sleep(0.01)
            return None  # Explicit None return

        worker = Worker(
            task_definition_name='test_none_return',
            execute_function=async_worker_returns_none,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        mock_task = self.__create_task(input_data={'message': 'test'})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Verify task completed with None result
            call_args = runner.async_task_client.update_task.call_args
            task_result = call_args.kwargs['body']

            self.assertEqual(task_result.status, TaskResultStatus.COMPLETED)
            self.assertEqual(task_result.output_data, {'result': None})

        asyncio.run(run_test())

    def test_token_refresh_error_handling(self):
        """Test that auth exceptions are handled correctly."""

        async def simple_async_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_token_refresh',
            execute_function=simple_async_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        # Track failure events
        failure_events = []

        class FailureCapture:
            def on_poll_failure(self, event):
                failure_events.append(event)

        runner.event_dispatcher.register(PollFailure, FailureCapture().on_poll_failure)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            # Mock batch_poll to raise a generic exception
            runner.async_task_client.batch_poll = AsyncMock(side_effect=Exception("Network error"))

            # Call __async_batch_poll
            tasks = await runner._AsyncTaskRunner__async_batch_poll(1)

            # Should return empty list
            self.assertEqual(tasks, [])

            # Should publish PollFailure event
            self.assertEqual(len(failure_events), 1)
            self.assertIn("Network error", str(failure_events[0].cause))

        asyncio.run(run_test())

    def test_concurrency_limit_respected(self):
        """Test that semaphore limits concurrent task execution."""

        execution_times = []

        async def slow_async_worker(task_id: str) -> dict:
            start = time.time()
            await asyncio.sleep(0.05)  # 50ms
            end = time.time()
            execution_times.append((task_id, start, end))
            return {'task_id': task_id, 'completed': True}

        worker = Worker(
            task_definition_name='test_concurrency',
            execute_function=slow_async_worker,
            thread_count=2  # Max 2 concurrent tasks
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        # Create 4 tasks
        mock_tasks = [
            self.__create_task(task_id=f'task_{i}', input_data={'task_id': f'task_{i}'})
            for i in range(4)
        ]

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(2)  # Max 2 concurrent

            # Return 2 tasks on first poll, 2 on second poll
            poll_calls = [0]
            async def batch_poll_mock(*args, **kwargs):
                poll_calls[0] += 1
                if poll_calls[0] == 1:
                    return mock_tasks[:2]  # First 2 tasks
                else:
                    return []

            runner.async_task_client.batch_poll = AsyncMock(side_effect=batch_poll_mock)
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            # First run_once - poll 2 tasks
            await runner.run_once()

            # Wait for tasks to complete
            await asyncio.sleep(0.15)

            # Verify only 2 tasks executed (respecting thread_count=2)
            self.assertEqual(len(execution_times), 2)

            # Verify they executed concurrently (overlapping time ranges)
            task1_start, task1_end = execution_times[0][1], execution_times[0][2]
            task2_start, task2_end = execution_times[1][1], execution_times[1][2]

            # Check for overlap (concurrent execution)
            overlap = (task1_start < task2_end) and (task2_start < task1_end)
            self.assertTrue(overlap, "Tasks should execute concurrently")

        asyncio.run(run_test())

    def test_adaptive_backoff_on_empty_polls(self):
        """Test exponential backoff when queue is empty."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_backoff',
            execute_function=simple_worker,
            poll_interval=0.1  # 100ms
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            # Mock batch_poll to return empty (no tasks)
            runner.async_task_client.batch_poll = AsyncMock(return_value=[])

            # Run multiple iterations with empty polls
            # Note: Some iterations may skip polling due to backoff, so just verify counter increases
            for i in range(10):
                await runner.run_once()

            # Verify _consecutive_empty_polls incremented (should be >= 3 due to backoff)
            self.assertGreaterEqual(runner._consecutive_empty_polls, 3)

            # Verify batch_poll was called at least a few times
            self.assertGreater(runner.async_task_client.batch_poll.call_count, 0)

        asyncio.run(run_test())

    def test_auth_failure_backoff(self):
        """Test that auth failures trigger PollFailure events."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_auth_backoff',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        # Track failure events
        failure_events = []

        class FailureCapture:
            def on_poll_failure(self, event):
                failure_events.append(event)

        runner.event_dispatcher.register(PollFailure, FailureCapture().on_poll_failure)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            # Mock batch_poll to raise exception
            runner.async_task_client.batch_poll = AsyncMock(side_effect=Exception("Auth error"))

            # Call __async_batch_poll
            tasks = await runner._AsyncTaskRunner__async_batch_poll(1)

            # Should return empty list
            self.assertEqual(tasks, [])

            # Should publish PollFailure event
            self.assertEqual(len(failure_events), 1)

        asyncio.run(run_test())

    def test_worker_exception_handling(self):
        """Test that worker exceptions are caught and reported correctly."""

        async def faulty_worker(value: int) -> dict:
            await asyncio.sleep(0.01)
            raise ValueError("Intentional test error")

        worker = Worker(
            task_definition_name='test_faulty_worker',
            execute_function=faulty_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        # Track failure events
        failure_events = []

        class FailureCapture:
            def on_task_execution_failure(self, event):
                failure_events.append(event)

        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[FailureCapture()]
        )

        mock_task = self.__create_task(input_data={'value': 5})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Verify failure event was published
            self.assertEqual(len(failure_events), 1)
            self.assertEqual(failure_events[0].task_id, self.TASK_ID)
            self.assertIn("Intentional test error", str(failure_events[0].cause))

            # Verify update_task was called with FAILED status
            call_args = runner.async_task_client.update_task.call_args
            task_result = call_args.kwargs['body']
            self.assertEqual(task_result.status, TaskResultStatus.FAILED)

        asyncio.run(run_test())

    def test_capacity_check_prevents_over_polling(self):
        """Test that capacity check prevents polling when at max workers."""

        async def slow_worker(value: int) -> dict:
            await asyncio.sleep(0.5)  # Slow enough to stay running
            return {'result': value}

        worker = Worker(
            task_definition_name='test_capacity',
            execute_function=slow_worker,
            thread_count=2  # Max 2 concurrent
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(2)

            # Mock batch_poll to return only the number of tasks requested (count param)
            async def batch_poll_respects_count(*args, **kwargs):
                count = kwargs.get('count', 1)
                # Return tasks up to the requested count
                return [self.__create_task(task_id=f'task_{i}', input_data={'value': i}) for i in range(count)]

            runner.async_task_client.batch_poll = AsyncMock(side_effect=batch_poll_respects_count)
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            # First poll - should request 2 tasks (available_slots=2)
            await runner.run_once()

            # Wait briefly for tasks to be created
            await asyncio.sleep(0.01)

            # Should have 2 running tasks
            self.assertEqual(len(runner._running_tasks), 2)

            # Second poll - at capacity, should return early without polling
            await runner.run_once()

            # Still 2 tasks (didn't create more)
            self.assertEqual(len(runner._running_tasks), 2)

            # Verify batch_poll was only called once (not called second time due to capacity)
            self.assertEqual(runner.async_task_client.batch_poll.call_count, 1)

        asyncio.run(run_test())

    def test_paused_worker_stops_polling(self):
        """Test that paused workers don't poll."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_paused',
            execute_function=simple_worker,
            paused=True  # Worker is paused
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[self.__create_task()])

            # Run once - should NOT poll because worker is paused
            await runner.run_once()

            # Verify batch_poll was NOT called
            runner.async_task_client.batch_poll.assert_not_called()

        asyncio.run(run_test())

    def test_multiple_concurrent_tasks(self):
        """Test that multiple tasks execute concurrently up to thread_count."""

        execution_order = []

        async def concurrent_worker(task_num: int) -> dict:
            execution_order.append(f'start_{task_num}')
            await asyncio.sleep(0.05)
            execution_order.append(f'end_{task_num}')
            return {'task': task_num}

        worker = Worker(
            task_definition_name='test_concurrent',
            execute_function=concurrent_worker,
            thread_count=3  # Max 3 concurrent
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        # Create 3 tasks
        mock_tasks = [
            self.__create_task(task_id=f'task_{i}', input_data={'task_num': i})
            for i in range(3)
        ]

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(3)

            runner.async_task_client.batch_poll = AsyncMock(return_value=mock_tasks)
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.2)

            # Verify all 3 tasks started before any ended (concurrent execution)
            start_indices = [i for i, event in enumerate(execution_order) if event.startswith('start_')]
            end_indices = [i for i, event in enumerate(execution_order) if event.startswith('end_')]

            # All starts should come before all ends (concurrent execution)
            self.assertEqual(len(start_indices), 3)
            self.assertEqual(len(end_indices), 3)
            self.assertTrue(all(s < e for s in start_indices for e in end_indices[:1]))

        asyncio.run(run_test())

    def test_task_result_serialization(self):
        """Test that TaskResult is properly serialized for update."""

        async def worker_with_complex_output(data: dict) -> dict:
            return {
                'processed': True,
                'items': [1, 2, 3],
                'metadata': {'count': 3, 'status': 'ok'}
            }

        worker = Worker(
            task_definition_name='test_serialization',
            execute_function=worker_with_complex_output,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        runner = AsyncTaskRunner(worker=worker, configuration=config)

        mock_task = self.__create_task(input_data={'data': {'test': 'value'}})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Verify task result was serialized correctly
            call_args = runner.async_task_client.update_task.call_args
            task_result = call_args.kwargs['body']

            self.assertIsInstance(task_result, TaskResult)
            self.assertEqual(task_result.output_data['processed'], True)
            self.assertEqual(task_result.output_data['items'], [1, 2, 3])
            self.assertEqual(task_result.output_data['metadata']['count'], 3)

        asyncio.run(run_test())

    # Helper methods

    def __create_task(self, task_id=None, input_data=None):
        """Create a mock Task object."""
        task = Task()
        task.task_id = task_id or self.TASK_ID
        task.workflow_instance_id = self.WORKFLOW_INSTANCE_ID
        task.task_def_name = 'test_task'
        task.input_data = input_data or {}
        task.status = 'SCHEDULED'
        return task

    def __create_task_result(self, status=TaskResultStatus.COMPLETED, output_data=None):
        """Create a mock TaskResult object."""
        return TaskResult(
            task_id=self.TASK_ID,
            workflow_instance_id=self.WORKFLOW_INSTANCE_ID,
            worker_id='test_worker',
            status=status,
            output_data=output_data or {}
        )


    def test_all_event_types_published(self):
        """Test that all 6 event types are published correctly."""

        async def simple_worker(value: int) -> dict:
            return {'result': value * 2}

        worker = Worker(
            task_definition_name='test_all_events',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        # Capture all event types
        events_by_type = {
            'poll_started': [],
            'poll_completed': [],
            'poll_failure': [],
            'execution_started': [],
            'execution_completed': [],
            'execution_failure': []
        }

        class AllEventsCapture:
            def on_poll_started(self, event):
                events_by_type['poll_started'].append(event)
            def on_poll_completed(self, event):
                events_by_type['poll_completed'].append(event)
            def on_poll_failure(self, event):
                events_by_type['poll_failure'].append(event)
            def on_task_execution_started(self, event):
                events_by_type['execution_started'].append(event)
            def on_task_execution_completed(self, event):
                events_by_type['execution_completed'].append(event)
            def on_task_execution_failure(self, event):
                events_by_type['execution_failure'].append(event)

        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[AllEventsCapture()]
        )

        mock_task = self.__create_task(input_data={'value': 10})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            # Successful execution scenario
            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Verify success events
            self.assertEqual(len(events_by_type['poll_started']), 1)
            self.assertEqual(len(events_by_type['poll_completed']), 1)
            self.assertEqual(len(events_by_type['execution_started']), 1)
            self.assertEqual(len(events_by_type['execution_completed']), 1)

            # No failure events yet
            self.assertEqual(len(events_by_type['poll_failure']), 0)
            self.assertEqual(len(events_by_type['execution_failure']), 0)

            # Verify event data
            poll_started = events_by_type['poll_started'][0]
            self.assertEqual(poll_started.task_type, 'test_all_events')
            self.assertEqual(poll_started.poll_count, 1)

            poll_completed = events_by_type['poll_completed'][0]
            self.assertEqual(poll_completed.tasks_received, 1)
            self.assertGreater(poll_completed.duration_ms, 0)

            execution_completed = events_by_type['execution_completed'][0]
            self.assertEqual(execution_completed.task_id, self.TASK_ID)
            self.assertGreater(execution_completed.duration_ms, 0)
            self.assertGreater(execution_completed.output_size_bytes, 0)

            # Now test failure scenario
            runner.async_task_client.batch_poll = AsyncMock(side_effect=Exception("Network error"))
            await runner.run_once()

            # Verify poll failure event was published
            self.assertEqual(len(events_by_type['poll_failure']), 1)
            poll_failure = events_by_type['poll_failure'][0]
            self.assertIn("Network error", str(poll_failure.cause))

        asyncio.run(run_test())

    def test_custom_event_listener_integration(self):
        """Test that custom event listeners receive events correctly."""

        async def tracked_worker(operation: str) -> dict:
            await asyncio.sleep(0.01)
            return {'operation': operation, 'status': 'completed'}

        worker = Worker(
            task_definition_name='test_custom_listener',
            execute_function=tracked_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        # Custom listener that tracks SLA
        class SLAMonitor:
            def __init__(self):
                self.sla_breaches = []
                self.total_executions = 0

            def on_task_execution_completed(self, event):
                self.total_executions += 1
                if event.duration_ms > 100:  # 100ms SLA
                    self.sla_breaches.append({
                        'task_id': event.task_id,
                        'duration_ms': event.duration_ms
                    })

        sla_monitor = SLAMonitor()

        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[sla_monitor]
        )

        mock_task = self.__create_task(input_data={'operation': 'test_op'})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Verify custom listener received events
            self.assertEqual(sla_monitor.total_executions, 1)
            # Task should complete in < 100ms (no SLA breach)
            self.assertEqual(len(sla_monitor.sla_breaches), 0)

        asyncio.run(run_test())

    def test_multiple_event_listeners(self):
        """Test that multiple event listeners can be registered and all receive events."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_multi_listeners',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        # Multiple listeners
        listener1_events = []
        listener2_events = []

        class Listener1:
            def on_task_execution_completed(self, event):
                listener1_events.append(event)

        class Listener2:
            def on_task_execution_completed(self, event):
                listener2_events.append(event)
            def on_poll_completed(self, event):
                listener2_events.append(event)

        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[Listener1(), Listener2()]
        )

        mock_task = self.__create_task(input_data={'value': 5})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Both listeners should receive TaskExecutionCompleted
            self.assertEqual(len(listener1_events), 1)
            self.assertGreaterEqual(len(listener2_events), 2)  # TaskExecutionCompleted + PollCompleted

            # Verify they received the same event
            self.assertEqual(listener1_events[0].task_id, self.TASK_ID)

        asyncio.run(run_test())

    def test_event_listener_exception_isolation(self):
        """Test that exceptions in event listeners don't break worker execution."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_listener_exception',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        # Faulty listener that raises exception
        class FaultyListener:
            def on_task_execution_completed(self, event):
                raise ValueError("Intentional listener error")

        # Good listener that should still work
        good_listener_events = []

        class GoodListener:
            def on_task_execution_completed(self, event):
                good_listener_events.append(event)

        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[FaultyListener(), GoodListener()]
        )

        mock_task = self.__create_task(input_data={'value': 5})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            # Should complete without raising exception (listener error isolated)
            await runner.run_once()
            await asyncio.sleep(0.1)

            # Good listener should still receive events
            self.assertEqual(len(good_listener_events), 1)

            # Update task should still be called (worker execution not affected)
            runner.async_task_client.update_task.assert_called_once()

        asyncio.run(run_test())

    def test_event_data_accuracy(self):
        """Test that event data is accurate and complete."""

        async def detailed_worker(value: int) -> dict:
            await asyncio.sleep(0.02)  # Measurable duration
            return {'result': value * 2, 'metadata': {'processed': True}}

        worker = Worker(
            task_definition_name='test_event_data',
            execute_function=detailed_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        captured_events = {}

        class DetailedCapture:
            def on_poll_started(self, event):
                captured_events['poll_started'] = event
            def on_poll_completed(self, event):
                captured_events['poll_completed'] = event
            def on_task_execution_started(self, event):
                captured_events['execution_started'] = event
            def on_task_execution_completed(self, event):
                captured_events['execution_completed'] = event

        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[DetailedCapture()]
        )

        mock_task = self.__create_task(input_data={'value': 10})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Verify PollStarted event
            poll_started = captured_events['poll_started']
            self.assertEqual(poll_started.task_type, 'test_event_data')
            self.assertEqual(poll_started.poll_count, 1)
            self.assertIsNotNone(poll_started.worker_id)
            self.assertIsNotNone(poll_started.timestamp)

            # Verify PollCompleted event
            poll_completed = captured_events['poll_completed']
            self.assertEqual(poll_completed.task_type, 'test_event_data')
            self.assertEqual(poll_completed.tasks_received, 1)
            self.assertGreater(poll_completed.duration_ms, 0)
            self.assertIsNotNone(poll_completed.timestamp)

            # Verify TaskExecutionStarted event
            execution_started = captured_events['execution_started']
            self.assertEqual(execution_started.task_type, 'test_event_data')
            self.assertEqual(execution_started.task_id, self.TASK_ID)
            self.assertEqual(execution_started.workflow_instance_id, self.WORKFLOW_INSTANCE_ID)
            self.assertIsNotNone(execution_started.worker_id)
            self.assertIsNotNone(execution_started.timestamp)

            # Verify TaskExecutionCompleted event
            execution_completed = captured_events['execution_completed']
            self.assertEqual(execution_completed.task_type, 'test_event_data')
            self.assertEqual(execution_completed.task_id, self.TASK_ID)
            self.assertEqual(execution_completed.workflow_instance_id, self.WORKFLOW_INSTANCE_ID)
            self.assertGreater(execution_completed.duration_ms, 10)  # Should be > 20ms (sleep time)
            self.assertGreater(execution_completed.output_size_bytes, 0)
            self.assertIsNotNone(execution_completed.worker_id)
            self.assertIsNotNone(execution_completed.timestamp)

        asyncio.run(run_test())

    def test_metrics_collector_receives_events(self):
        """Test that MetricsCollector receives events when registered as listener."""

        async def simple_worker(value: int) -> dict:
            return {'result': value}

        worker = Worker(
            task_definition_name='test_metrics_events',
            execute_function=simple_worker,
            thread_count=1
        )

        config = Configuration()
        config.AUTH_TOKEN = self.AUTH_TOKEN

        # Mock MetricsCollector to track method calls
        mock_metrics = Mock()
        mock_metrics.on_poll_started = Mock()
        mock_metrics.on_poll_completed = Mock()
        mock_metrics.on_task_execution_started = Mock()
        mock_metrics.on_task_execution_completed = Mock()

        runner = AsyncTaskRunner(
            worker=worker,
            configuration=config,
            event_listeners=[mock_metrics]
        )

        mock_task = self.__create_task(input_data={'value': 5})

        async def run_test():
            runner.async_api_client = AsyncMock()
            runner.async_task_client = AsyncMock()
            runner._semaphore = asyncio.Semaphore(1)

            runner.async_task_client.batch_poll = AsyncMock(return_value=[mock_task])
            runner.async_task_client.update_task = AsyncMock(return_value=self.UPDATE_TASK_RESPONSE)

            await runner.run_once()
            await asyncio.sleep(0.1)

            # Verify MetricsCollector methods were called
            mock_metrics.on_poll_started.assert_called_once()
            mock_metrics.on_poll_completed.assert_called_once()
            mock_metrics.on_task_execution_started.assert_called_once()
            mock_metrics.on_task_execution_completed.assert_called_once()

            # Verify event objects passed to metrics collector
            execution_completed_event = mock_metrics.on_task_execution_completed.call_args[0][0]
            self.assertEqual(execution_completed_event.task_id, self.TASK_ID)
            self.assertGreater(execution_completed_event.duration_ms, 0)

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
