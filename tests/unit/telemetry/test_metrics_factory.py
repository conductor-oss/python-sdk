"""
Tests for the metrics factory and gated metrics selection.
"""

import os
import shutil
import tempfile
import unittest

from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_factory import create_metrics_collector
from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector
from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector


class TestMetricsFactory(unittest.TestCase):

    def setUp(self):
        self.metrics_dir = tempfile.mkdtemp()
        self.settings = MetricsSettings(directory=self.metrics_dir)
        self._saved_env = {}
        for key in ("WORKER_CANONICAL_METRICS", "WORKER_LEGACY_METRICS"):
            self._saved_env[key] = os.environ.pop(key, None)

    def tearDown(self):
        for key, val in self._saved_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        if os.path.exists(self.metrics_dir):
            shutil.rmtree(self.metrics_dir)

    def test_default_returns_legacy(self):
        """With no env vars set, factory returns LegacyMetricsCollector."""
        collector = create_metrics_collector(self.settings)
        self.assertIsInstance(collector, LegacyMetricsCollector)

    def test_canonical_true_returns_canonical(self):
        """WORKER_CANONICAL_METRICS=true selects CanonicalMetricsCollector."""
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        collector = create_metrics_collector(self.settings)
        self.assertIsInstance(collector, CanonicalMetricsCollector)

    def test_canonical_1_returns_canonical(self):
        """WORKER_CANONICAL_METRICS=1 selects CanonicalMetricsCollector."""
        os.environ["WORKER_CANONICAL_METRICS"] = "1"
        collector = create_metrics_collector(self.settings)
        self.assertIsInstance(collector, CanonicalMetricsCollector)

    def test_canonical_false_returns_legacy(self):
        """WORKER_CANONICAL_METRICS=false selects LegacyMetricsCollector."""
        os.environ["WORKER_CANONICAL_METRICS"] = "false"
        collector = create_metrics_collector(self.settings)
        self.assertIsInstance(collector, LegacyMetricsCollector)

    def test_canonical_takes_priority_over_legacy(self):
        """WORKER_CANONICAL_METRICS=true wins even if WORKER_LEGACY_METRICS=true."""
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        os.environ["WORKER_LEGACY_METRICS"] = "true"
        collector = create_metrics_collector(self.settings)
        self.assertIsInstance(collector, CanonicalMetricsCollector)

    def test_legacy_collector_name(self):
        """LegacyMetricsCollector.collector_name() returns 'legacy'."""
        collector = create_metrics_collector(self.settings)
        self.assertEqual(collector.collector_name(), "legacy")

    def test_canonical_collector_name(self):
        """CanonicalMetricsCollector.collector_name() returns 'canonical'."""
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        collector = create_metrics_collector(
            MetricsSettings(directory=tempfile.mkdtemp())
        )
        self.assertEqual(collector.collector_name(), "canonical")

    def test_both_implementations_satisfy_same_interface(self):
        """Both implementations have the same public method surface."""
        legacy = LegacyMetricsCollector(self.settings)
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        canonical = create_metrics_collector(
            MetricsSettings(directory=tempfile.mkdtemp())
        )

        required_methods = [
            "collector_name",
            "increment_task_poll",
            "increment_task_poll_error",
            "increment_task_execution_started",
            "increment_task_execution_queue_full",
            "increment_uncaught_exception",
            "increment_worker_restart",
            "increment_task_paused",
            "increment_task_execution_error",
            "increment_task_ack_failed",
            "increment_task_ack_error",
            "increment_task_update_error",
            "increment_external_payload_used",
            "increment_workflow_start_error",
            "record_task_poll_time",
            "record_task_execute_time",
            "record_task_update_time",
            "record_api_request_time",
            "record_task_result_payload_size",
            "record_workflow_input_payload_size",
            "on_poll_started",
            "on_poll_completed",
            "on_poll_failure",
            "on_task_execution_started",
            "on_task_execution_completed",
            "on_task_execution_failure",
            "on_workflow_started",
            "on_workflow_input_payload_size",
            "on_workflow_payload_used",
            "on_task_result_payload_size",
            "on_task_payload_used",
        ]

        for method_name in required_methods:
            self.assertTrue(
                hasattr(legacy, method_name) and callable(getattr(legacy, method_name)),
                f"LegacyMetricsCollector missing method: {method_name}",
            )
            self.assertTrue(
                hasattr(canonical, method_name) and callable(getattr(canonical, method_name)),
                f"CanonicalMetricsCollector missing method: {method_name}",
            )


if __name__ == "__main__":
    unittest.main()
