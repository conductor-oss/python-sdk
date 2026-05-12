"""
Tests for CanonicalMetricsCollector.

Verifies that canonical metric names, types, labels, and bucket sets are
correct per the sdk-metrics-harmonization spec.
"""

import os
import shutil
import tempfile
import unittest

from prometheus_client import write_to_textfile

from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector
from conductor.client.telemetry.metrics_collector_base import _exception_label
from conductor.client.event.task_runner_events import (
    PollStarted,
    PollCompleted,
    PollFailure,
    TaskExecutionStarted,
    TaskExecutionCompleted,
    TaskExecutionFailure,
)


class TestCanonicalMetricsCollector(unittest.TestCase):

    def setUp(self):
        self.metrics_dir = tempfile.mkdtemp()
        self.settings = MetricsSettings(directory=self.metrics_dir)
        self.collector = CanonicalMetricsCollector(self.settings)

    def tearDown(self):
        if os.path.exists(self.metrics_dir):
            shutil.rmtree(self.metrics_dir)

    def _get_metrics_text(self):
        path = os.path.join(self.metrics_dir, "test_out.prom")
        write_to_textfile(path, self.collector.registry)
        with open(path) as f:
            return f.read()

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------

    def test_task_poll_counter(self):
        self.collector.increment_task_poll("my_task")
        text = self._get_metrics_text()
        self.assertIn('task_poll_total{taskType="my_task"}', text)

    def test_task_poll_error_counter(self):
        self.collector.increment_task_poll_error("my_task", RuntimeError("oops"))
        text = self._get_metrics_text()
        self.assertIn("task_poll_error_total", text)
        self.assertIn('exception="RuntimeError"', text)

    def test_task_execution_started_counter(self):
        self.collector.increment_task_execution_started("my_task")
        text = self._get_metrics_text()
        self.assertIn('task_execution_started_total{taskType="my_task"}', text)

    def test_uncaught_exception_with_label(self):
        self.collector.increment_uncaught_exception(ValueError("bad"))
        text = self._get_metrics_text()
        self.assertIn("thread_uncaught_exceptions_total", text)
        self.assertIn('exception="ValueError"', text)

    def test_external_payload_uses_camelcase_label(self):
        self.collector.increment_external_payload_used("ent", "READ", "TASK_INPUT")
        text = self._get_metrics_text()
        self.assertIn("external_payload_used_total", text)
        self.assertIn('payloadType="TASK_INPUT"', text)

    def test_exception_label_uses_class_name(self):
        self.collector.increment_task_execution_error("t", ValueError("x"))
        text = self._get_metrics_text()
        self.assertIn('exception="ValueError"', text)

    def test_workflow_start_error(self):
        self.collector.increment_workflow_start_error("wf", Exception("fail"))
        text = self._get_metrics_text()
        self.assertIn("workflow_start_error_total", text)
        self.assertIn('exception="Exception"', text)

    # ------------------------------------------------------------------
    # Time Histograms
    # ------------------------------------------------------------------

    def test_task_poll_time_is_histogram(self):
        self.collector.record_task_poll_time("my_task", 0.05, status="SUCCESS")
        text = self._get_metrics_text()
        self.assertIn("task_poll_time_seconds_bucket", text)
        self.assertIn("task_poll_time_seconds_count", text)
        self.assertIn("task_poll_time_seconds_sum", text)
        self.assertIn('le="0.1"', text)

    def test_task_execute_time_is_histogram(self):
        self.collector.record_task_execute_time("my_task", 0.5, status="SUCCESS")
        text = self._get_metrics_text()
        self.assertIn("task_execute_time_seconds_bucket", text)

    def test_task_update_time_is_histogram(self):
        self.collector.record_task_update_time("my_task", 0.2, status="FAILURE")
        text = self._get_metrics_text()
        self.assertIn("task_update_time_seconds_bucket", text)
        self.assertIn('status="FAILURE"', text)

    def test_api_request_time_canonical_name(self):
        self.collector.record_api_request_time("GET", "/api/tasks", "200", 0.1)
        text = self._get_metrics_text()
        self.assertIn("http_api_client_request_seconds_bucket", text)
        self.assertIn("http_api_client_request_seconds_count", text)

    def test_time_histogram_bucket_set(self):
        """Canonical time histograms use the spec bucket set."""
        self.collector.record_task_poll_time("my_task", 0.001)
        text = self._get_metrics_text()
        for boundary in ("0.001", "0.005", "0.01", "0.025", "0.05", "0.1",
                         "0.25", "0.5", "1.0", "2.5", "5.0", "10.0"):
            self.assertIn(f'le="{boundary}"', text)

    # ------------------------------------------------------------------
    # Size Histograms
    # ------------------------------------------------------------------

    def test_task_result_size_bytes_histogram(self):
        self.collector.record_task_result_payload_size("my_task", 5000)
        text = self._get_metrics_text()
        self.assertIn("task_result_size_bytes_bucket", text)
        self.assertIn("task_result_size_bytes_count", text)

    def test_workflow_input_size_bytes_histogram(self):
        self.collector.record_workflow_input_payload_size("wf", "1", 50000)
        text = self._get_metrics_text()
        self.assertIn("workflow_input_size_bytes_bucket", text)

    def test_size_histogram_bucket_set(self):
        """Canonical size histograms use the spec bucket set."""
        self.collector.record_task_result_payload_size("t", 500)
        text = self._get_metrics_text()
        # prometheus_client uses scientific notation for large values
        for boundary in ("100.0", "1000.0", "10000.0", "100000.0",
                         "1e+06", "1e+07"):
            self.assertIn(f'le="{boundary}"', text)

    # ------------------------------------------------------------------
    # Event handler integration
    # ------------------------------------------------------------------

    def test_event_poll_started_increments_counter(self):
        event = PollStarted(task_type="t", worker_id="w", poll_count=1)
        self.collector.on_poll_started(event)
        text = self._get_metrics_text()
        self.assertIn('task_poll_total{taskType="t"}', text)

    def test_event_poll_completed_records_histogram(self):
        event = PollCompleted(task_type="t", duration_ms=100.0, tasks_received=1)
        self.collector.on_poll_completed(event)
        text = self._get_metrics_text()
        self.assertIn("task_poll_time_seconds_bucket", text)

    def test_event_poll_failure_records_error_and_histogram(self):
        event = PollFailure(task_type="t", duration_ms=50.0, cause=RuntimeError("x"))
        self.collector.on_poll_failure(event)
        text = self._get_metrics_text()
        self.assertIn("task_poll_error_total", text)
        self.assertIn("task_poll_time_seconds_bucket", text)

    def test_event_execution_started(self):
        event = TaskExecutionStarted(task_type="t", task_id="id", worker_id="w", workflow_instance_id="wf")
        self.collector.on_task_execution_started(event)
        text = self._get_metrics_text()
        self.assertIn("task_execution_started_total", text)

    def test_event_execution_completed_records_histogram_and_size(self):
        event = TaskExecutionCompleted(
            task_type="t", task_id="id", worker_id="w",
            workflow_instance_id="wf", duration_ms=200.0, output_size_bytes=1024,
        )
        self.collector.on_task_execution_completed(event)
        text = self._get_metrics_text()
        self.assertIn("task_execute_time_seconds_bucket", text)
        self.assertIn("task_result_size_bytes_bucket", text)

    def test_event_execution_failure_records_counter_and_histogram(self):
        event = TaskExecutionFailure(
            task_type="t", task_id="id", worker_id="w",
            workflow_instance_id="wf", cause=ValueError("bad"), duration_ms=100.0,
        )
        self.collector.on_task_execution_failure(event)
        text = self._get_metrics_text()
        self.assertIn("task_execute_error_total", text)
        self.assertIn("task_execute_time_seconds_bucket", text)

    # ------------------------------------------------------------------
    # active_workers gauge
    # ------------------------------------------------------------------

    def test_active_workers_gauge_increments_on_start(self):
        event = TaskExecutionStarted(task_type="t", task_id="id", worker_id="w", workflow_instance_id="wf")
        self.collector.on_task_execution_started(event)
        text = self._get_metrics_text()
        self.assertIn('active_workers{taskType="t"}', text)
        self.assertIn("1.0", text)

    def test_active_workers_gauge_decrements_on_complete(self):
        start = TaskExecutionStarted(task_type="t", task_id="id", worker_id="w", workflow_instance_id="wf")
        self.collector.on_task_execution_started(start)
        self.collector.on_task_execution_started(start)

        complete = TaskExecutionCompleted(
            task_type="t", task_id="id", worker_id="w",
            workflow_instance_id="wf", duration_ms=100.0, output_size_bytes=None,
        )
        self.collector.on_task_execution_completed(complete)
        text = self._get_metrics_text()
        self.assertIn('active_workers{taskType="t"} 1.0', text)

    def test_active_workers_gauge_decrements_on_failure(self):
        start = TaskExecutionStarted(task_type="t", task_id="id", worker_id="w", workflow_instance_id="wf")
        self.collector.on_task_execution_started(start)

        failure = TaskExecutionFailure(
            task_type="t", task_id="id", worker_id="w",
            workflow_instance_id="wf", cause=ValueError("x"), duration_ms=50.0,
        )
        self.collector.on_task_execution_failure(failure)
        text = self._get_metrics_text()
        self.assertIn('active_workers{taskType="t"} 0.0', text)

    def test_active_workers_gauge_floors_at_zero(self):
        complete = TaskExecutionCompleted(
            task_type="t", task_id="id", worker_id="w",
            workflow_instance_id="wf", duration_ms=100.0, output_size_bytes=None,
        )
        self.collector.on_task_execution_completed(complete)
        text = self._get_metrics_text()
        self.assertIn('active_workers{taskType="t"} 0.0', text)

    def test_active_workers_tracks_multiple_task_types(self):
        self.collector.on_task_execution_started(
            TaskExecutionStarted(task_type="a", task_id="1", worker_id="w", workflow_instance_id="wf"))
        self.collector.on_task_execution_started(
            TaskExecutionStarted(task_type="a", task_id="2", worker_id="w", workflow_instance_id="wf"))
        self.collector.on_task_execution_started(
            TaskExecutionStarted(task_type="b", task_id="3", worker_id="w", workflow_instance_id="wf"))

        text = self._get_metrics_text()
        self.assertIn('active_workers{taskType="a"} 2.0', text)
        self.assertIn('active_workers{taskType="b"} 1.0', text)


class TestExceptionLabel(unittest.TestCase):
    """Test the _exception_label helper."""

    def test_none(self):
        self.assertEqual(_exception_label(None), "None")

    def test_exception_instance(self):
        self.assertEqual(_exception_label(ValueError("x")), "ValueError")

    def test_exception_class(self):
        self.assertEqual(_exception_label(RuntimeError), "RuntimeError")

    def test_string_passthrough(self):
        self.assertEqual(_exception_label("SomeError"), "SomeError")


if __name__ == "__main__":
    unittest.main()
