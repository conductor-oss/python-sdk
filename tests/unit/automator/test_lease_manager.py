"""Tests for the centralized LeaseManager."""

import threading
import time
import unittest
from unittest.mock import MagicMock, call, patch

from conductor.client.automator.lease_tracker import (
    LeaseManager,
    LeaseInfo,
    LEASE_EXTEND_DURATION_FACTOR,
    LEASE_EXTEND_RETRY_COUNT,
)


class TestLeaseManagerTrackUntrack(unittest.TestCase):
    """Test track/untrack operations."""

    def setUp(self):
        LeaseManager._reset_instance()
        self.manager = LeaseManager(check_interval=60)  # Long interval — we trigger manually

    def tearDown(self):
        self.manager.shutdown()
        LeaseManager._reset_instance()

    def test_track_adds_task(self):
        client = MagicMock()
        self.manager.track('task-1', 'wf-1', 30.0, client)
        self.assertEqual(self.manager.tracked_count, 1)

    def test_untrack_removes_task(self):
        client = MagicMock()
        self.manager.track('task-1', 'wf-1', 30.0, client)
        self.manager.untrack('task-1')
        self.assertEqual(self.manager.tracked_count, 0)

    def test_untrack_nonexistent_is_noop(self):
        self.manager.untrack('nonexistent')
        self.assertEqual(self.manager.tracked_count, 0)

    def test_track_skips_short_interval(self):
        """Tasks with response_timeout < ~1.25s (interval < 1s) should be skipped."""
        client = MagicMock()
        self.manager.track('task-1', 'wf-1', 1.0, client)  # 1.0 * 0.8 = 0.8 < 1
        self.assertEqual(self.manager.tracked_count, 0)

    def test_track_accepts_valid_timeout(self):
        client = MagicMock()
        self.manager.track('task-1', 'wf-1', 10.0, client)  # 10 * 0.8 = 8.0 >= 1
        self.assertEqual(self.manager.tracked_count, 1)

    def test_track_multiple_tasks(self):
        client = MagicMock()
        for i in range(10):
            self.manager.track(f'task-{i}', f'wf-{i}', 30.0, client)
        self.assertEqual(self.manager.tracked_count, 10)

    def test_track_overwrites_existing(self):
        client = MagicMock()
        self.manager.track('task-1', 'wf-1', 30.0, client)
        self.manager.track('task-1', 'wf-1', 60.0, client)
        self.assertEqual(self.manager.tracked_count, 1)


class TestLeaseManagerHeartbeat(unittest.TestCase):
    """Test heartbeat dispatch logic."""

    def setUp(self):
        LeaseManager._reset_instance()
        self.manager = LeaseManager(check_interval=60)

    def tearDown(self):
        self.manager.shutdown()
        LeaseManager._reset_instance()

    def test_heartbeat_sent_when_due(self):
        """Heartbeat should be dispatched when interval has elapsed."""
        client = MagicMock()
        self.manager.track('task-1', 'wf-1', 10.0, client)

        # Fast-forward: set last_heartbeat_time to the past
        with self.manager._lock:
            info = self.manager._tracked['task-1']
            info.last_heartbeat_time = time.monotonic() - 20  # Well past the 8s interval

        self.manager._check_and_send()

        # Wait for the pool thread to execute the heartbeat
        self.manager._executor.shutdown(wait=True)
        client.update_task.assert_called_once()
        result = client.update_task.call_args[1]['body']
        self.assertEqual(result.task_id, 'task-1')
        self.assertEqual(result.workflow_instance_id, 'wf-1')
        self.assertTrue(result.extend_lease)

    def test_heartbeat_not_sent_when_not_due(self):
        """Heartbeat should NOT be dispatched when interval hasn't elapsed."""
        client = MagicMock()
        self.manager.track('task-1', 'wf-1', 10.0, client)

        self.manager._check_and_send()

        self.manager._executor.shutdown(wait=True)
        client.update_task.assert_not_called()

    def test_heartbeat_retries_on_failure(self):
        """Heartbeat should retry up to LEASE_EXTEND_RETRY_COUNT times."""
        client = MagicMock()
        client.update_task.side_effect = Exception("server error")

        info = LeaseInfo(
            task_id='task-1',
            workflow_instance_id='wf-1',
            response_timeout_seconds=30.0,
            last_heartbeat_time=time.monotonic(),
            interval_seconds=24.0,
            task_client=client,
        )

        with patch('conductor.client.automator.lease_tracker.time.sleep'):
            LeaseManager._send_heartbeat(info)

        self.assertEqual(client.update_task.call_count, LEASE_EXTEND_RETRY_COUNT)

    def test_heartbeat_stops_retrying_on_success(self):
        """Heartbeat should stop retrying after a successful call."""
        client = MagicMock()
        client.update_task.side_effect = [Exception("fail"), None]  # Fail then succeed

        info = LeaseInfo(
            task_id='task-1',
            workflow_instance_id='wf-1',
            response_timeout_seconds=30.0,
            last_heartbeat_time=time.monotonic(),
            interval_seconds=24.0,
            task_client=client,
        )

        with patch('conductor.client.automator.lease_tracker.time.sleep'):
            LeaseManager._send_heartbeat(info)

        self.assertEqual(client.update_task.call_count, 2)

    def test_multiple_tasks_heartbeats_dispatched_independently(self):
        """Each due task gets its own heartbeat dispatch."""
        client_a = MagicMock()
        client_b = MagicMock()

        self.manager.track('task-a', 'wf-a', 10.0, client_a)
        self.manager.track('task-b', 'wf-b', 10.0, client_b)

        # Make both due
        with self.manager._lock:
            past = time.monotonic() - 20
            self.manager._tracked['task-a'].last_heartbeat_time = past
            self.manager._tracked['task-b'].last_heartbeat_time = past

        self.manager._check_and_send()
        self.manager._executor.shutdown(wait=True)

        client_a.update_task.assert_called_once()
        client_b.update_task.assert_called_once()


class TestLeaseManagerNonBlocking(unittest.TestCase):
    """Test that heartbeats don't block the caller."""

    def setUp(self):
        LeaseManager._reset_instance()

    def tearDown(self):
        LeaseManager._reset_instance()

    def test_poll_loop_not_blocked_by_slow_heartbeat(self):
        """The caller should return immediately even if heartbeat is slow."""
        slow_client = MagicMock()
        slow_client.update_task.side_effect = lambda **kw: time.sleep(2)

        manager = LeaseManager(check_interval=60)
        manager.track('task-1', 'wf-1', 10.0, slow_client)

        with manager._lock:
            manager._tracked['task-1'].last_heartbeat_time = time.monotonic() - 20

        start = time.monotonic()
        manager._check_and_send()  # Submits to pool, returns immediately
        elapsed = time.monotonic() - start

        # _check_and_send should return in < 100ms (it just submits to the pool)
        self.assertLess(elapsed, 0.1, "check_and_send blocked for too long")

        manager.shutdown()


class TestLeaseManagerSingleton(unittest.TestCase):
    """Test singleton behavior."""

    def setUp(self):
        LeaseManager._reset_instance()

    def tearDown(self):
        LeaseManager._reset_instance()

    def test_get_instance_returns_same_object(self):
        a = LeaseManager.get_instance()
        b = LeaseManager.get_instance()
        self.assertIs(a, b)
        a.shutdown()

    def test_reset_creates_new_instance(self):
        a = LeaseManager.get_instance()
        LeaseManager._reset_instance()
        b = LeaseManager.get_instance()
        self.assertIsNot(a, b)
        b.shutdown()

    @patch('conductor.client.automator.lease_tracker.os.getpid')
    def test_new_instance_after_fork(self, mock_getpid):
        """After fork (different PID), a fresh instance should be created."""
        mock_getpid.return_value = 1000
        a = LeaseManager.get_instance()

        mock_getpid.return_value = 2000  # Simulate fork
        b = LeaseManager.get_instance()

        self.assertIsNot(a, b)
        a.shutdown()
        b.shutdown()


class TestLeaseManagerBackgroundThread(unittest.TestCase):
    """Test the background thread lifecycle."""

    def setUp(self):
        LeaseManager._reset_instance()

    def tearDown(self):
        LeaseManager._reset_instance()

    def test_thread_starts_lazily_on_first_track(self):
        manager = LeaseManager(check_interval=60)
        self.assertFalse(manager._started)

        client = MagicMock()
        manager.track('task-1', 'wf-1', 10.0, client)
        self.assertTrue(manager._started)
        self.assertTrue(manager._thread.is_alive())

        manager.shutdown()

    def test_thread_not_started_if_no_tracks(self):
        manager = LeaseManager(check_interval=60)
        self.assertFalse(manager._started)
        manager.shutdown()

    def test_background_thread_sends_heartbeats(self):
        """Verify the background thread actually dispatches heartbeats."""
        client = MagicMock()
        manager = LeaseManager(check_interval=0.1)  # Check every 100ms

        manager.track('task-1', 'wf-1', 10.0, client)

        # Make it due
        with manager._lock:
            manager._tracked['task-1'].last_heartbeat_time = time.monotonic() - 20

        # Wait for background thread to pick it up
        time.sleep(0.5)

        manager.shutdown()
        client.update_task.assert_called()

    def test_shutdown_stops_thread(self):
        manager = LeaseManager(check_interval=0.1)
        client = MagicMock()
        manager.track('task-1', 'wf-1', 10.0, client)
        self.assertTrue(manager._thread.is_alive())

        manager.shutdown()
        self.assertFalse(manager._thread.is_alive())


class TestLeaseManagerThreadSafety(unittest.TestCase):
    """Test concurrent track/untrack operations."""

    def setUp(self):
        LeaseManager._reset_instance()

    def tearDown(self):
        LeaseManager._reset_instance()

    def test_concurrent_track_untrack(self):
        """Many threads tracking/untracking should not corrupt state."""
        manager = LeaseManager(check_interval=60)
        client = MagicMock()
        errors = []

        def track_and_untrack(thread_id):
            try:
                for i in range(50):
                    task_id = f'task-{thread_id}-{i}'
                    manager.track(task_id, f'wf-{thread_id}', 30.0, client)
                    manager.untrack(task_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=track_and_untrack, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        self.assertEqual(manager.tracked_count, 0)
        manager.shutdown()


if __name__ == '__main__':
    unittest.main()
