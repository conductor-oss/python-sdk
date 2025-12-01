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
- ⭐ AUTOMATIC JSON SCHEMA REGISTRATION from complex Python type hints:
  * Multiple parameters (str, int, bool, float)
  * Nested dataclasses (Address, ContactInfo, OrderRequest)
  * Lists of dataclasses (List[OrderItem])
  * Optional fields (Optional[str], default values)
  * Generates JSON Schema draft-07 automatically
  * Registers schemas as {task_name}_input and {task_name}_output

Usage:
    export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
    python3 examples/workers_e2e.py

Or with Orkes Cloud:
    export CONDUCTOR_SERVER_URL="https://developer.orkescloud.com/api"
    export CONDUCTOR_AUTH_KEY="your-key"
    export CONDUCTOR_AUTH_SECRET="your-secret"
    python3 examples/workers_e2e.py

Expected Output:
    ================================================================================
    Registering task definition: process_complex_order
    ================================================================================
    Generating JSON schemas from function signature...
      ✓ Generated schemas: input=Yes, output=Yes
    Registering JSON schemas...
      ✓ Registered input schema: process_complex_order_input (v1)
      ✓ Registered output schema: process_complex_order_output (v1)
    Creating task definition for 'process_complex_order'...
    ✓ Registered task definition: process_complex_order
      View at: http://localhost:5000/taskDef/process_complex_order
      With 2 JSON schema(s): process_complex_order_input, process_complex_order_output
"""

import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Union, Optional, List

# Add parent directory to path so we can import conductor modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.context import get_task_context, TaskInProgress
from conductor.client.worker.worker_task import worker_task
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.task_def import TaskDef
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
    poll_timeout=10,
    register_task_def=True
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


# ============================================================================
# COMPLEX SCHEMA EXAMPLE - Demonstrates JSON Schema Generation
# ============================================================================

@dataclass
class Address:
    """Address information - demonstrates nested dataclass."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"  # Default value - makes this field optional in schema


@dataclass
class ContactInfo:
    """Contact information - demonstrates optional fields."""
    email: str
    phone: Optional[str] = None      # Optional - nullable in schema
    mobile: Optional[str] = None     # Optional - nullable in schema


@dataclass
class OrderItem:
    """Order item - demonstrates dataclass within List."""
    sku: str
    quantity: int
    price: float


@dataclass
class OrderRequest:
    """
    Complex order request - demonstrates:
    - Nested dataclasses (Address, ContactInfo)
    - Lists of primitives (tags)
    - Lists of dataclasses (items)
    - Optional fields at multiple levels
    """
    order_id: str
    customer_name: str
    shipping_address: Address        # Nested dataclass
    billing_address: Address         # Nested dataclass
    contact: ContactInfo             # Nested dataclass with optional fields
    items: List[OrderItem]           # List of dataclasses
    tags: List[str]                  # List of primitives
    priority: int = 1                # Default value - optional in schema
    requires_signature: bool = False # Default value - optional in schema


# Create TaskDef with advanced configuration for the complex order worker
complex_order_task_def = TaskDef(
    name='process_complex_order',  # Will be overridden by task_definition_name
    description='Process customer orders with complex validation and retry logic',
    retry_count=3,                          # Retry up to 3 times on failure
    retry_logic='EXPONENTIAL_BACKOFF',      # Use exponential backoff between retries
    retry_delay_seconds=10,                 # Start with 10 second delay
    backoff_scale_factor=3,                 # Double delay each retry (10s, 20s, 40s)
    timeout_seconds=600,                    # Task must complete within 10 minutes
    response_timeout_seconds=120,           # Each execution attempt has 2 minutes
    timeout_policy='RETRY',                 # Retry on timeout
    concurrent_exec_limit=30,                # Max 5 concurrent executions
    rate_limit_per_frequency=100,           # Max 100 executions
    rate_limit_frequency_in_seconds=60,     # Per 60 seconds
    poll_timeout_seconds=30                 # Long poll timeout for efficiency
)

@worker_task(
    task_definition_name='process_complex_order',
    thread_count=10,
    register_task_def=True,  # Will auto-generate and register JSON schema!
    task_def=complex_order_task_def  # Advanced task configuration
)
async def process_complex_order(
    order: OrderRequest,
    idempotency_key: Optional[str],
    timeout_seconds: int = 300
) -> dict:
    """
    COMPLEX SCHEMA WORKER - Demonstrates automatic JSON Schema generation AND TaskDef configuration

    This worker showcases TWO powerful SDK features:

    1. AUTOMATIC JSON SCHEMA GENERATION from complex Python type hints:
       - 3 top-level parameters (order, idempotency_key, timeout_seconds)
       - OrderRequest dataclass with 9 fields
       - 3 nested dataclasses (Address x2, ContactInfo)
       - List of dataclasses (OrderItem)
       - Optional fields at multiple levels
       - Default values correctly marked as optional
       - Schema registered as: process_complex_order_input (v1)

    2. ADVANCED TASK CONFIGURATION via task_def parameter:
       - Retry policy: 3 retries with EXPONENTIAL_BACKOFF (10s, 20s, 40s)
       - Timeouts: 10 min total, 2 min per execution
       - Rate limiting: Max 100 executions per 60 seconds
       - Concurrency: Max 5 concurrent executions
       - All configured via TaskDef object passed to @worker_task

    Benefits:
    - Input validation in Conductor UI
    - Type-safe workflow design
    - Auto-completion in workflow editor
    - Runtime validation of task inputs
    - Production-ready retry and timeout policies
    - Rate limiting to protect downstream services
    """
    # Simulate order processing
    ctx = get_task_context()
    ctx.add_log(f"Processing order {order.order_id} with {len(order.items)} items")
    ctx.add_log(f"Shipping to: {order.shipping_address.city}, {order.shipping_address.state}")
    ctx.add_log(f"Contact: {order.contact.email}")

    return {
        'order_id': order.order_id,
        'status': 'processed',
        'items_count': len(order.items),
        'customer': order.customer_name,
        'total_price': sum(item.price * item.quantity for item in order.items)
    }


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
       - Auto-registers with JSON schema

    2. process_complex_order (def) - TaskRunner
       - ⭐ COMPLEX SCHEMA DEMO - showcases JSON Schema generation
       - Multiple parameters (order, idempotency_key, timeout_seconds)
       - Nested dataclasses (OrderRequest → Address x2, ContactInfo, OrderItem)
       - List of dataclasses (items: List[OrderItem])
       - Optional fields at multiple levels
       - Auto-generates comprehensive JSON Schema (draft-07)
       - Schema registered as: process_complex_order_input (v1)

    3. long_running_task (def) - TaskRunner
       - Demonstrates manual lease extension with TaskInProgress
       - Takes 5 seconds total (5 polls × 1 second each)
       - thread_count=5 (5 concurrent threads)

    4. greet (def) - TaskRunner
       - Simple sync worker from helloworld package

    5. greet_async (async def) - AsyncTaskRunner
       - Simple async worker from helloworld package

    6. fetch_user (async def) - AsyncTaskRunner
       - HTTP API call using httpx (from user_example package)

    7. update_user (def) - TaskRunner
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
    - JSON Schema registration logs for calculate and process_complex_order
    - Long-running task showing 5 polls with TaskInProgress
    - Metrics at http://localhost:8000/metrics
    - Workflow execution in UI (URL printed at startup)
    - Registered task definitions with schemas in Conductor UI

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
