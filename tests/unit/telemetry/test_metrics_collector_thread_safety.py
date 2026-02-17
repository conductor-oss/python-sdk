import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_collector import MetricsCollector


class TestMetricsCollectorThreadSafety(unittest.TestCase):
    """Test thread safety of MetricsCollector."""

    def setUp(self):
        """Create temporary directory for metrics."""
        self.temp_dir = tempfile.mkdtemp()
        self.metrics_settings = MetricsSettings(directory=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_concurrent_counter_increments(self):
        """Test that concurrent counter increments from multiple threads work correctly."""
        collector = MetricsCollector(self.metrics_settings)

        # Number of threads and increments per thread
        num_threads = 10
        increments_per_thread = 100

        # Track exceptions from threads
        exceptions = []

        def increment_task_poll():
            try:
                for i in range(increments_per_thread):
                    collector.increment_task_poll(f"task_type_{threading.current_thread().name}")
            except Exception as e:
                exceptions.append(e)

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=increment_task_poll, name=f"thread_{i}")
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)

        # Verify no exceptions occurred
        self.assertEqual(len(exceptions), 0, f"Exceptions occurred during concurrent access: {exceptions}")

    def test_concurrent_mixed_metrics(self):
        """Test that concurrent mixed metric operations (counters, gauges, quantiles) work correctly."""
        collector = MetricsCollector(self.metrics_settings)

        num_threads = 5
        operations_per_thread = 50
        exceptions = []

        def mixed_operations():
            try:
                for i in range(operations_per_thread):
                    # Mix different metric types
                    collector.increment_task_poll("task_a")
                    collector.record_task_result_payload_size("task_a", 1024)
                    collector.record_task_execute_time("task_a", 0.123)
                    collector.increment_worker_restart("task_a")
            except Exception as e:
                exceptions.append(e)

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=mixed_operations, name=f"thread_{i}")
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10.0)

        # Verify no exceptions occurred
        self.assertEqual(len(exceptions), 0, f"Exceptions occurred during concurrent access: {exceptions}")

    def test_concurrent_quantile_recording(self):
        """Test that concurrent quantile recording works correctly."""
        collector = MetricsCollector(self.metrics_settings)

        num_threads = 5
        observations_per_thread = 50
        exceptions = []

        def record_quantiles():
            try:
                for i in range(observations_per_thread):
                    # Record execution time (which uses quantiles)
                    collector.record_task_execute_time("task_b", float(i) / 100.0)
            except Exception as e:
                exceptions.append(e)

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=record_quantiles, name=f"thread_{i}")
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10.0)

        # Verify no exceptions occurred
        self.assertEqual(len(exceptions), 0, f"Exceptions occurred during concurrent access: {exceptions}")


if __name__ == '__main__':
    unittest.main()
