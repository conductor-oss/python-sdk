"""
Tests for the metrics factory and gated metrics selection.
"""

import os
import shutil
import tempfile
import unittest
from unittest import mock

from conductor.client.configuration.settings.metrics_settings import (
    MetricsSettings,
    _reset_cleaned_metrics_directories,
)
from conductor.client.telemetry.metrics_factory import (
    create_metrics_collector,
    create_metrics_collector_for_parent,
)
from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector
from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector


class TestMetricsFactory(unittest.TestCase):

    def setUp(self):
        _reset_cleaned_metrics_directories()
        self._saved_env = {}
        for key in ("WORKER_CANONICAL_METRICS", "WORKER_LEGACY_METRICS"):
            self._saved_env[key] = os.environ.pop(key, None)
        self.metrics_dir = tempfile.mkdtemp()

    def tearDown(self):
        for key, val in self._saved_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        if os.path.exists(self.metrics_dir):
            shutil.rmtree(self.metrics_dir)
        _reset_cleaned_metrics_directories()

    def _make_settings(self, **kwargs):
        kwargs.setdefault("directory", self.metrics_dir)
        return MetricsSettings(**kwargs)

    def test_default_returns_legacy(self):
        """With no env vars set, factory returns LegacyMetricsCollector."""
        collector = create_metrics_collector(self._make_settings())
        self.assertIsInstance(collector, LegacyMetricsCollector)

    def test_canonical_true_returns_canonical(self):
        """WORKER_CANONICAL_METRICS=true selects CanonicalMetricsCollector."""
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        collector = create_metrics_collector(self._make_settings())
        self.assertIsInstance(collector, CanonicalMetricsCollector)

    def test_canonical_1_returns_canonical(self):
        """WORKER_CANONICAL_METRICS=1 selects CanonicalMetricsCollector."""
        os.environ["WORKER_CANONICAL_METRICS"] = "1"
        collector = create_metrics_collector(self._make_settings())
        self.assertIsInstance(collector, CanonicalMetricsCollector)

    def test_canonical_yes_returns_canonical(self):
        """WORKER_CANONICAL_METRICS=yes selects CanonicalMetricsCollector."""
        os.environ["WORKER_CANONICAL_METRICS"] = "yes"
        collector = create_metrics_collector(self._make_settings())
        self.assertIsInstance(collector, CanonicalMetricsCollector)

    def test_canonical_false_returns_legacy(self):
        """WORKER_CANONICAL_METRICS=false selects LegacyMetricsCollector."""
        os.environ["WORKER_CANONICAL_METRICS"] = "false"
        collector = create_metrics_collector(self._make_settings())
        self.assertIsInstance(collector, LegacyMetricsCollector)

    def test_canonical_takes_priority_over_legacy(self):
        """WORKER_CANONICAL_METRICS=true wins even if WORKER_LEGACY_METRICS=true."""
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        os.environ["WORKER_LEGACY_METRICS"] = "true"
        collector = create_metrics_collector(self._make_settings())
        self.assertIsInstance(collector, CanonicalMetricsCollector)

    def test_legacy_collector_name(self):
        """LegacyMetricsCollector.collector_name() returns 'legacy'."""
        collector = create_metrics_collector(self._make_settings())
        self.assertEqual(collector.collector_name(), "legacy")

    def test_canonical_collector_name(self):
        """CanonicalMetricsCollector.collector_name() returns 'canonical'."""
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        collector = create_metrics_collector(self._make_settings())
        self.assertEqual(collector.collector_name(), "canonical")

    def test_both_implementations_satisfy_same_interface(self):
        """Both implementations have the same public method surface."""
        legacy = LegacyMetricsCollector(self._make_settings())
        os.environ["WORKER_CANONICAL_METRICS"] = "true"
        canonical = create_metrics_collector(self._make_settings())

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

    def test_create_collector_is_non_destructive(self):
        """create_metrics_collector runs in every spawned worker, so it must
        NEVER delete .db files -- doing so would wipe live sibling metrics.
        Even with clean_directory=True, the factory leaves existing files
        untouched; cleanup is the parent's responsibility."""
        db_path = os.path.join(self.metrics_dir, "gauge_livesum_12345.db")
        with open(db_path, "w") as f:
            f.write("fake")

        settings = MetricsSettings(directory=self.metrics_dir, clean_directory=True)
        create_metrics_collector(settings)

        self.assertTrue(
            os.path.exists(db_path),
            "create_metrics_collector must not delete .db files (worker path)",
        )

    def test_create_for_parent_cleans_then_returns_collector(self):
        """create_metrics_collector_for_parent is the parent/owner entrypoint: it
        cleans the directory up front (honoring clean_directory) and then returns
        a valid collector, so the parent's own first write is not orphaned."""
        db_path = os.path.join(self.metrics_dir, "gauge_livesum_12345.db")
        with open(db_path, "w") as f:
            f.write("fake")

        settings = MetricsSettings(directory=self.metrics_dir, clean_directory=True)
        collector = create_metrics_collector_for_parent(settings)

        self.assertFalse(
            os.path.exists(db_path),
            "create_metrics_collector_for_parent must clean .db files with clean_directory=True",
        )
        self.assertIsInstance(collector, LegacyMetricsCollector)

    def test_clean_directory_removes_db_files(self):
        """MetricsSettings.clean_metrics_directory() removes .db files when
        clean_directory=True."""
        db_path = os.path.join(self.metrics_dir, "gauge_livesum_12345.db")
        with open(db_path, "w") as f:
            f.write("fake")

        settings = MetricsSettings(directory=self.metrics_dir, clean_directory=True)
        settings.clean_metrics_directory()

        self.assertFalse(
            os.path.exists(db_path),
            "clean_directory=True should remove existing .db files",
        )

    def test_clean_metrics_directory_noop_without_flags(self):
        """clean_metrics_directory() leaves .db files untouched when neither
        clean_directory nor clean_dead_pids is set."""
        db_path = os.path.join(self.metrics_dir, "gauge_livesum_12345.db")
        with open(db_path, "w") as f:
            f.write("fake")

        settings = MetricsSettings(directory=self.metrics_dir)
        settings.clean_metrics_directory()

        self.assertTrue(
            os.path.exists(db_path),
            "clean_metrics_directory() must not delete files when no flag is set",
        )

    def test_clean_metrics_directory_idempotent_per_process(self):
        """The destructive cleanup runs only on the first call per directory.
        A second call must not wipe .db files a live process (e.g. the parent's
        collector) started writing after the first clean -- this is what lets
        the entrypoint clean up front and TaskHandler safely call it again."""
        settings = MetricsSettings(directory=self.metrics_dir, clean_directory=True)
        settings.clean_metrics_directory()

        # Simulate a live process creating a .db file after the first clean.
        live_db = os.path.join(self.metrics_dir, f"gauge_livesum_{os.getpid()}.db")
        with open(live_db, "w") as f:
            f.write("fake")

        settings.clean_metrics_directory()

        self.assertTrue(
            os.path.exists(live_db),
            "second clean_metrics_directory() call must be a no-op and keep the file",
        )

    def test_clean_dead_pids_removes_dead_pid_file(self):
        """clean_dead_pids=True removes .db files whose PID no longer exists."""
        dead_pid = 2_000_000_000
        db_path = os.path.join(self.metrics_dir, f"gauge_livesum_{dead_pid}.db")
        with open(db_path, "w") as f:
            f.write("fake")

        settings = MetricsSettings(directory=self.metrics_dir, clean_dead_pids=True)
        settings.clean_metrics_directory()

        self.assertFalse(
            os.path.exists(db_path),
            "clean_dead_pids=True should remove .db file for a non-existent PID",
        )

    def test_clean_dead_pids_keeps_live_pid_file(self):
        """clean_dead_pids=True keeps .db files whose PID is still alive."""
        live_pid = os.getpid()
        db_path = os.path.join(self.metrics_dir, f"gauge_livesum_{live_pid}.db")
        with open(db_path, "w") as f:
            f.write("fake")

        settings = MetricsSettings(directory=self.metrics_dir, clean_dead_pids=True)
        settings.clean_metrics_directory()

        self.assertTrue(
            os.path.exists(db_path),
            "clean_dead_pids=True must keep .db files for live PIDs",
        )

    @mock.patch("os.kill", side_effect=PermissionError("Operation not permitted"))
    def test_clean_dead_pids_keeps_file_on_permission_error(self, _mock_kill):
        """PermissionError from os.kill means the process is alive but owned
        by another user -- the .db file must be kept."""
        db_path = os.path.join(self.metrics_dir, "gauge_livesum_99999.db")
        with open(db_path, "w") as f:
            f.write("fake")

        settings = MetricsSettings(directory=self.metrics_dir, clean_dead_pids=True)
        settings.clean_metrics_directory()

        self.assertTrue(
            os.path.exists(db_path),
            "PermissionError should be treated as 'process alive' -- file must be kept",
        )


if __name__ == "__main__":
    unittest.main()
