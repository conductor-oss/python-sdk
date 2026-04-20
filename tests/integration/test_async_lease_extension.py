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
import threading
import unittest

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


# -- Async Workers -----------------------------------------------------------

@worker_task(
    task_definition_name='async_lease_heartbeat_task',
    lease_extend_enabled=True,
    register_task_def=True,
    task_def=TaskDef(
        name='async_lease_heartbeat_task',
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
    task_definition_name='async_lease_no_heartbeat_task',
    lease_extend_enabled=False,
    register_task_def=True,
    task_def=TaskDef(
        name='async_lease_no_heartbeat_task',
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
    task_definition_name='async_lease_fast_with_hb',
    lease_extend_enabled=True,
    register_task_def=True,
    task_def=TaskDef(
        name='async_lease_fast_with_hb',
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
    task_definition_name='async_lease_fast_no_hb',
    lease_extend_enabled=False,
    register_task_def=True,
    task_def=TaskDef(
        name='async_lease_fast_no_hb',
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

class TestAsyncLeaseExtension(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from tests.integration.conftest import skip_if_server_unavailable
        skip_if_server_unavailable()

        cls.config = Configuration()
        cls.metadata_client = OrkesMetadataClient(cls.config)
        cls.workflow_client = OrkesWorkflowClient(cls.config)

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

    def _wait_for_workflow(self, wf_id, timeout_seconds=90):
        """Poll until workflow reaches a terminal state."""
        for _ in range(timeout_seconds):
            wf = self.workflow_client.get_workflow(wf_id, include_tasks=True)
            if wf.status in ('COMPLETED', 'FAILED', 'TIMED_OUT', 'TERMINATED'):
                return wf
            time.sleep(1)
        return self.workflow_client.get_workflow(wf_id, include_tasks=True)

    def _run_workers_in_background(self, duration_seconds=90):
        """Start workers in a background thread, return stop function."""
        handler = TaskHandler(
            configuration=self.config,
            scan_for_annotated_workers=True,
        )
        handler.start_processes()

        def stop():
            handler.stop_processes()

        timer = threading.Timer(duration_seconds, stop)
        timer.daemon = True
        timer.start()

        return stop

    # -- Tests ----------------------------------------------------------------

    def test_01_async_with_heartbeat_completes(self):
        """Async task WITH lease_extend_enabled=True completes when sleep > responseTimeout."""
        print("\n" + "=" * 80)
        print("TEST: Async with heartbeat — task should COMPLETE")
        print(f"  responseTimeoutSeconds={RESPONSE_TIMEOUT_SECONDS}s, task sleeps {TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_name = 'test_async_lease_heartbeat'
        self._register_workflow(wf_name, 'async_lease_heartbeat_task')

        stop_workers = self._run_workers_in_background(duration_seconds=90)
        time.sleep(3)  # let workers start

        try:
            wf_id = self._start_workflow(wf_name, 'ASYNC-HB-001')
            wf = self._wait_for_workflow(wf_id, timeout_seconds=80)

            print(f"\n  Workflow ID: {wf_id}")
            print(f"  Final status: {wf.status}")
            for task in (wf.tasks or []):
                print(f"  Task {task.task_def_name}: {task.status}")

            self.assertEqual(wf.status, 'COMPLETED',
                             f"Workflow should COMPLETE with heartbeat, got {wf.status}")

            tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
            task = tasks_by_ref.get('async_lease_heartbeat_task_ref')
            self.assertIsNotNone(task)
            self.assertEqual(task.status, 'COMPLETED')
            self.assertEqual(task.output_data.get('job_id'), 'ASYNC-HB-001')
            self.assertEqual(task.output_data.get('slept'), TASK_SLEEP_SECONDS)
            print("\n  PASS: Async task completed with heartbeat keeping lease alive")
        finally:
            stop_workers()

    def test_02_async_without_heartbeat_times_out(self):
        """Async task WITHOUT lease_extend_enabled times out when sleep > responseTimeout."""
        print("\n" + "=" * 80)
        print("TEST: Async without heartbeat — task should TIME OUT")
        print(f"  responseTimeoutSeconds={RESPONSE_TIMEOUT_SECONDS}s, task sleeps {TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_name = 'test_async_lease_no_heartbeat'
        self._register_workflow(wf_name, 'async_lease_no_heartbeat_task')

        stop_workers = self._run_workers_in_background(duration_seconds=90)
        time.sleep(3)

        try:
            wf_id = self._start_workflow(wf_name, 'ASYNC-NOHB-001')
            wf = self._wait_for_workflow(wf_id, timeout_seconds=80)

            print(f"\n  Workflow ID: {wf_id}")
            print(f"  Final status: {wf.status}")
            for task in (wf.tasks or []):
                print(f"  Task {task.task_def_name}: {task.status}")

            self.assertIn(wf.status, ('FAILED', 'TIMED_OUT'),
                          f"Workflow should FAIL/TIMEOUT without heartbeat, got {wf.status}")

            tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
            task = tasks_by_ref.get('async_lease_no_heartbeat_task_ref')
            self.assertIsNotNone(task)
            self.assertIn(task.status, ('TIMED_OUT', 'FAILED', 'CANCELED'),
                          f"Task should be TIMED_OUT/FAILED, got {task.status}")
            print("\n  PASS: Async task timed out as expected without heartbeat")
        finally:
            stop_workers()

    def test_03_no_performance_overhead(self):
        """Heartbeat tracking adds no meaningful overhead to fast async tasks."""
        print("\n" + "=" * 80)
        print("TEST: Performance — heartbeat enabled vs disabled on fast tasks")
        print(f"  Running {PERF_TASK_COUNT} tasks each, sleep={FAST_TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_with_hb = 'test_async_perf_with_hb'
        wf_no_hb = 'test_async_perf_no_hb'
        self._register_workflow(wf_with_hb, 'async_lease_fast_with_hb')
        self._register_workflow(wf_no_hb, 'async_lease_fast_no_hb')

        stop_workers = self._run_workers_in_background(duration_seconds=120)
        time.sleep(3)

        try:
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
        finally:
            stop_workers()


if __name__ == '__main__':
    unittest.main()
