"""
Conductor Python SDK - End-to-End Worker Example

This example demonstrates the complete workflow execution lifecycle:
1. Register a workflow definition
2. Start a workflow execution
3. Start workers to process tasks
4. Monitor workflow completion

Demonstrates:
- Sync workers (def) → TaskRunner (ThreadPoolExecutor)
- Async workers (async def) → AsyncTaskRunner (pure async/await)
- Long-running tasks with TaskInProgress (manual lease extension)
- Worker discovery from multiple packages
- Prometheus metrics collection

Usage:
    export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
    python3 examples/workers_e2e.py

Or with Orkes Cloud:
    export CONDUCTOR_SERVER_URL="https://developer.orkescloud.com/api"
    export CONDUCTOR_AUTH_KEY="your-key"
    export CONDUCTOR_AUTH_SECRET="your-secret"
    python3 examples/workers_e2e.py
"""

import json
import logging
import os
import shutil
import sys
import time
from typing import Union

# Add parent directory to path so we can import conductor modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context import get_task_context, TaskInProgress
from conductor.client.worker.worker_task import worker_task
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

# Optional: Import custom event listener if available
try:
    from examples.task_listener_example import TaskExecutionLogger
    HAS_TASK_LOGGER = True
except ImportError:
    HAS_TASK_LOGGER = False


# ============================================================================
# WORKER DEFINITIONS
# ============================================================================

@worker_task(
    task_definition_name='calculate',
    thread_count=100,  # High concurrency - async workers can handle it!
    poll_timeout=10
)
async def calculate_fibonacci(n: int) -> int:
    """
    ASYNC WORKER - Automatically uses AsyncTaskRunner

    This function is defined as 'async def', so the SDK automatically:
    - Creates AsyncTaskRunner (not TaskRunner)
    - Uses pure async/await execution (no thread overhead)
    - Runs in a single event loop with high concurrency

    Architecture:
    - Thread count: 1 (event loop only)
    - Concurrency: Up to 100 concurrent tasks
    - Memory: ~3-6 MB per process

    Note: This is a CPU-bound task (fibonacci calculation), which isn't
    ideal for async workers. Use this pattern for I/O-bound operations
    (HTTP calls, database queries, file I/O).
    """
    if n <= 1:
        return n
    return await calculate_fibonacci(n - 1) + await calculate_fibonacci(n - 2)


@worker_task(
    task_definition_name='long_running_task',
    thread_count=5,
    poll_timeout=100
)
def long_running_task() -> Union[dict, TaskInProgress]:
    """
    SYNC WORKER - Demonstrates manual lease extension with TaskInProgress

    This function is defined as 'def' (not async), so the SDK automatically:
    - Creates TaskRunner (not AsyncTaskRunner)
    - Uses ThreadPoolExecutor for execution
    - Runs tasks in separate threads

    Architecture:
    - Thread count: 1 (main) + 5 (pool) = 6 threads
    - Concurrency: Up to 5 concurrent tasks
    - Memory: ~8-10 MB per process

    Lease Extension Pattern:
    - Returns TaskInProgress when work is not complete
    - Conductor re-queues the task after callback_after_seconds
    - Worker polls the same task again (poll_count increments)
    - This prevents task timeout for long-running operations

    Returns:
        Union[dict, TaskInProgress]:
            - TaskInProgress: When still processing (extends lease)
            - dict: When complete (final result)
    """
    # Get task context to access task metadata
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()  # How many times this task has been polled
    task_id = ctx.get_task_id()        # Unique task ID

    # Add log that will be visible in Conductor UI
    ctx.add_log(f"Processing long-running task, poll {poll_count}/5")

    if poll_count < 5:
        # STILL WORKING - Extend lease by returning TaskInProgress
        # This tells Conductor: "I'm not done yet, call me back in 1 second"
        return TaskInProgress(
            callback_after_seconds=1,  # Re-queue task after 1 second
            output={
                # Intermediate output visible in Conductor UI
                'task_id': task_id,
                'status': 'processing',
                'poll_count': poll_count,
                'progress': poll_count * 20,  # 20%, 40%, 60%, 80%, 100%
                'message': f'Working on poll {poll_count}/5'
            }
        )

    # COMPLETE - Return final result after 5 polls
    ctx.add_log(f"Long-running task completed after {poll_count} polls")
    return {
        'task_id': task_id,
        'status': 'completed',
        'result': 'success',
        'total_time_seconds': poll_count,
        'total_polls': poll_count
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main function orchestrating the end-to-end workflow execution.

    Flow:
    1. Load configuration from environment variables
    2. Register workflow definition with Conductor
    3. Start workflow execution (creates tasks in SCHEDULED state)
    4. Start workers (poll for tasks, execute, update results)
    5. Monitor workflow completion
    """

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    # Create Configuration from environment variables:
    # Required:
    #   - CONDUCTOR_SERVER_URL: http://localhost:8080/api
    # Optional (for Orkes Cloud):
    #   - CONDUCTOR_AUTH_KEY: your-key-id
    #   - CONDUCTOR_AUTH_SECRET: your-key-secret
    api_config = Configuration()

    # ========================================================================
    # METRICS SETUP (Optional)
    # ========================================================================

    # Configure Prometheus metrics with HTTP server
    # Metrics will be available at: http://localhost:8000/metrics
    metrics_dir = os.path.join('/tmp', 'conductor_metrics')

    # Clean up previous metrics
    if os.path.exists(metrics_dir):
        shutil.rmtree(metrics_dir)
    os.makedirs(metrics_dir, exist_ok=True)

    metrics_settings = MetricsSettings(
        directory=metrics_dir,      # SQLite .db files for multiprocess coordination
        update_interval=10,         # Update metrics every 10 seconds
        http_port=8000              # HTTP server on port 8000
    )

    # ========================================================================
    # STEP 1: REGISTER WORKFLOW DEFINITION
    # ========================================================================

    print("\n" + "="*80)
    print("STEP 1: Registering Workflow Definition")
    print("="*80)

    # Load workflow definition from JSON file
    # This file contains the workflow structure (tasks, order, inputs)
    workflow_json_path = os.path.join(os.path.dirname(__file__), 'workers_e2e_workflow.json')
    with open(workflow_json_path, 'r') as f:
        workflow_def_json = json.load(f)

    # Create metadata client for registering workflows
    metadata_client = OrkesMetadataClient(api_config)

    # Create WorkflowDef object from JSON
    # Note: We filter out server-generated fields (createTime, updateTime)
    # and only include fields needed for registration
    workflow_def = WorkflowDef(
        name=workflow_def_json['name'],                    # Workflow name
        description=workflow_def_json.get('description'),  # Description
        version=workflow_def_json.get('version', 1),       # Version number
        tasks=workflow_def_json.get('tasks', []),          # Task definitions
        input_parameters=workflow_def_json.get('inputParameters', []),
        output_parameters=workflow_def_json.get('outputParameters', {}),
        failure_workflow=workflow_def_json.get('failureWorkflow', ''),
        schema_version=workflow_def_json.get('schemaVersion', 2),
        restartable=workflow_def_json.get('restartable', True),
        workflow_status_listener_enabled=workflow_def_json.get('workflowStatusListenerEnabled', False),
        owner_email=workflow_def_json.get('ownerEmail'),
        timeout_policy=workflow_def_json.get('timeoutPolicy', 'ALERT_ONLY'),
        timeout_seconds=workflow_def_json.get('timeoutSeconds', 0),
        variables=workflow_def_json.get('variables', {}),
        input_template=workflow_def_json.get('inputTemplate', {}),
        enforce_schema=workflow_def_json.get('enforceSchema', True),
        metadata=workflow_def_json.get('metadata', {})
    )

    # Register the workflow (overwrite if it already exists)
    try:
        metadata_client.register_workflow_def(workflow_def, overwrite=True)
        print(f"✓ Registered workflow: {workflow_def.name} (version {workflow_def.version})")
    except Exception as e:
        print(f"⚠ Workflow registration failed (may already exist): {e}")

    # ========================================================================
    # STEP 2: START WORKFLOW EXECUTION
    # ========================================================================

    print("\n" + "="*80)
    print("STEP 2: Starting Workflow Execution")
    print("="*80)

    # Create workflow client for executing workflows
    workflow_client = OrkesWorkflowClient(api_config)

    # Create a StartWorkflowRequest
    # This tells Conductor to create workflow tasks in SCHEDULED state
    start_request = StartWorkflowRequest()
    start_request.name = workflow_def.name      # Which workflow to run
    start_request.version = workflow_def.version  # Which version
    start_request.input = {"job_id": "demo-job-001"}  # Workflow input data

    # Start the workflow - this returns a unique workflow execution ID
    workflow_id = workflow_client.start_workflow(start_workflow_request=start_request)

    # Construct URL to view workflow execution in Conductor UI
    workflow_url = f"{api_config.ui_host}/execution/{workflow_id}"

    print(f"✓ Workflow started: {workflow_id}")
    print(f"\n📊 View workflow execution:")
    print(f"   {workflow_url}")
    print(f"\n📈 View metrics:")
    print(f"   curl http://localhost:8000/metrics")

    # Give Conductor a moment to queue the tasks
    time.sleep(1)

    # ========================================================================
    # STEP 3: START WORKERS TO PROCESS TASKS
    # ========================================================================

    print("\n" + "="*80)
    print("STEP 3: Starting Workers")
    print("="*80)
    print("Workers will poll for and execute the workflow tasks...")
    print("Press Ctrl+C to stop\n")

    # Setup optional event listeners for custom monitoring
    event_listeners = [TaskExecutionLogger()] if HAS_TASK_LOGGER else []

    try:
        # Create TaskHandler - orchestrates worker processes
        with TaskHandler(
            configuration=api_config,
            metrics_settings=metrics_settings,
            scan_for_annotated_workers=True,  # Auto-discover @worker_task decorated functions
            import_modules=[
                "helloworld.greetings_worker",  # greet, greet_async workers
                "user_example.user_workers"     # fetch_user, update_user workers
            ],
            event_listeners=event_listeners  # Optional: custom event listeners
        ) as task_handler:

            # Start worker processes
            # TaskHandler spawns one process per worker:
            # - Process 1: calculate (async def) → AsyncTaskRunner
            # - Process 2: long_running_task (def) → TaskRunner
            # - Process 3: greet (def) → TaskRunner
            # - Process 4: greet_async (async def) → AsyncTaskRunner
            # - Process 5: fetch_user (async def) → AsyncTaskRunner
            # - Process 6: update_user (def) → TaskRunner
            task_handler.start_processes()

            print("\n⏳ Workers are running. Waiting for workflow to complete...")
            print(f"   Monitor at: {workflow_url}\n")

            # Block until workers are stopped (Ctrl+C or process termination)
            task_handler.join_processes()

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down gracefully...")

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise

    finally:
        # ====================================================================
        # STEP 4: CHECK FINAL WORKFLOW STATUS
        # ====================================================================

        # Query workflow status to see if it completed successfully
        try:
            workflow_status = workflow_client.get_workflow(workflow_id, include_tasks=False)
            print(f"\n📋 Final workflow status: {workflow_status.status}")
            print(f"   View details: {workflow_url}")
        except Exception:
            # Ignore errors (workflow client may be unavailable)
            pass

    print("\n✅ Workers stopped. Goodbye!")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    """
    End-to-End Example: Workers, Workflow, and Monitoring

    Workers in this example:
    -----------------------
    1. calculate (async def) - AsyncTaskRunner
       - Fibonacci calculation (demo only - use sync for CPU-bound)
       - thread_count=100 (100 concurrent async tasks in 1 event loop!)

    2. long_running_task (def) - TaskRunner
       - Demonstrates manual lease extension with TaskInProgress
       - Takes 5 seconds total (5 polls × 1 second each)
       - thread_count=5 (5 concurrent threads)

    3. greet (def) - TaskRunner
       - Simple sync worker from helloworld package

    4. greet_async (async def) - AsyncTaskRunner
       - Simple async worker from helloworld package

    5. fetch_user (async def) - AsyncTaskRunner
       - HTTP API call using httpx (from user_example package)

    6. update_user (def) - TaskRunner
       - Process User dataclass (from user_example package)

    Workflow Tasks (see workers_e2e_workflow.json):
    -----------------------------------------------
    1. calculate (n=20)
    2. greet_async (name="Orkes")
    3. greet (name from greet_async output)
    4. long_running_task (demonstrates TaskInProgress)
    5. fetch_user (user_id=1)
    6. fetch_user (user_id=1) - demonstrates multiple calls
    7. update_user (user from fetch_user output)

    What to Observe:
    ----------------
    - Worker logs showing AsyncTaskRunner vs TaskRunner creation
    - Long-running task showing 5 polls with TaskInProgress
    - Metrics at http://localhost:8000/metrics
    - Workflow execution in UI (URL printed at startup)

    Key Concepts:
    ------------
    - Multiprocessing: One process per worker
    - Auto-detection: def → TaskRunner, async def → AsyncTaskRunner
    - Dynamic batch polling: Batch size = thread_count - currently_running
    - Manual lease extension: Return TaskInProgress to extend lease
    - Event-driven metrics: Prometheus metrics via event listeners
    """
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )

        # Run the main workflow
        main()

    except KeyboardInterrupt:
        # User pressed Ctrl+C - exit gracefully
        pass
