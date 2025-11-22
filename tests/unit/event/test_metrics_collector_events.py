"""
Unit tests for MetricsCollector event listener integration
"""

import unittest
from unittest.mock import Mock, patch
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.event.task_runner_events import (
    PollStarted,
    PollCompleted,
    PollFailure,
    TaskExecutionStarted,
    TaskExecutionCompleted,
    TaskExecutionFailure
)


class TestMetricsCollectorEvents(unittest.TestCase):
    """Test MetricsCollector event listener methods"""

    def setUp(self):
        """Create a MetricsCollector for each test"""
        # MetricsCollector without settings (no actual metrics collection)
        self.collector = MetricsCollector(settings=None)

    def test_on_poll_started(self):
        """Test on_poll_started event handler"""
        with patch.object(self.collector, 'increment_task_poll') as mock_increment:
            event = PollStarted(
                task_type="test_task",
                worker_id="worker_1",
                poll_count=5
            )
            self.collector.on_poll_started(event)

            mock_increment.assert_called_once_with("test_task")

    def test_on_poll_completed(self):
        """Test on_poll_completed event handler"""
        with patch.object(self.collector, 'record_task_poll_time') as mock_record:
            event = PollCompleted(
                task_type="test_task",
                duration_ms=250.0,
                tasks_received=3
            )
            self.collector.on_poll_completed(event)

            # Duration should be converted from ms to seconds, status added
            mock_record.assert_called_once_with("test_task", 0.25, status="SUCCESS")

    def test_on_poll_failure(self):
        """Test on_poll_failure event handler"""
        with patch.object(self.collector, 'increment_task_poll_error') as mock_increment:
            error = Exception("Test error")
            event = PollFailure(
                task_type="test_task",
                duration_ms=100.0,
                cause=error
            )
            self.collector.on_poll_failure(event)

            mock_increment.assert_called_once_with("test_task", error)

    def test_on_task_execution_started(self):
        """Test on_task_execution_started event handler (no-op)"""
        event = TaskExecutionStarted(
            task_type="test_task",
            task_id="task_123",
            worker_id="worker_1",
            workflow_instance_id="wf_123"
        )
        # Should not raise any exception
        self.collector.on_task_execution_started(event)

    def test_on_task_execution_completed(self):
        """Test on_task_execution_completed event handler"""
        with patch.object(self.collector, 'record_task_execute_time') as mock_time, \
             patch.object(self.collector, 'record_task_result_payload_size') as mock_size:

            event = TaskExecutionCompleted(
                task_type="test_task",
                task_id="task_123",
                worker_id="worker_1",
                workflow_instance_id="wf_123",
                duration_ms=500.0,
                output_size_bytes=1024
            )
            self.collector.on_task_execution_completed(event)

            # Duration should be converted from ms to seconds, status added
            mock_time.assert_called_once_with("test_task", 0.5, status="SUCCESS")
            mock_size.assert_called_once_with("test_task", 1024)

    def test_on_task_execution_completed_no_output_size(self):
        """Test on_task_execution_completed with no output size"""
        with patch.object(self.collector, 'record_task_execute_time') as mock_time, \
             patch.object(self.collector, 'record_task_result_payload_size') as mock_size:

            event = TaskExecutionCompleted(
                task_type="test_task",
                task_id="task_123",
                worker_id="worker_1",
                workflow_instance_id="wf_123",
                duration_ms=500.0,
                output_size_bytes=None
            )
            self.collector.on_task_execution_completed(event)

            mock_time.assert_called_once_with("test_task", 0.5, status="SUCCESS")
            # Should not record size if None
            mock_size.assert_not_called()

    def test_on_task_execution_failure(self):
        """Test on_task_execution_failure event handler"""
        with patch.object(self.collector, 'increment_task_execution_error') as mock_increment:
            error = Exception("Task failed")
            event = TaskExecutionFailure(
                task_type="test_task",
                task_id="task_123",
                worker_id="worker_1",
                workflow_instance_id="wf_123",
                cause=error,
                duration_ms=200.0
            )
            self.collector.on_task_execution_failure(event)

            mock_increment.assert_called_once_with("test_task", error)


if __name__ == '__main__':
    unittest.main()
