"""
Comprehensive tests for MetricsCollector.

Tests cover:
1. Event listener methods (on_poll_completed, on_task_execution_completed, etc.)
2. Increment methods (increment_task_poll, increment_task_paused, etc.)
3. Record methods (record_api_request_time, record_task_poll_time, etc.)
4. Quantile/percentile calculations
5. Integration with Prometheus registry
6. Edge cases and boundary conditions
"""

import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from prometheus_client import write_to_textfile

from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.client.event.task_runner_events import (
    PollStarted,
    PollCompleted,
    PollFailure,
    TaskExecutionStarted,
    TaskExecutionCompleted,
    TaskExecutionFailure
)
from conductor.client.event.workflow_events import (
    WorkflowStarted,
    WorkflowInputPayloadSize,
    WorkflowPayloadUsed
)
from conductor.client.event.task_events import (
    TaskResultPayloadSize,
    TaskPayloadUsed
)


class TestMetricsCollector(unittest.TestCase):
    """Test MetricsCollector functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for metrics
        self.metrics_dir = tempfile.mkdtemp()
        self.metrics_settings = MetricsSettings(
            directory=self.metrics_dir,
            file_name='test_metrics.prom',
            update_interval=0.1
        )

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.metrics_dir):
            shutil.rmtree(self.metrics_dir)

    # =========================================================================
    # Event Listener Tests
    # =========================================================================

    def test_on_poll_started(self):
        """Test on_poll_started event handler"""
        collector = MetricsCollector(self.metrics_settings)

        event = PollStarted(
            task_type='test_task',
            worker_id='worker1',
            poll_count=5
        )

        # Should not raise exception
        collector.on_poll_started(event)

        # Verify task_poll_total incremented
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_poll_total{taskType="test_task"}', metrics_content)

    def test_on_poll_completed_success(self):
        """Test on_poll_completed event handler with successful poll"""
        collector = MetricsCollector(self.metrics_settings)

        event = PollCompleted(
            task_type='test_task',
            duration_ms=125.5,
            tasks_received=2
        )

        collector.on_poll_completed(event)

        # Verify timing recorded
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        # Should have quantile metrics
        self.assertIn('task_poll_time_seconds{taskType="test_task",status="SUCCESS"', metrics_content)
        self.assertIn('task_poll_time_seconds_count{taskType="test_task",status="SUCCESS"}', metrics_content)

    def test_on_poll_failure(self):
        """Test on_poll_failure event handler"""
        collector = MetricsCollector(self.metrics_settings)

        exception = RuntimeError("Poll failed")
        event = PollFailure(
            task_type='test_task',
            duration_ms=50.0,
            cause=exception
        )

        collector.on_poll_failure(event)

        # Verify failure timing recorded
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_poll_time_seconds{taskType="test_task",status="FAILURE"', metrics_content)

    def test_on_task_execution_started(self):
        """Test on_task_execution_started event handler"""
        collector = MetricsCollector(self.metrics_settings)

        event = TaskExecutionStarted(
            task_type='test_task',
            task_id='task123',
            worker_id='worker1',
            workflow_instance_id='wf456'
        )

        # Should not raise exception
        collector.on_task_execution_started(event)

    def test_on_task_execution_completed(self):
        """Test on_task_execution_completed event handler"""
        collector = MetricsCollector(self.metrics_settings)

        event = TaskExecutionCompleted(
            task_type='test_task',
            task_id='task123',
            worker_id='worker1',
            workflow_instance_id='wf456',
            duration_ms=350.25,
            output_size_bytes=1024
        )

        collector.on_task_execution_completed(event)

        # Verify execution timing recorded
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_execute_time_seconds{taskType="test_task",status="SUCCESS"', metrics_content)

    def test_on_task_execution_failure(self):
        """Test on_task_execution_failure event handler"""
        collector = MetricsCollector(self.metrics_settings)

        exception = ValueError("Task failed")
        event = TaskExecutionFailure(
            task_type='test_task',
            task_id='task123',
            worker_id='worker1',
            workflow_instance_id='wf456',
            cause=exception,
            duration_ms=100.0
        )

        collector.on_task_execution_failure(event)

        # Verify failure recorded
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_execute_error_total{taskType="test_task"', metrics_content)
        self.assertIn('task_execute_time_seconds{taskType="test_task",status="FAILURE"', metrics_content)

    def test_on_workflow_started_success(self):
        """Test on_workflow_started event handler for successful start"""
        collector = MetricsCollector(self.metrics_settings)

        event = WorkflowStarted(
            name='test_workflow',
            version='1',
            workflow_id='wf123',
            success=True
        )

        # Should not raise exception
        collector.on_workflow_started(event)

    def test_on_workflow_started_failure(self):
        """Test on_workflow_started event handler for failed start"""
        collector = MetricsCollector(self.metrics_settings)

        exception = RuntimeError("Workflow start failed")
        event = WorkflowStarted(
            name='test_workflow',
            version='1',
            workflow_id=None,
            success=False,
            cause=exception
        )

        collector.on_workflow_started(event)

        # Verify error counter incremented
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('workflow_start_error_total{workflowType="test_workflow"', metrics_content)

    def test_on_workflow_input_payload_size(self):
        """Test on_workflow_input_payload_size event handler"""
        collector = MetricsCollector(self.metrics_settings)

        event = WorkflowInputPayloadSize(
            name='test_workflow',
            version='1',
            size_bytes=2048
        )

        collector.on_workflow_input_payload_size(event)

        # Verify size recorded
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('workflow_input_size{workflowType="test_workflow",version="1"}', metrics_content)

    def test_on_workflow_payload_used(self):
        """Test on_workflow_payload_used event handler"""
        collector = MetricsCollector(self.metrics_settings)

        event = WorkflowPayloadUsed(
            name='test_workflow',
            payload_type='input'
        )

        collector.on_workflow_payload_used(event)

        # Verify external payload counter incremented
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('external_payload_used_total{workflowType="test_workflow",payloadType="input"}', metrics_content)

    def test_on_task_result_payload_size(self):
        """Test on_task_result_payload_size event handler"""
        collector = MetricsCollector(self.metrics_settings)

        event = TaskResultPayloadSize(
            task_type='test_task',
            size_bytes=4096
        )

        collector.on_task_result_payload_size(event)

        # Verify size recorded
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_result_size{taskType="test_task"}', metrics_content)

    def test_on_task_payload_used(self):
        """Test on_task_payload_used event handler"""
        collector = MetricsCollector(self.metrics_settings)

        event = TaskPayloadUsed(
            task_type='test_task',
            payload_type='output'
        )

        collector.on_task_payload_used(event)

        # Verify external payload counter incremented
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('external_payload_used_total{taskType="test_task",payloadType="output"}', metrics_content)

    # =========================================================================
    # Increment Methods Tests
    # =========================================================================

    def test_increment_task_poll(self):
        """Test increment_task_poll method"""
        collector = MetricsCollector(self.metrics_settings)

        collector.increment_task_poll('test_task')
        collector.increment_task_poll('test_task')
        collector.increment_task_poll('test_task')

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        # Should have task_poll_total metric
        self.assertIn('task_poll_total{taskType="test_task"} 3.0', metrics_content)

    def test_increment_task_poll_error_is_noop(self):
        """Test increment_task_poll_error is a no-op"""
        collector = MetricsCollector(self.metrics_settings)

        # Should not raise exception
        exception = RuntimeError("Poll error")
        collector.increment_task_poll_error('test_task', exception)

        # Should not create TASK_POLL_ERROR metric
        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertNotIn('task_poll_error_total', metrics_content)

    def test_increment_task_paused(self):
        """Test increment_task_paused method"""
        collector = MetricsCollector(self.metrics_settings)

        collector.increment_task_paused('test_task')
        collector.increment_task_paused('test_task')

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_paused_total{taskType="test_task"} 2.0', metrics_content)

    def test_increment_task_execution_error(self):
        """Test increment_task_execution_error method"""
        collector = MetricsCollector(self.metrics_settings)

        exception = ValueError("Execution failed")
        collector.increment_task_execution_error('test_task', exception)

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_execute_error_total{taskType="test_task"', metrics_content)

    def test_increment_task_update_error(self):
        """Test increment_task_update_error method"""
        collector = MetricsCollector(self.metrics_settings)

        exception = RuntimeError("Update failed")
        collector.increment_task_update_error('test_task', exception)

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_update_error_total{taskType="test_task"', metrics_content)

    def test_increment_external_payload_used(self):
        """Test increment_external_payload_used method"""
        collector = MetricsCollector(self.metrics_settings)

        collector.increment_external_payload_used('test_task', 'input')
        collector.increment_external_payload_used('test_task', 'output')

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('external_payload_used_total{taskType="test_task",payloadType="input"} 1.0', metrics_content)
        self.assertIn('external_payload_used_total{taskType="test_task",payloadType="output"} 1.0', metrics_content)

    # =========================================================================
    # Record Methods Tests
    # =========================================================================

    def test_record_api_request_time(self):
        """Test record_api_request_time method"""
        collector = MetricsCollector(self.metrics_settings)

        collector.record_api_request_time(
            method='GET',
            uri='/tasks/poll/batch/test_task',
            status='200',
            time_spent=0.125
        )

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        # Should have quantile metrics
        self.assertIn('api_request_time_seconds{method="GET",uri="/tasks/poll/batch/test_task",status="200"', metrics_content)
        self.assertIn('api_request_time_seconds_count', metrics_content)
        self.assertIn('api_request_time_seconds_sum', metrics_content)

    def test_record_api_request_time_error_status(self):
        """Test record_api_request_time with error status"""
        collector = MetricsCollector(self.metrics_settings)

        collector.record_api_request_time(
            method='POST',
            uri='/tasks/update',
            status='500',
            time_spent=0.250
        )

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('api_request_time_seconds{method="POST",uri="/tasks/update",status="500"', metrics_content)

    def test_record_task_result_payload_size(self):
        """Test record_task_result_payload_size method"""
        collector = MetricsCollector(self.metrics_settings)

        collector.record_task_result_payload_size('test_task', 8192)

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_result_size{taskType="test_task"} 8192.0', metrics_content)

    def test_record_workflow_input_payload_size(self):
        """Test record_workflow_input_payload_size method"""
        collector = MetricsCollector(self.metrics_settings)

        collector.record_workflow_input_payload_size('test_workflow', '1', 16384)

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('workflow_input_size{workflowType="test_workflow",version="1"} 16384.0', metrics_content)

    # =========================================================================
    # Quantile Calculation Tests
    # =========================================================================

    def test_quantile_calculation_with_multiple_samples(self):
        """Test quantile calculation with multiple timing samples"""
        collector = MetricsCollector(self.metrics_settings)

        # Record 100 samples with known distribution
        for i in range(100):
            collector.record_api_request_time(
                method='GET',
                uri='/test',
                status='200',
                time_spent=i / 1000.0  # 0.0, 0.001, 0.002, ..., 0.099
            )

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        # Should have quantile labels (0.5, 0.75, 0.9, 0.95, 0.99)
        self.assertIn('quantile="0.5"', metrics_content)
        self.assertIn('quantile="0.75"', metrics_content)
        self.assertIn('quantile="0.9"', metrics_content)
        self.assertIn('quantile="0.95"', metrics_content)
        self.assertIn('quantile="0.99"', metrics_content)

        # Should have count and sum
        self.assertIn('api_request_time_seconds_count{method="GET",uri="/test",status="200"} 100.0', metrics_content)

    def test_quantile_sliding_window(self):
        """Test quantile calculations use sliding window (last 1000 observations)"""
        collector = MetricsCollector(self.metrics_settings)

        # Record 1500 samples (exceeds window size of 1000)
        for i in range(1500):
            collector.record_api_request_time(
                method='GET',
                uri='/test',
                status='200',
                time_spent=0.001
            )

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        # Count should reflect all samples
        self.assertIn('api_request_time_seconds_count{method="GET",uri="/test",status="200"} 1500.0', metrics_content)

    def test_percentile_calculation(self):
        """Test _calculate_percentile helper function"""
        collector = MetricsCollector(self.metrics_settings)

        # Simple sorted array
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        p50 = collector._calculate_percentile(values, 0.5)
        p90 = collector._calculate_percentile(values, 0.9)
        p99 = collector._calculate_percentile(values, 0.99)

        # p50 should be around 5.5
        self.assertAlmostEqual(p50, 5.5, delta=1.0)

        # p90 should be around 9
        self.assertAlmostEqual(p90, 9.0, delta=1.0)

        # p99 should be around 10
        self.assertAlmostEqual(p99, 10.0, delta=0.5)

    def test_percentile_empty_list(self):
        """Test percentile calculation with empty list"""
        collector = MetricsCollector(self.metrics_settings)

        result = collector._calculate_percentile([], 0.5)
        self.assertEqual(result, 0.0)

    def test_percentile_single_value(self):
        """Test percentile calculation with single value"""
        collector = MetricsCollector(self.metrics_settings)

        result = collector._calculate_percentile([42.0], 0.95)
        self.assertEqual(result, 42.0)

    # =========================================================================
    # Edge Cases and Boundary Conditions
    # =========================================================================

    def test_multiple_task_types(self):
        """Test metrics for multiple different task types"""
        collector = MetricsCollector(self.metrics_settings)

        collector.increment_task_poll('task1')
        collector.increment_task_poll('task2')
        collector.increment_task_poll('task3')

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_poll_total{taskType="task1"}', metrics_content)
        self.assertIn('task_poll_total{taskType="task2"}', metrics_content)
        self.assertIn('task_poll_total{taskType="task3"}', metrics_content)

    def test_concurrent_metric_updates(self):
        """Test metrics can handle concurrent updates"""
        collector = MetricsCollector(self.metrics_settings)

        # Simulate concurrent updates
        for _ in range(10):
            collector.increment_task_poll('test_task')
            collector.record_api_request_time('GET', '/test', '200', 0.001)

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('task_poll_total{taskType="test_task"} 10.0', metrics_content)

    def test_zero_duration_timing(self):
        """Test recording zero duration timing"""
        collector = MetricsCollector(self.metrics_settings)

        collector.record_api_request_time('GET', '/test', '200', 0.0)

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        # Should still record the timing
        self.assertIn('api_request_time_seconds', metrics_content)

    def test_very_large_payload_size(self):
        """Test recording very large payload sizes"""
        collector = MetricsCollector(self.metrics_settings)

        large_size = 100 * 1024 * 1024  # 100 MB
        collector.record_task_result_payload_size('test_task', large_size)

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn(f'task_result_size{{taskType="test_task"}} {float(large_size)}', metrics_content)

    def test_special_characters_in_labels(self):
        """Test handling special characters in label values"""
        collector = MetricsCollector(self.metrics_settings)

        # Task name with special characters
        collector.increment_task_poll('task-with-dashes')
        collector.increment_task_poll('task_with_underscores')

        self._write_metrics(collector)
        metrics_content = self._read_metrics_file()

        self.assertIn('taskType="task-with-dashes"', metrics_content)
        self.assertIn('taskType="task_with_underscores"', metrics_content)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _write_metrics(self, collector):
        """Write metrics to file using prometheus write_to_textfile"""
        metrics_file = os.path.join(self.metrics_dir, 'test_metrics.prom')
        write_to_textfile(metrics_file, collector.registry)

    def _read_metrics_file(self):
        """Read metrics file content"""
        metrics_file = os.path.join(self.metrics_dir, 'test_metrics.prom')
        if not os.path.exists(metrics_file):
            return ''
        with open(metrics_file, 'r') as f:
            return f.read()


if __name__ == '__main__':
    unittest.main()
