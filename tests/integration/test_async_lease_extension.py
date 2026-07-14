"""
E2E test for lease extension with async workers (AsyncTaskRunner).

Proves that the centralized LeaseManager works correctly with async workers:

1. WITH lease extension: async long-running task COMPLETES even when execution
   time exceeds responseTimeoutSeconds — heartbeats keep the lease alive.

2. WITHOUT lease extension: same async task TIMES OUT after responseTimeoutSeconds.

3. PERFORMANCE: async worker with heartbeat enabled but short task (no heartbeat
   actually needed) has no meaningful overhead vs. one without heartbeat tracking.

Run:
    export CONDUCTOR_SERVER_URL="http://localhost:8000/api"
    python3 -m pytest tests/integration/test_async_lease_extension.py -v -s

Prerequisites:
    - Conductor server running (e.g. http://localhost:8000/api)
"""

import asyncio
import logging
import os
import sys
import time
import unittest
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from conductor.client.automator.task_handler import TaskHandler, get_registered_workers
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Short response timeout — task must heartbeat to stay alive
RESPONSE_TIMEOUT_SECONDS = 10

# Task sleeps longer than the response timeout to prove heartbeat works.
# Must be long enough that the server's workflow sweeper catches the expired
# task BEFORE the worker completes.
TASK_SLEEP_SECONDS = 50

# Short task duration for performance test — well within timeout
FAST_TASK_SLEEP_SECONDS = 2

# Number of fast tasks for performance comparison
PERF_TASK_COUNT = 5

# Per-run suffix so this suite's task/workflow names don't collide with other
# runs (or other PRs/developers) on the shared dev server. With fixed names,
# concurrent runs poll the same queues and steal/strand each other's tasks,
# producing non-deterministic SCHEDULED/RUNNING failures.
RUN_ID = uuid4().hex[:8]
HEARTBEAT_TASK = f'async_lease_heartbeat_task_{RUN_ID}'
NO_HEARTBEAT_TASK = f'async_lease_no_heartbeat_task_{RUN_ID}'
FAST_HB_TASK = f'async_lease_fast_with_hb_{RUN_ID}'
FAST_NO_HB_TASK = f'async_lease_fast_no_hb_{RUN_ID}'


# -- Async Workers -----------------------------------------------------------

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
async def async_lease_heartbeat_task(job_id: str) -> dict:
    """Async long-running task with heartbeat — should complete."""
    logger.info("[async_heartbeat] Starting job %s, sleeping %ss (timeout=%ss)",
                job_id, TASK_SLEEP_SECONDS, RESPONSE_TIMEOUT_SECONDS)
    await asyncio.sleep(TASK_SLEEP_SECONDS)
    logger.info("[async_heartbeat] Completed job %s", job_id)
    return {'job_id': job_id, 'status': 'completed', 'slept': TASK_SLEEP_SECONDS}


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
async def async_lease_no_heartbeat_task(job_id: str) -> dict:
    """Async long-running task without heartbeat — should time out."""
    logger.info("[async_no_heartbeat] Starting job %s, sleeping %ss (timeout=%ss)",
                job_id, TASK_SLEEP_SECONDS, RESPONSE_TIMEOUT_SECONDS)
    await asyncio.sleep(TASK_SLEEP_SECONDS)
    logger.info("[async_no_heartbeat] Completed job %s", job_id)
    return {'job_id': job_id, 'status': 'completed', 'slept': TASK_SLEEP_SECONDS}


@worker_task(
    task_definition_name=FAST_HB_TASK,
    lease_extend_enabled=True,
    register_task_def=True,
    task_def=TaskDef(
        name=FAST_HB_TASK,
        response_timeout_seconds=60,
        timeout_seconds=120,
        retry_count=0,
    ),
    overwrite_task_def=True,
)
async def async_lease_fast_with_hb(job_id: str) -> dict:
    """Fast async task with heartbeat enabled — for overhead measurement."""
    await asyncio.sleep(FAST_TASK_SLEEP_SECONDS)
    return {'job_id': job_id, 'status': 'completed'}


@worker_task(
    task_definition_name=FAST_NO_HB_TASK,
    lease_extend_enabled=False,
    register_task_def=True,
    task_def=TaskDef(
        name=FAST_NO_HB_TASK,
        response_timeout_seconds=60,
        timeout_seconds=120,
        retry_count=0,
    ),
    overwrite_task_def=True,
)
async def async_lease_fast_no_hb(job_id: str) -> dict:
    """Fast async task without heartbeat — baseline for comparison."""
    await asyncio.sleep(FAST_TASK_SLEEP_SECONDS)
    return {'job_id': job_id, 'status': 'completed'}


# -- Test class --------------------------------------------------------------

@pytest.mark.slow_async
class TestAsyncLeaseExtension(unittest.TestCase):

    # Only the workers defined in THIS module. Used to scope the TaskHandler so
    # it doesn't spin up every @worker_task registered across the imported test
    # suite (that was ~24 worker processes started/torn down per test).
    WORKER_TASK_NAMES = {
        HEARTBEAT_TASK,
        NO_HEARTBEAT_TASK,
        FAST_HB_TASK,
        FAST_NO_HB_TASK,
    }

    @classmethod
    def setUpClass(cls):
        from tests.integration.conftest import skip_if_server_unavailable
        skip_if_server_unavailable()

        cls.config = Configuration()
        cls.metadata_client = OrkesMetadataClient(cls.config)
        cls.workflow_client = OrkesWorkflowClient(cls.config)

        # Start workers ONCE for the whole class (not per test) and only the
        # four workers this module needs. Both changes cut the repeated
        # process-scan/start/stop overhead that dominated the runtime.
        workers = [
            w for w in get_registered_workers()
            if w.get_task_definition_name() in cls.WORKER_TASK_NAMES
        ]
        cls._task_handler = TaskHandler(
            workers=workers,
            configuration=cls.config,
            scan_for_annotated_workers=False,
        )
        cls._task_handler.start_processes()
        time.sleep(3)  # let workers start (once, not per test)

        # Confirm every worker this module needs was actually started with a
        # live process. If one silently fails to start, its task sits in
        # SCHEDULED forever and surfaces later as an opaque "workflow still
        # RUNNING" assertion; fail loudly here naming the exact worker instead.
        started = {}
        for worker, process in zip(cls._task_handler.workers,
                                   cls._task_handler.task_runner_processes):
            started[worker.get_task_definition_name()] = process.is_alive()
        logger.info("Started workers (name -> alive): %s", started)
        missing = [n for n in cls.WORKER_TASK_NAMES
                   if not started.get(n, False)]
        assert not missing, (
            f"workers not started/alive: {missing}; started={started}")

    @classmethod
    def tearDownClass(cls):
        handler = getattr(cls, '_task_handler', None)
        if handler is not None:
            handler.stop_processes()

    def _register_workflow(self, wf_name, task_names):
        """Register a workflow with one or more tasks in sequence."""
        workflow = WorkflowDef(name=wf_name, version=1)
        tasks = []
        for task_name in (task_names if isinstance(task_names, list) else [task_names]):
            tasks.append(WorkflowTask(
                name=task_name,
                task_reference_name=f'{task_name}_ref',
                input_parameters={'job_id': '${workflow.input.job_id}'},
            ))
        workflow._tasks = tasks
        try:
            self.metadata_client.update_workflow_def(workflow, overwrite=True)
        except Exception:
            self.metadata_client.register_workflow_def(workflow, overwrite=True)
        logger.info("Registered workflow: %s", wf_name)

    def _start_workflow(self, wf_name, job_id):
        """Start a workflow and return the execution ID."""
        req = StartWorkflowRequest()
        req.name = wf_name
        req.version = 1
        req.input = {'job_id': job_id}
        wf_id = self.workflow_client.start_workflow(start_workflow_request=req)
        logger.info("Started workflow %s: %s", wf_name, wf_id)
        return wf_id

    TERMINAL_STATES = ('COMPLETED', 'FAILED', 'TIMED_OUT', 'TERMINATED')

    def _wait_for_workflow(self, wf_id, timeout_seconds=90):
        """Poll until workflow reaches a terminal state. If it doesn't within
        the budget, dump server-side diagnostics so the ensuing assertion shows
        *why* (e.g. a task stuck in SCHEDULED with no poller) rather than only a
        bare status mismatch.
        """
        for _ in range(timeout_seconds):
            wf = self.workflow_client.get_workflow(wf_id, include_tasks=True)
            if wf.status in self.TERMINAL_STATES:
                return wf
            time.sleep(1)
        wf = self.workflow_client.get_workflow(wf_id, include_tasks=True)
        if wf.status not in self.TERMINAL_STATES:
            print(f"  [diag] workflow {wf_id} still {wf.status} "
                  f"after {timeout_seconds}s")
            self._dump_workflow_diagnostics(wf)
        return wf

    def _dump_workflow_diagnostics(self, wf):
        """Print task statuses plus server-side poll data / queue size so a
        non-terminal workflow shows *why* (e.g. a task stuck in SCHEDULED with
        no poller = the worker isn't consuming it), rather than only a bare
        status assertion. Poll data is server-side, so it survives regardless
        of worker child-process log capture.
        """
        from conductor.client.orkes.orkes_task_client import OrkesTaskClient
        task_client = OrkesTaskClient(self.config)

        # Worker processes can die *after* setUpClass; report current liveness
        # so we can tell "worker crashed mid-suite" apart from "worker alive but
        # not polling / server not timing out".
        handler = getattr(self, '_task_handler', None)
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

    # -- Tests ----------------------------------------------------------------

    def test_01_async_with_heartbeat_completes(self):
        """Async task WITH lease_extend_enabled=True completes when sleep > responseTimeout."""
        print("\n" + "=" * 80)
        print("TEST: Async with heartbeat — task should COMPLETE")
        print(f"  responseTimeoutSeconds={RESPONSE_TIMEOUT_SECONDS}s, task sleeps {TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_name = f'test_async_lease_heartbeat_{RUN_ID}'
        self._register_workflow(wf_name, HEARTBEAT_TASK)

        wf_id = self._start_workflow(wf_name, 'ASYNC-HB-001')
        wf = self._wait_for_workflow(wf_id, timeout_seconds=80)

        print(f"\n  Workflow ID: {wf_id}")
        print(f"  Final status: {wf.status}")
        for task in (wf.tasks or []):
            print(f"  Task {task.task_def_name}: {task.status}")

        self.assertEqual(wf.status, 'COMPLETED',
                         f"Workflow should COMPLETE with heartbeat, got {wf.status}")

        tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
        task = tasks_by_ref.get(f'{HEARTBEAT_TASK}_ref')
        self.assertIsNotNone(task)
        self.assertEqual(task.status, 'COMPLETED')
        self.assertEqual(task.output_data.get('job_id'), 'ASYNC-HB-001')
        self.assertEqual(task.output_data.get('slept'), TASK_SLEEP_SECONDS)
        print("\n  PASS: Async task completed with heartbeat keeping lease alive")

    def test_02_async_without_heartbeat_times_out(self):
        """Async task WITHOUT lease_extend_enabled times out when sleep > responseTimeout."""
        print("\n" + "=" * 80)
        print("TEST: Async without heartbeat — task should TIME OUT")
        print(f"  responseTimeoutSeconds={RESPONSE_TIMEOUT_SECONDS}s, task sleeps {TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_name = f'test_async_lease_no_heartbeat_{RUN_ID}'
        self._register_workflow(wf_name, NO_HEARTBEAT_TASK)

        wf_id = self._start_workflow(wf_name, 'ASYNC-NOHB-001')
        wf = self._wait_for_workflow(wf_id, timeout_seconds=80)

        print(f"\n  Workflow ID: {wf_id}")
        print(f"  Final status: {wf.status}")
        for task in (wf.tasks or []):
            print(f"  Task {task.task_def_name}: {task.status}")

        self.assertIn(wf.status, ('FAILED', 'TIMED_OUT'),
                      f"Workflow should FAIL/TIMEOUT without heartbeat, got {wf.status}")

        tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
        task = tasks_by_ref.get(f'{NO_HEARTBEAT_TASK}_ref')
        self.assertIsNotNone(task)
        self.assertIn(task.status, ('TIMED_OUT', 'FAILED', 'CANCELED'),
                      f"Task should be TIMED_OUT/FAILED, got {task.status}")
        print("\n  PASS: Async task timed out as expected without heartbeat")

    def test_03_no_performance_overhead(self):
        """Heartbeat tracking adds no meaningful overhead to fast async tasks."""
        print("\n" + "=" * 80)
        print("TEST: Performance — heartbeat enabled vs disabled on fast tasks")
        print(f"  Running {PERF_TASK_COUNT} tasks each, sleep={FAST_TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_with_hb = f'test_async_perf_with_hb_{RUN_ID}'
        wf_no_hb = f'test_async_perf_no_hb_{RUN_ID}'
        self._register_workflow(wf_with_hb, FAST_HB_TASK)
        self._register_workflow(wf_no_hb, FAST_NO_HB_TASK)

        # Run tasks WITH heartbeat tracking
        hb_workflow_ids = []
        for i in range(PERF_TASK_COUNT):
            wf_id = self._start_workflow(wf_with_hb, f'PERF-HB-{i:03d}')
            hb_workflow_ids.append(wf_id)

        # Run tasks WITHOUT heartbeat tracking
        no_hb_workflow_ids = []
        for i in range(PERF_TASK_COUNT):
            wf_id = self._start_workflow(wf_no_hb, f'PERF-NOHB-{i:03d}')
            no_hb_workflow_ids.append(wf_id)

        # Wait for all to complete
        hb_times = []
        for wf_id in hb_workflow_ids:
            wf = self._wait_for_workflow(wf_id, timeout_seconds=30)
            self.assertEqual(wf.status, 'COMPLETED',
                             f"Fast HB task should complete, got {wf.status}")
            task = wf.tasks[0]
            duration_ms = task.end_time - task.start_time
            hb_times.append(duration_ms)

        no_hb_times = []
        for wf_id in no_hb_workflow_ids:
            wf = self._wait_for_workflow(wf_id, timeout_seconds=30)
            self.assertEqual(wf.status, 'COMPLETED',
                             f"Fast no-HB task should complete, got {wf.status}")
            task = wf.tasks[0]
            duration_ms = task.end_time - task.start_time
            no_hb_times.append(duration_ms)

        avg_hb = sum(hb_times) / len(hb_times)
        avg_no_hb = sum(no_hb_times) / len(no_hb_times)
        overhead_ms = avg_hb - avg_no_hb
        overhead_pct = (overhead_ms / avg_no_hb * 100) if avg_no_hb > 0 else 0

        print(f"\n  With heartbeat:    avg {avg_hb:.0f}ms  {hb_times}")
        print(f"  Without heartbeat: avg {avg_no_hb:.0f}ms  {no_hb_times}")
        print(f"  Overhead:          {overhead_ms:+.0f}ms ({overhead_pct:+.1f}%)")

        # Heartbeat tracking should add < 500ms overhead per task
        # (LeaseManager.track is just a dict insert + set add)
        self.assertLess(overhead_ms, 500,
                        f"Heartbeat overhead too high: {overhead_ms:.0f}ms")

        print("\n  PASS: No meaningful performance overhead from heartbeat tracking")


if __name__ == '__main__':
    unittest.main()
