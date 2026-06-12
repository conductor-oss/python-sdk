"""Unit tests for the poll-loop liveness watchdog on TaskRunner / AsyncTaskRunner.

The watchdog restarts a worker whose poll loop has gone silent (a wedged event
loop / poll thread that TaskHandler's is_alive()-only supervisor cannot detect).
We test the decision logic and env parsing; os._exit is patched so the test
process survives.
"""
import asyncio
import os
import time
import unittest
from unittest.mock import patch

from conductor.client.automator import async_task_runner as atr
from conductor.client.automator import task_runner as tr
from conductor.client.automator.async_task_runner import AsyncTaskRunner
from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker import Worker


def _async_worker():
    async def fn() -> dict:
        await asyncio.sleep(0)
        return {}
    return Worker(task_definition_name="wd_async", execute_function=fn, thread_count=2)


def _sync_worker():
    def fn() -> dict:
        return {}
    return Worker(task_definition_name="wd_sync", execute_function=fn, thread_count=2)


class TestPollStallTimeoutEnv(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_default_is_300(self):
        os.environ.pop("CONDUCTOR_WORKER_POLL_STALL_TIMEOUT_SECONDS", None)
        self.assertEqual(atr._get_poll_stall_timeout_seconds(), 300)
        self.assertEqual(tr._get_poll_stall_timeout_seconds(), 300)

    def test_custom_value(self):
        os.environ["CONDUCTOR_WORKER_POLL_STALL_TIMEOUT_SECONDS"] = "45"
        self.assertEqual(atr._get_poll_stall_timeout_seconds(), 45)

    def test_zero_disables(self):
        os.environ["CONDUCTOR_WORKER_POLL_STALL_TIMEOUT_SECONDS"] = "0"
        self.assertEqual(atr._get_poll_stall_timeout_seconds(), 0)

    def test_invalid_falls_back_to_default(self):
        os.environ["CONDUCTOR_WORKER_POLL_STALL_TIMEOUT_SECONDS"] = "not-a-number"
        self.assertEqual(atr._get_poll_stall_timeout_seconds(), 300)

    def test_negative_clamped_to_zero(self):
        os.environ["CONDUCTOR_WORKER_POLL_STALL_TIMEOUT_SECONDS"] = "-5"
        self.assertEqual(atr._get_poll_stall_timeout_seconds(), 0)


class _WatchdogChecks:
    """Shared assertions; subclasses provide a freshly-built runner."""

    def _make_runner(self):  # pragma: no cover - overridden
        raise NotImplementedError

    def test_fresh_loop_does_not_exit(self):
        r = self._make_runner()
        r._poll_stall_timeout = 10
        r._last_loop_activity = time.monotonic()
        with patch.object(os, "_exit") as mock_exit:
            self.assertFalse(r._check_poll_stall())
            mock_exit.assert_not_called()

    def test_stalled_loop_exits_with_code(self):
        r = self._make_runner()
        r._poll_stall_timeout = 5
        r._last_loop_activity = time.monotonic() - 60  # silent for 60s
        with patch.object(os, "_exit") as mock_exit:
            r._check_poll_stall()
            mock_exit.assert_called_once_with(70)

    def test_disabled_never_exits_even_when_stale(self):
        r = self._make_runner()
        r._poll_stall_timeout = 0  # disabled
        r._last_loop_activity = time.monotonic() - 99999
        with patch.object(os, "_exit") as mock_exit:
            self.assertFalse(r._check_poll_stall())
            mock_exit.assert_not_called()

    def test_shutdown_suppresses_exit(self):
        r = self._make_runner()
        r._poll_stall_timeout = 5
        r._last_loop_activity = time.monotonic() - 60
        r._shutdown = True
        with patch.object(os, "_exit") as mock_exit:
            self.assertFalse(r._check_poll_stall())
            mock_exit.assert_not_called()


class TestAsyncWatchdog(_WatchdogChecks, unittest.TestCase):
    def _make_runner(self):
        return AsyncTaskRunner(worker=_async_worker(), configuration=Configuration())


class TestSyncWatchdog(_WatchdogChecks, unittest.TestCase):
    def _make_runner(self):
        return TaskRunner(worker=_sync_worker(), configuration=Configuration())


if __name__ == "__main__":
    unittest.main()
