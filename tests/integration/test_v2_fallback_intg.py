"""
Integration test for update-task-v2 graceful degradation.

Verifies that when update-task-v2 is unavailable (or available), the SDK
correctly auto-detects and falls back to v1 while still completing workflows.

Run:
    python -m pytest tests/integration/test_v2_fallback_intg.py -v -s
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
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.worker.worker_task import worker_task

logger = logging.getLogger(__name__)

WORKFLOW_NAME = "test_v2_fallback_workflow"
WORKFLOW_VERSION = 1


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

@worker_task(task_definition_name="v2_fallback_task_a", thread_count=3, register_task_def=True)
async def fallback_worker_a(task_index: int = 0) -> dict:
    return {"worker": "v2_fallback_task_a", "task_index": task_index}


@worker_task(task_definition_name="v2_fallback_task_b", thread_count=3, register_task_def=True)
async def fallback_worker_b(task_index: int = 0) -> dict:
    return {"worker": "v2_fallback_task_b", "task_index": task_index}


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestV2FallbackIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from tests.integration.conftest import skip_if_server_unavailable
        skip_if_server_unavailable()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(process)d] %(name)-45s %(levelname)-10s %(message)s",
        )
        logging.getLogger("conductor.client").setLevel(logging.WARNING)

        cls.config = Configuration()
        cls.workflow_client = OrkesWorkflowClient(cls.config)
        cls.metadata_client = OrkesMetadataClient(cls.config)

    def test_0_register_workflow(self):
        """Register workflow with 2 task types (3 tasks each)."""
        tasks = []
        idx = 0
        for task_type, count in [("v2_fallback_task_a", 3), ("v2_fallback_task_b", 3)]:
            for i in range(count):
                idx += 1
                tasks.append(
                    WorkflowTask(
                        name=task_type,
                        task_reference_name=f"{task_type}_{i + 1}",
                        input_parameters={"task_index": idx},
                    )
                )

        workflow = WorkflowDef(name=WORKFLOW_NAME, version=WORKFLOW_VERSION)
        workflow._tasks = tasks
        try:
            self.metadata_client.update_workflow_def(workflow, overwrite=True)
        except Exception:
            self.metadata_client.register_workflow_def(workflow, overwrite=True)
        print(f"\n  Registered workflow '{WORKFLOW_NAME}' with {len(tasks)} tasks")

    def test_1_workflows_complete_with_v2_or_fallback(self):
        """Start workers and verify workflows complete regardless of v2 support.

        This test doesn't force a 404 — it runs against the real server.
        If v2 is available, it uses v2. If not, it auto-detects and falls back.
        Either way, all workflows should complete successfully.
        """
        workflow_count = 5

        handler_ready = threading.Event()
        handler_ref = {}

        def _run_workers():
            handler = TaskHandler(
                configuration=self.config,
                scan_for_annotated_workers=True,
            )
            handler_ref["h"] = handler
            handler.start_processes()
            handler_ready.set()
            handler_ref["stop"] = threading.Event()
            handler_ref["stop"].wait()
            handler.stop_processes()

        worker_thread = threading.Thread(target=_run_workers, daemon=True)
        worker_thread.start()
        handler_ready.wait(timeout=30)
        self.assertTrue(handler_ready.is_set(), "Workers failed to start within 30s")
        time.sleep(3)  # Warm up

        try:
            # Submit workflows
            workflow_ids = []
            for i in range(workflow_count):
                req = StartWorkflowRequest()
                req.name = WORKFLOW_NAME
                req.version = WORKFLOW_VERSION
                req.input = {"run_index": i}
                wf_id = self.workflow_client.start_workflow(start_workflow_request=req)
                workflow_ids.append(wf_id)

            print(f"\n  Submitted {len(workflow_ids)} workflows")

            # Wait for completion
            deadline = time.time() + 60  # 60s timeout
            pending = set(workflow_ids)
            completed = 0
            failed = 0

            while pending and time.time() < deadline:
                still_pending = set()
                for wf_id in pending:
                    try:
                        wf = self.workflow_client.get_workflow(wf_id, include_tasks=False)
                    except Exception:
                        still_pending.add(wf_id)
                        continue

                    if wf.status == "COMPLETED":
                        completed += 1
                    elif wf.status in ("FAILED", "TERMINATED", "TIMED_OUT"):
                        failed += 1
                        logger.warning("Workflow %s ended with status %s", wf_id, wf.status)
                    else:
                        still_pending.add(wf_id)

                pending = still_pending
                if pending:
                    time.sleep(1)

            print(f"  Results: {completed} completed, {failed} failed, {len(pending)} pending")

            self.assertEqual(len(pending), 0, f"{len(pending)} workflows did not complete in time")
            self.assertEqual(completed, workflow_count, f"Expected {workflow_count} completed, got {completed}")

        finally:
            handler_ref.get("stop", threading.Event()).set()
            worker_thread.join(timeout=15)


if __name__ == "__main__":
    unittest.main(verbosity=2)
