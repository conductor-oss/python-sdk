"""
E2E test for lease extension (heartbeat) feature.

Proves that:
1. WITH lease extension enabled: a long-running task completes successfully
   even when its execution time exceeds responseTimeoutSeconds, because
   heartbeats keep the lease alive.

2. WITHOUT lease extension: the same long-running task times out on the
   server after responseTimeoutSeconds and is retried/failed.

Run:
    export CONDUCTOR_SERVER_URL="http://localhost:6767/api"
    python3 -m pytest tests/integration/test_lease_extension.py -v -s

Prerequisites:
    - Conductor server running (default: http://localhost:6767/api)
"""

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
# Must be long enough that the server's workflow sweeper (which runs every
# ~30s) catches the expired task BEFORE the worker completes.
TASK_SLEEP_SECONDS = 50


# -- Workers -----------------------------------------------------------------

# Worker WITH lease extension enabled — heartbeats keep it alive
@worker_task(
    task_definition_name='lease_heartbeat_task',
    lease_extend_enabled=True,
    register_task_def=True,
    task_def=TaskDef(
        name='lease_heartbeat_task',
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
    task_definition_name='lease_no_heartbeat_task',
    lease_extend_enabled=False,
    register_task_def=True,
    task_def=TaskDef(
        name='lease_no_heartbeat_task',
        response_timeout_seconds=RESPONSE_TIMEOUT_SECONDS,
        timeout_seconds=120,
        retry_count=0,
    ),
    overwrite_task_def=True,
)
def lease_no_heartbeat_task(job_id: str) -> dict:
    """Long-running task without heartbeat — should time out."""
    logger.info("[no_heartbeat_task] Starting job %s, sleeping %ss (timeout=%ss)",
                job_id, TASK_SLEEP_SECONDS, RESPONSE_TIMEOUT_SECONDS)
    time.sleep(TASK_SLEEP_SECONDS)
    logger.info("[no_heartbeat_task] Completed job %s", job_id)
    return {'job_id': job_id, 'status': 'completed', 'slept': TASK_SLEEP_SECONDS}


# -- Test class --------------------------------------------------------------

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

    def _wait_for_workflow(self, wf_id, timeout_seconds=60):
        """Poll until workflow reaches a terminal state."""
        for i in range(timeout_seconds):
            wf = self.workflow_client.get_workflow(wf_id, include_tasks=True)
            if wf.status in ('COMPLETED', 'FAILED', 'TIMED_OUT', 'TERMINATED'):
                return wf
            time.sleep(1)
        # Return whatever state it's in after timeout
        return self.workflow_client.get_workflow(wf_id, include_tasks=True)

    def _run_workers_in_background(self, duration_seconds=60):
        """Start workers in a background thread, return stop function."""
        handler = TaskHandler(
            configuration=self.config,
            scan_for_annotated_workers=True,
        )
        handler.start_processes()

        def stop():
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

        wf_name = 'test_lease_heartbeat'
        self._register_workflow(wf_name, 'lease_heartbeat_task')

        stop_workers = self._run_workers_in_background(duration_seconds=90)
        time.sleep(3)  # let workers start

        try:
            wf_id = self._start_workflow(wf_name, 'HEARTBEAT-001')
            wf = self._wait_for_workflow(wf_id, timeout_seconds=80)

            print(f"\n  Final status: {wf.status}")
            for task in (wf.tasks or []):
                print(f"  Task {task.task_def_name}: {task.status}")

            self.assertEqual(wf.status, 'COMPLETED',
                             f"Workflow should COMPLETE with heartbeat, got {wf.status}")

            # Verify task output
            tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
            task = tasks_by_ref.get('lease_heartbeat_task_ref')
            self.assertIsNotNone(task)
            self.assertEqual(task.status, 'COMPLETED')
            self.assertEqual(task.output_data.get('job_id'), 'HEARTBEAT-001')
            self.assertEqual(task.output_data.get('slept'), TASK_SLEEP_SECONDS)
            print("\n  PASS: Task completed with heartbeat keeping lease alive")
        finally:
            stop_workers()

    def test_02_without_heartbeat_times_out(self):
        """Task WITHOUT lease_extend_enabled times out when sleep > responseTimeout."""
        print("\n" + "=" * 80)
        print("TEST: Without heartbeat — task should TIME OUT")
        print(f"  responseTimeoutSeconds={RESPONSE_TIMEOUT_SECONDS}s, task sleeps {TASK_SLEEP_SECONDS}s")
        print("=" * 80)

        wf_name = 'test_lease_no_heartbeat'
        self._register_workflow(wf_name, 'lease_no_heartbeat_task')

        stop_workers = self._run_workers_in_background(duration_seconds=90)
        time.sleep(3)  # let workers start

        try:
            wf_id = self._start_workflow(wf_name, 'NO-HEARTBEAT-001')
            wf = self._wait_for_workflow(wf_id, timeout_seconds=80)

            print(f"\n  Final status: {wf.status}")
            for task in (wf.tasks or []):
                print(f"  Task {task.task_def_name}: {task.status}")

            # Without heartbeat, the task should timeout or fail
            self.assertIn(wf.status, ('FAILED', 'TIMED_OUT'),
                          f"Workflow should FAIL/TIMEOUT without heartbeat, got {wf.status}")

            tasks_by_ref = {t.reference_task_name: t for t in wf.tasks}
            task = tasks_by_ref.get('lease_no_heartbeat_task_ref')
            self.assertIsNotNone(task)
            self.assertIn(task.status, ('TIMED_OUT', 'FAILED', 'CANCELED'),
                          f"Task should be TIMED_OUT/FAILED, got {task.status}")
            print("\n  PASS: Task timed out as expected without heartbeat")
        finally:
            stop_workers()


if __name__ == '__main__':
    unittest.main()
