import os
import time
import unittest
from multiprocessing import Value
from unittest.mock import patch

import httpx

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from tests.unit.resources.workers import ClassWorker


# These are shared across forked worker processes (multiprocessing.Value uses shared memory).
_client_creations = Value("i", 0)
_requests_total = Value("i", 0)
_poll_requests = Value("i", 0)
_fail_next_poll = Value("i", 0)


class _FlakyHttpxClient:
    """
    Stand-in for httpx.Client used by RESTClientObject during chaos tests.

    This avoids binding to local TCP sockets (which may be disallowed in some sandboxes)
    while still exercising:
    - RESTClientObject protocol-error handling + connection reset + retry
    - TaskRunner polling loop in a real worker subprocess
    """

    def __init__(self, *args, **kwargs):
        with _client_creations.get_lock():
            _client_creations.value += 1

    def close(self):
        return

    def request(self, method, url, params=None, content=None, timeout=None, headers=None):
        with _requests_total.get_lock():
            _requests_total.value += 1

        # TaskRunner polling endpoint:
        #   GET {host}/tasks/poll/batch/{tasktype}
        if "/tasks/poll/batch/" in url:
            with _poll_requests.get_lock():
                _poll_requests.value += 1

            with _fail_next_poll.get_lock():
                should_fail = _fail_next_poll.value > 0
                if should_fail:
                    _fail_next_poll.value -= 1

            if should_fail:
                raise httpx.ProtocolError("chaos: simulated ConnectionTerminated/protocol error")

            return httpx.Response(
                200,
                content=b"[]",
                headers={"Content-Type": "application/json"},
            )

        # TaskRunner update endpoint:
        #   POST {host}/tasks
        if url.endswith("/tasks"):
            return httpx.Response(
                200,
                content=b"OK",
                headers={"Content-Type": "text/plain"},
            )

        return httpx.Response(404, content=b"")


@unittest.skipUnless(os.getenv("RUN_CHAOS_TESTS") == "1", "Set RUN_CHAOS_TESTS=1 to run chaos tests")
@unittest.skipIf(os.name == "nt", "Chaos tests rely on fork semantics on POSIX")
class TestTaskHandlerChaos(unittest.TestCase):
    def setUp(self) -> None:
        with _client_creations.get_lock():
            _client_creations.value = 0
        with _requests_total.get_lock():
            _requests_total.value = 0
        with _poll_requests.get_lock():
            _poll_requests.value = 0
        with _fail_next_poll.get_lock():
            _fail_next_poll.value = 0

        # Patch httpx.Client in the SDK REST layer so worker subprocesses inherit it via fork.
        import conductor.client.http.rest as rest_module
        self._patcher = patch.object(rest_module.httpx, "Client", _FlakyHttpxClient)
        self._patcher.start()

    def tearDown(self) -> None:
        try:
            self._patcher.stop()
        except Exception:
            pass

    def test_protocol_error_triggers_client_reset_and_polling_continues(self):
        # Fail the first poll request at the transport layer (simulates a terminated keep-alive connection).
        with _fail_next_poll.get_lock():
            _fail_next_poll.value = 1

        worker = ClassWorker("chaos_task")
        worker.poll_interval = 1.0  # ms
        config = Configuration(server_api_url="http://chaos/api", debug=False)

        with TaskHandler(
            workers=[worker],
            configuration=config,
            scan_for_annotated_workers=False,
            monitor_interval_seconds=0.1,
            restart_backoff_seconds=0.0,
            restart_backoff_max_seconds=0.0,
        ) as handler:
            handler.start_processes()

            deadline = time.time() + 5
            while time.time() < deadline and int(_poll_requests.value) < 10:
                time.sleep(0.05)

            # At least one poll happened, and the worker is still alive.
            self.assertGreaterEqual(int(_poll_requests.value), 1)
            self.assertTrue(handler.is_healthy())

            # We should have created at least two httpx clients in the worker due to the reset+retry path.
            self.assertGreaterEqual(int(_client_creations.value), 2)

    def test_worker_process_restarts_after_kill(self):
        worker = ClassWorker("chaos_task")
        worker.poll_interval = 1.0  # ms
        config = Configuration(server_api_url="http://chaos/api", debug=False)

        with TaskHandler(
            workers=[worker],
            configuration=config,
            scan_for_annotated_workers=False,
            monitor_interval_seconds=0.1,
            restart_backoff_seconds=0.0,
            restart_backoff_max_seconds=0.0,
        ) as handler:
            handler.start_processes()

            deadline = time.time() + 5
            while time.time() < deadline and int(_poll_requests.value) < 5:
                time.sleep(0.05)

            status0 = handler.get_worker_process_status()[0]
            old_pid = status0["pid"]
            self.assertIsNotNone(old_pid)

            handler.task_runner_processes[0].kill()

            deadline = time.time() + 10
            while time.time() < deadline:
                status = handler.get_worker_process_status()[0]
                if status["restart_count"] >= 1 and status["pid"] != old_pid and status["alive"]:
                    break
                time.sleep(0.05)

            status1 = handler.get_worker_process_status()[0]
            self.assertGreaterEqual(status1["restart_count"], 1)
            self.assertNotEqual(status1["pid"], old_pid)
            self.assertTrue(status1["alive"])

