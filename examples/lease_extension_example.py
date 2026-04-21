"""
Lease Extension (Automatic Heartbeat) Example
==============================================

Demonstrates how lease extension keeps a long-running task alive
even when its execution time exceeds responseTimeoutSeconds.

How it works:
- The task has responseTimeoutSeconds=30 (server times it out after 30s of inactivity)
- The worker sleeps for 60s (well beyond the timeout)
- With lease_extend_enabled=True, the SDK automatically sends heartbeats at 80% of
  responseTimeoutSeconds (every 24s), resetting the server's timeout timer
- The task completes successfully despite running 2x longer than the timeout

Without lease extension, the server would mark the task as TIMED_OUT after 30s.

Run:
    export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
    python examples/lease_extension_example.py
"""

import logging
import time

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.worker.worker_task import worker_task

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# Task timeout configuration
RESPONSE_TIMEOUT_SECONDS = 30  # Server times out after 30s of inactivity
TASK_SLEEP_SECONDS = 60        # Worker sleeps 60s (2x the timeout)

WORKFLOW_NAME = 'lease_extension_demo'
TASK_NAME = 'lease_heartbeat_demo_task'


# ---------------------------------------------------------------------------
# Worker with lease extension enabled
# ---------------------------------------------------------------------------

@worker_task(
    task_definition_name=TASK_NAME,
    lease_extend_enabled=True,       # Heartbeats keep the lease alive
    register_task_def=True,
    task_def=TaskDef(
        name=TASK_NAME,
        response_timeout_seconds=RESPONSE_TIMEOUT_SECONDS,
        timeout_seconds=300,         # Overall SLA: 5 minutes
        retry_count=0,
    ),
    overwrite_task_def=True,
)
def lease_heartbeat_demo_task(job_id: str) -> dict:
    """
    Long-running task that sleeps longer than responseTimeoutSeconds.

    Without lease extension, this would time out after 30s.
    With lease extension, the SDK sends heartbeats at 24s intervals (80% of 30s),
    keeping the task alive until completion.
    """
    logger.info(
        "Starting job %s — sleeping %ds (responseTimeout=%ds, heartbeat every %ds)",
        job_id, TASK_SLEEP_SECONDS, RESPONSE_TIMEOUT_SECONDS,
        int(RESPONSE_TIMEOUT_SECONDS * 0.8),
    )
    time.sleep(TASK_SLEEP_SECONDS)
    logger.info("Completed job %s", job_id)
    return {
        'job_id': job_id,
        'status': 'completed',
        'slept_seconds': TASK_SLEEP_SECONDS,
        'response_timeout_seconds': RESPONSE_TIMEOUT_SECONDS,
    }


# ---------------------------------------------------------------------------
# Workflow setup and execution
# ---------------------------------------------------------------------------

def register_workflow(metadata_client: OrkesMetadataClient):
    """Register a single-task workflow for the demo."""
    workflow = WorkflowDef(name=WORKFLOW_NAME, version=1)
    task = WorkflowTask(
        name=TASK_NAME,
        task_reference_name=f'{TASK_NAME}_ref',
        input_parameters={'job_id': '${workflow.input.job_id}'},
    )
    workflow._tasks = [task]
    try:
        metadata_client.update_workflow_def(workflow, overwrite=True)
    except Exception:
        metadata_client.register_workflow_def(workflow, overwrite=True)
    logger.info("Registered workflow: %s", WORKFLOW_NAME)


def wait_for_workflow(workflow_client: OrkesWorkflowClient, wf_id: str, timeout: int = 120):
    """Poll until the workflow reaches a terminal state."""
    for _ in range(timeout):
        wf = workflow_client.get_workflow(wf_id, include_tasks=True)
        if wf.status in ('COMPLETED', 'FAILED', 'TIMED_OUT', 'TERMINATED'):
            return wf
        time.sleep(1)
    return workflow_client.get_workflow(wf_id, include_tasks=True)


def main():
    config = Configuration()
    metadata_client = OrkesMetadataClient(config)
    workflow_client = OrkesWorkflowClient(config)

    # Register the workflow definition
    register_workflow(metadata_client)

    # Start workers (auto-discovers @worker_task functions)
    with TaskHandler(configuration=config, scan_for_annotated_workers=True) as handler:
        handler.start_processes()
        time.sleep(2)  # Let workers initialize

        # Start the workflow
        req = StartWorkflowRequest()
        req.name = WORKFLOW_NAME
        req.version = 1
        req.input = {'job_id': 'DEMO-001'}
        wf_id = workflow_client.start_workflow(start_workflow_request=req)

        print()
        print("=" * 70)
        print(f"  Workflow started: {wf_id}")
        print(f"  Task sleeps {TASK_SLEEP_SECONDS}s with responseTimeout={RESPONSE_TIMEOUT_SECONDS}s")
        print(f"  Heartbeat interval: {int(RESPONSE_TIMEOUT_SECONDS * 0.8)}s (80% of timeout)")
        print(f"  UI: {config.ui_host}/execution/{wf_id}")
        print("=" * 70)
        print()

        # Wait for completion
        wf = wait_for_workflow(workflow_client, wf_id, timeout=TASK_SLEEP_SECONDS + 30)

        print(f"  Final status: {wf.status}")
        for task in (wf.tasks or []):
            print(f"  Task '{task.task_def_name}': {task.status}")
            if task.output_data:
                print(f"    Output: {task.output_data}")

        if wf.status == 'COMPLETED':
            print("\n  SUCCESS: Task completed with lease extension keeping it alive!")
        else:
            print(f"\n  UNEXPECTED: Workflow ended with status {wf.status}")


if __name__ == '__main__':
    main()
