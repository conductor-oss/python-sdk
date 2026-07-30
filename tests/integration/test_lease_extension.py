"""
E2E test for lease extension (heartbeat) feature.

Proves that:
1. WITH lease extension enabled: a long-running task completes successfully
   even when its execution time exceeds responseTimeoutSeconds, because
   heartbeats keep the lease alive.

2. WITHOUT lease extension: the same long-running task times out on the
   server after responseTimeoutSeconds and is retried/failed.

Run:
    export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
    python3 -m pytest tests/integration/test_lease_extension.py -v -s

Prerequisites:
    - Conductor server running (default: http://localhost:8080/api)
"""

import logging
import os
import sys
import time
import threading
import unittest
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

from tests.integration.retry_helpers import (
    TERMINAL_WORKFLOW_STATES,
    retry_on_transient as _retry_on_transient,
    wait_for_workflow_terminal,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Short response timeout — task must heartbeat to stay alive
RESPONSE_TIMEOUT_SECONDS = 10

# The heartbeat task sleeps longer than the response timeout so that, without
# heartbeats, its lease would expire mid-execution. Heartbeats keep it alive and
# it still completes. This only needs to exceed RESPONSE_TIMEOUT_SECONDS.
TASK_SLEEP_SECONDS = 50

# The no-heartbeat task must NOT report COMPLETED before the server times its
# expired lease out; otherwise the completion "wins" the race and the task ends
# up COMPLETED (the historical flake on a loaded shared server, where the
# sweeper runs late). Holding the task far longer than any server timeout path
# (responseTimeout + sweeper, and the task's own timeoutSeconds) guarantees the
# server always times it out first. The test itself doesn't wait this long: it
# polls for the terminal state and returns as soon as the timeout lands, and
# teardown force-terminates the still-sleeping worker process.
NO_HEARTBEAT_HOLD_SECONDS = 600

# Poll budget/interval for waiting on the workflow to reach the expected
# terminal state. Generous ceiling so slow-server variance is absorbed; the
# happy path returns in well under a minute.
POLL_TIMEOUT_SECONDS = 600
POLL_INTERVAL_SECONDS = 5

# Per-run suffix so this suite's task/workflow names don't collide with other
# runs (or other PRs/developers) on the shared dev server. With fixed names,
# concurrent runs poll the same queues and steal/strand each other's tasks,
# producing non-deterministic SCHEDULED/RUNNING failures.
RUN_ID = uuid4().hex[:8]
HEARTBEAT_TASK = f'lease_heartbeat_task_{RUN_ID}'
NO_HEARTBEAT_TASK = f'lease_no_heartbeat_task_{RUN_ID}'


# -- Workers -----------------------------------------------------------------

# Worker WITH lease extension enabled — heartbeats keep it alive
@worker_task(
    task_definition_name=HEARTBEAT_TASK,
    lease_extend_enabled=True,
    register_task_def=True,
    task_def=TaskDef(
        name=HEARTBEAT_TASK,
        response_timeout_seconds=RESPONSE_TIMEOUT_SECONDS,
        timeout_seconds=180,
        retry_count=0,
    ),
    overwrite_task_def=True,
)
def lease_heartbeat_task(job_id: str) -> dict:
    """Long-running task with heartbeat — should complete."""
    logger.info("[heartbeat_task] Starting job %s, sleeping %ss (timeout=%ss)",
                job_id, TASK_SLEEP_SECONDS, RESPONSE_TIMEOUT_SECONDS)
    time.sleep(TASK_SLEEP_SECONDS)
    logger.info("[heartbeat_task] Completed job %s", job_id)
    return {'job_id': job_id, 'status': 'completed', 'slept': TASK_SLEEP_SECONDS}


# Worker WITHOUT lease extension — will time out
@worker_task(
    task_definition_name=NO_HEARTBEAT_TASK,
    lease_extend_enabled=False,
    register_task_def=True,
    task_def=TaskDef(
        name=NO_HEARTBEAT_TASK,
        response_timeout_seconds=RESPONSE_TIMEOUT_SECONDS,
        timeout_seconds=120,
        retry_count=0,
    ),
    overwrite_task_def=True,
)
def lease_no_heartbeat_task(job_id: str) -> dict:
    """Long-running task without heartbeat — should time out.

    Holds the task well past every server timeout path so the server always
    times the expired lease out before this ever tries to report completion.
    """
    logger.info("[no_heartbeat_task] Starting job %s, holding %ss (timeout=%ss)",
                job_id, NO_HEARTBEAT_HOLD_SECONDS, RESPONSE_TIMEOUT_SECONDS)
    time.sleep(NO_HEARTBEAT_HOLD_SECONDS)
    logger.info("[no_heartbeat_task] Completed job %s", job_id)
    return {'job_id': job_id, 'status': 'completed', 'slept': NO_HEARTBEAT_HOLD_SECONDS}


# -- Test class --------------------------------------------------------------

@pytest.mark.slow_sync
class TestLeaseExtension(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from tests.integration.conftest import skip_if_server_unavailable
        skip_if_server_unavailable()

        cls.config = Configuration()
        cls.metadata_client = OrkesMetadataClient(cls.config)
        cls.workflow_client = OrkesWorkflowClient(cls.config)

    def _register_workflow(self, wf_name, task_name):
        """Register a single-task workflow."""
        workflow = WorkflowDef(name=wf_name, version=1)
        task = WorkflowTask(
            name=task_name,
            task_reference_name=f'{task_name}_ref',
            input_parameters={'job_id': '${workflow.input.job_id}'},
        )
        workflow._tasks = [task]
        try:
            _retry_on_transient(self.metadata_client.update_workflow_def,
                                 workflow, overwrite=True)
        except Exception:
            _retry_on_transient(self.metadata_client.register_workflow_def,
                                 workflow, overwrite=True)
        logger.info("Registered workflow: %s", wf_name)

    def _start_workflow(self, wf_name, job_id):
        """Start a workflow and return the execution ID."""
        req = StartWorkflowRequest()
        req.name = wf_name
        req.version = 1
        req.input = {'job_id': job_id}
        wf_id = _retry_on_transient(self.workflow_client.start_workflow,
                                    start_workflow_request=req)
        logger.info("Started workflow %s: %s", wf_name, wf_id)
        return wf_id

    TERMINAL_STATES = TERMINAL_WORKFLOW_STATES

    def _wait_for_workflow(self, wf_id, timeout_seconds=POLL_TIMEOUT_SECONDS,
                           poll_interval=POLL_INTERVAL_SECONDS):
        """Poll until workflow reaches a terminal state. If it doesn't within
        the budget, dump server-side diagnostics so the ensuing assertion shows
        *why* (e.g. a task stuck in SCHEDULED with no poller) rather than only a
        bare status mismatch. Delegates the polling loop to the shared
        ``wait_for_workflow_terminal`` (transient blips swallowed, real errors
        raised), then does a definitive final fetch + diagnostics on give-up.
        """
        wf = wait_for_workflow_terminal(
            self.workflow_client, wf_id,
            timeout_seconds=timeout_seconds, poll_interval=poll_interval,
            include_tasks=True, terminal_states=self.TERMINAL_STATES,
            swallow='transient', log=lambda _msg: None)
        if wf is not None and wf.status in self.TERMINAL_STATES:
            return wf
        wf = _retry_on_transient(self.workflow_client.get_workflow,
                                 wf_id, include_tasks=True)
        if wf.status not in self.TERMINAL_STATES:
            print(f"  [diag] workflow {wf_id} still {wf.status} "
                  f"after {timeout_seconds}s")
            self._dump_workflow_diagnostics(wf)
        return wf

    def _dump_workflow_diagnostics(self, wf):
        """Print task statuses plus server-side poll data / queue size so a
        non-terminal workflow shows *why* (e.g. a task stuck in SCHEDULED with
        no poller = the worker isn't consuming it). Poll data is server-side,
        so it survives regardless of worker child-process log capture.
        """
        from conductor.client.orkes.orkes_task_client import OrkesTaskClient
        task_client = OrkesTaskClient(self.config)

        handler = getattr(self, '_active_handler', None)
        if handler is not None:
            alive = {}
            for worker, process in zip(handler.workers, handler.task_runner_processes):
                alive[worker.get_task_definition_name()] = process.is_alive()
            print(f"  [diag] worker liveness: {alive}")

        for task in (getattr(wf, 'tasks', None) or []):
            print(f"  [diag] task {task.task_def_name}: {task.status}")
            try:
                queue_size = task_client.get_queue_size_for_task(task.task_def_name)
                poll_data = task_client.get_task_poll_data(task.task_def_name) or []
                pollers = [(p.worker_id, p.domain, p.last_poll_time) for p in poll_data]
                print(f"  [diag] {task.task_def_name}: "
                      f"queue_size={queue_size} pollers={pollers}")
            except Exception as e:  # diagnostics must never mask the real failure
                print(f"  [diag] {task.task_def_name}: failed to fetch poll data: {e!r}")

    def _run_workers_in_background(self, duration_seconds=POLL_TIMEOUT_SECONDS + 60):
        """Start workers in a background thread, return stop function.

        Workers stay alive across the whole poll window; the test's `finally`
        calls the returned stop() as soon as it finishes (usually in well under
        a minute), and the timer is only a backstop. stop() is idempotent so the
        backstop firing after the test already stopped is harmless.
        """
        handler = TaskHandler(
            configuration=self.config,
            scan_for_annotated_workers=True,
        )
        handler.start_processes()
        # Expose the handler so _dump_workflow_diagnostics can report liveness.
        self.__class__._active_handler = handler

        stopped = threading.Event()

        def stop():
            if stopped.is_set():
                return
            stopped.set()
            handler.stop_processes()

        # Auto-stop after duration
        timer = threading.Timer(duration_seconds, stop)
        timer.daemon = True
        timer.start()

        return stop

    def test_01_with_heartbeat_completes(self):
        """Task WITH lease_extend_enabled=True completes even when sleep > responseTimeout."""
        print("\n" + "=" * 80)
        print("TEST: With heartbeat — task should COMPLETE")
        print(f"  responseTimeoutSeconds={RESPONSE_TIMEOUT_SECONDS}s, task sleeps {TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_name = f'test_lease_heartbeat_{RUN_ID}'
        self._register_workflow(wf_name, HEARTBEAT_TASK)

        stop_workers = self._run_workers_in_background()
        time.sleep(3)  # let workers start

        try:
            wf_id = self._start_workflow(wf_name, 'HEARTBEAT-001')
            wf = self._wait_for_workflow(wf_id)

            print(f"\n  Final status: {wf.status}")
            for task in (wf.tasks or []):
                print(f"  Task {task.task_def_name}: {task.status}")

            self.assertEqual(wf.status, 'COMPLETED',
                             f"Workflow should COMPLETE with heartbeat, got {wf.status}")

            # Verify task output
            tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
            task = tasks_by_ref.get(f'{HEARTBEAT_TASK}_ref')
            self.assertIsNotNone(task)
            self.assertEqual(task.status, 'COMPLETED')
            self.assertEqual(task.output_data.get('job_id'), 'HEARTBEAT-001')
            self.assertEqual(task.output_data.get('slept'), TASK_SLEEP_SECONDS)
            print("\n  PASS: Task completed with heartbeat keeping lease alive")
        finally:
            stop_workers()

    # NOTE: excluded from the long-* CI buckets. This scenario asserts a purely
    # server-side mechanic — the server timing out the task's expired lease on
    # its own. The sdkdev server does not seem to consistently/reliably time out
    # the task by itself on a timeline that works with integration testing, so
    # gating CI on it produces flakes unrelated to the SDK. The SDK behaviour
    # (heartbeats keeping a task alive) is still covered by test_01.
    # Deselected via `-m "... and not server_timeout_unreliable"`; still runs
    # under --bucket=all or when targeted directly.
    @pytest.mark.server_timeout_unreliable
    def test_02_without_heartbeat_times_out(self):
        """Task WITHOUT lease_extend_enabled times out when sleep > responseTimeout."""
        print("\n" + "=" * 80)
        print("TEST: Without heartbeat — task should TIME OUT")
        print(f"  responseTimeoutSeconds={RESPONSE_TIMEOUT_SECONDS}s, task holds {NO_HEARTBEAT_HOLD_SECONDS}s")
        print("=" * 80)

        wf_name = f'test_lease_no_heartbeat_{RUN_ID}'
        self._register_workflow(wf_name, NO_HEARTBEAT_TASK)

        stop_workers = self._run_workers_in_background()
        time.sleep(3)  # let workers start

        try:
            wf_id = self._start_workflow(wf_name, 'NO-HEARTBEAT-001')
            wf = self._wait_for_workflow(wf_id)

            print(f"\n  Final status: {wf.status}")
            for task in (wf.tasks or []):
                print(f"  Task {task.task_def_name}: {task.status}")

            # Without heartbeat, the task should timeout or fail
            self.assertIn(wf.status, ('FAILED', 'TIMED_OUT'),
                          f"Workflow should FAIL/TIMEOUT without heartbeat, got {wf.status}")

            tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
            task = tasks_by_ref.get(f'{NO_HEARTBEAT_TASK}_ref')
            self.assertIsNotNone(task)
            self.assertIn(task.status, ('TIMED_OUT', 'FAILED', 'CANCELED'),
                          f"Task should be TIMED_OUT/FAILED, got {task.status}")
            print("\n  PASS: Task timed out as expected without heartbeat")
        finally:
            stop_workers()


if __name__ == '__main__':
    unittest.main()
