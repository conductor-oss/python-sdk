# Task Management API Reference

Complete API reference for task management operations in Conductor Python SDK.

> 📚 **Complete Working Example**: See [task_workers.py](../examples/task_workers.py) for comprehensive task worker implementations.

## Quick Start

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus

# Initialize client
configuration = Configuration(
    server_api_url="http://localhost:8080/api",
    debug=False,
    authentication_settings=AuthenticationSettings(
        key_id="your_key_id",
        key_secret="your_key_secret"
    )
)

task_client = OrkesTaskClient(configuration)

# Poll for tasks
task = task_client.poll_task("SIMPLE_TASK", worker_id="worker1", domain="test")
if task:
    try:
        # Process the task
        output = {"result": "Task processed successfully"}

        # Update task with result
        task_result = TaskResult(
            workflow_instance_id=task.workflow_instance_id,
            task_id=task.task_id,
            status=TaskResultStatus.COMPLETED,
            output_data=output
        )
        task_client.update_task(task_result)
    except Exception as e:
        # Handle failure
        task_result = TaskResult(
            workflow_instance_id=task.workflow_instance_id,
            task_id=task.task_id,
            status=TaskResultStatus.FAILED,
            reason_for_incompletion=str(e)
        )
        task_client.update_task(task_result)
```

## Quick Links

- [Task Polling APIs](#task-polling-apis)
- [Task Management APIs](#task-management-apis)
- [Task Queue APIs](#task-queue-apis)
- [Task Log APIs](#task-log-apis)
- [Task Search APIs](#task-search-apis)
- [Task Signal APIs](#task-signal-apis)
- [API Details](#api-details)
- [Model Reference](#model-reference)
- [Error Handling](#error-handling)

## Task Polling APIs

APIs for polling tasks from task queues for execution by workers.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `poll_task()` | `GET /tasks/poll/{tasktype}` | Poll a single task by type | [Example](#poll-task) |
| `batch_poll_tasks()` | `GET /tasks/poll/batch/{tasktype}` | Batch poll multiple tasks | [Example](#batch-poll-tasks) |

## Task Management APIs

Core operations for managing task execution and state.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `get_task()` | `GET /tasks/{taskId}` | Get task details by ID | [Example](#get-task) |
| `update_task()` | `POST /tasks` | Update task with result | [Example](#update-task) |
| `update_task_by_ref_name()` | `POST /tasks/{workflowId}/{taskRefName}/{status}` | Update task by reference name | [Example](#update-task-by-ref-name) |
| `update_task_sync()` | `POST /tasks/{workflowId}/{taskRefName}/{status}/sync` | Update task synchronously | [Example](#update-task-sync) |

## Task Queue APIs

APIs for managing and monitoring task queues.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `get_queue_size_for_task()` | `GET /tasks/queue/sizes` | Get queue size for task type | [Example](#get-queue-size) |
| `get_task_poll_data()` | `GET /tasks/queue/polldata` | Get poll data for task type | [Example](#get-poll-data) |

## Task Log APIs

Operations for managing task execution logs.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `add_task_log()` | `POST /tasks/{taskId}/log` | Add log message to task | [Example](#add-task-log) |
| `get_task_logs()` | `GET /tasks/{taskId}/log` | Get all logs for task | [Example](#get-task-logs) |

## Task Search APIs

Search and query task execution data.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| Search Tasks | `GET /tasks/search` | Search tasks with filters | See [Workflow API](./WORKFLOW.md#search-workflows) |
| Search Tasks V2 | `GET /tasks/search-v2` | Enhanced task search | See [Workflow API](./WORKFLOW.md#search-workflows-v2) |

## Task Signal APIs

APIs for signaling tasks with external events.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| Signal Task Async | `POST /tasks/{workflowId}/{taskRefName}/signal` | Signal task asynchronously | See Advanced Usage |
| Signal Task Sync | `POST /tasks/{workflowId}/{taskRefName}/signal/sync` | Signal task synchronously | See Advanced Usage |

---

## API Details

### Task Polling

#### Poll Task

Poll a single task from the queue for execution.

```python
# Basic polling
task = task_client.poll_task("SIMPLE_TASK")

# Poll with worker ID (recommended for tracking)
task = task_client.poll_task(
    task_type="SIMPLE_TASK",
    worker_id="worker-1"
)

# Poll from specific domain
task = task_client.poll_task(
    task_type="SIMPLE_TASK",
    worker_id="worker-1",
    domain="payments"
)

if task:
    print(f"Received task: {task.task_id}")
    print(f"Input data: {task.input_data}")
```

**Parameters:**
- `task_type` (str, required): Type of task to poll
- `worker_id` (str, optional): Unique worker identifier
- `domain` (str, optional): Task domain for routing

**Returns:** `Task` object or None if no tasks available

#### Batch Poll Tasks

Poll multiple tasks at once for efficient processing.

```python
# Poll up to 10 tasks with 100ms timeout
tasks = task_client.batch_poll_tasks(
    task_type="BATCH_PROCESS",
    worker_id="batch-worker-1",
    count=10,
    timeout_in_millisecond=100
)

for task in tasks:
    print(f"Processing task: {task.task_id}")
    # Process tasks in parallel or sequentially
```

**Parameters:**
- `task_type` (str, required): Type of tasks to poll
- `worker_id` (str, optional): Worker identifier
- `count` (int, optional): Number of tasks to poll (default: 1)
- `timeout_in_millisecond` (int, optional): Long poll timeout
- `domain` (str, optional): Task domain

**Returns:** List of `Task` objects

---

### Task Management

#### Get Task

Retrieve detailed information about a specific task.

```python
task = task_client.get_task("550e8400-e29b-41d4-a716-446655440000")

print(f"Task ID: {task.task_id}")
print(f"Task Type: {task.task_def_name}")
print(f"Status: {task.status}")
print(f"Workflow ID: {task.workflow_instance_id}")
print(f"Retry Count: {task.retry_count}")
print(f"Poll Count: {task.poll_count}")
```

**Returns:** `Task` object with full details

#### Update Task

Update a task with execution result using TaskResult object.

```python
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus

# Success case
task_result = TaskResult(
    workflow_instance_id=task.workflow_instance_id,
    task_id=task.task_id,
    status=TaskResultStatus.COMPLETED,
    output_data={
        "processed": True,
        "items_count": 42,
        "timestamp": "2024-01-15T10:30:00Z"
    }
)

response = task_client.update_task(task_result)
print(f"Task updated: {response}")

# Failure case with reason
task_result = TaskResult(
    workflow_instance_id=task.workflow_instance_id,
    task_id=task.task_id,
    status=TaskResultStatus.FAILED,
    reason_for_incompletion="Database connection failed",
    output_data={"error_code": "DB_CONN_ERR"}
)

task_client.update_task(task_result)

# In Progress update with logs
task_result = TaskResult(
    workflow_instance_id=task.workflow_instance_id,
    task_id=task.task_id,
    status=TaskResultStatus.IN_PROGRESS,
    output_data={"progress": 50},
    logs=["Processing batch 1 of 2", "50% complete"]
)

task_client.update_task(task_result)
```

**TaskResult Status Options:**
- `COMPLETED`: Task completed successfully
- `FAILED`: Task failed (will retry based on retry policy)
- `FAILED_WITH_TERMINAL_ERROR`: Task failed, no retries
- `IN_PROGRESS`: Task still processing

#### Update Task By Ref Name

Update a task using workflow ID and task reference name.

```python
# Update task by reference name
response = task_client.update_task_by_ref_name(
    workflow_id="550e8400-e29b-41d4-a716-446655440000",
    task_ref_name="process_payment",
    status="COMPLETED",
    output={
        "payment_id": "PAY-12345",
        "status": "success",
        "amount": 99.99
    },
    worker_id="payment-worker-1"
)

print(f"Task updated: {response}")
```

**Parameters:**
- `workflow_id` (str, required): Workflow instance ID
- `task_ref_name` (str, required): Task reference name from workflow
- `status` (str, required): Task completion status
- `output` (object, required): Task output data
- `worker_id` (str, optional): Worker identifier

#### Update Task Sync

Update task synchronously and get the updated workflow state.

```python
# Update and get workflow state
workflow = task_client.update_task_sync(
    workflow_id="550e8400-e29b-41d4-a716-446655440000",
    task_ref_name="validate_order",
    status="COMPLETED",
    output={
        "valid": True,
        "total": 199.99
    },
    worker_id="validator-1"
)

print(f"Workflow status: {workflow.status}")
print(f"Next tasks: {[t.task_def_name for t in workflow.tasks if t.status == 'IN_PROGRESS']}")
```

**Returns:** `Workflow` object with current state

---

### Task Queue Management

#### Get Queue Size

Get the current queue size for a task type.

```python
# Check queue depth
queue_size = task_client.get_queue_size_for_task("PROCESS_ORDER")
print(f"Queue size for PROCESS_ORDER: {queue_size}")

# Monitor queue sizes
task_types = ["PROCESS_ORDER", "SEND_EMAIL", "GENERATE_REPORT"]
for task_type in task_types:
    size = task_client.get_queue_size_for_task(task_type)
    if size > 100:
        print(f"WARNING: High queue depth for {task_type}: {size}")
```

**Returns:** Integer queue size

#### Get Poll Data

Get polling statistics for a task type.

```python
# Get poll data for monitoring
poll_data_list = task_client.get_task_poll_data("PROCESS_ORDER")

for poll_data in poll_data_list:
    print(f"Queue: {poll_data.queue_name}")
    print(f"Domain: {poll_data.domain}")
    print(f"Worker ID: {poll_data.worker_id}")
    print(f"Last Poll Time: {poll_data.last_poll_time}")
```

**Returns:** List of `PollData` objects

---

### Task Logging

#### Add Task Log

Add log messages to a running task for debugging and monitoring.

```python
# Add single log message
task_client.add_task_log(
    task_id="550e8400-e29b-41d4-a716-446655440000",
    log_message="Starting data validation"
)

# Add progress logs
for i in range(10):
    task_client.add_task_log(
        task_id=task.task_id,
        log_message=f"Processing batch {i+1}/10 - {(i+1)*10}% complete"
    )
    # Do actual processing...

# Add error logs
try:
    # Some operation
    pass
except Exception as e:
    task_client.add_task_log(
        task_id=task.task_id,
        log_message=f"ERROR: {str(e)}"
    )
```

#### Get Task Logs

Retrieve all log messages for a task.

```python
# Get all logs for a task
logs = task_client.get_task_logs("550e8400-e29b-41d4-a716-446655440000")

for log in logs:
    print(f"[{log.created_time}] {log.log}")

# Check for errors in logs
error_logs = [log for log in logs if "ERROR" in log.log]
if error_logs:
    print(f"Found {len(error_logs)} error messages")
```

**Returns:** List of `TaskExecLog` objects

---

## Model Reference

### Core Models

#### Task

The main task object returned from polling.

```python
class Task:
    task_id: str                           # Unique task identifier
    task_def_name: str                     # Task type/definition name
    reference_task_name: str               # Reference name in workflow
    workflow_instance_id: str              # Parent workflow ID
    workflow_type: str                     # Workflow type name
    correlation_id: Optional[str]          # Correlation identifier
    scheduled_time: int                    # When task was scheduled
    start_time: int                        # When task started
    end_time: Optional[int]                # When task completed
    update_time: int                       # Last update time
    status: str                            # Current status
    input_data: dict                       # Task input parameters
    output_data: Optional[dict]            # Task output (if completed)
    reason_for_incompletion: Optional[str] # Failure reason
    retry_count: int                       # Number of retries
    poll_count: int                        # Number of polls
    task_def: Optional[TaskDef]            # Task definition
    domain: Optional[str]                  # Task domain
    rate_limit_per_frequency: int          # Rate limit setting
    rate_limit_frequency_in_seconds: int   # Rate limit window
    worker_id: Optional[str]               # Last worker ID
```

#### TaskResult

Result object for updating task status.

```python
class TaskResult:
    workflow_instance_id: str               # Workflow ID
    task_id: str                           # Task ID
    status: TaskResultStatus               # Completion status
    output_data: Optional[dict]            # Output data
    reason_for_incompletion: Optional[str] # Failure reason
    logs: Optional[List[str]]              # Log messages
    external_output_payload_storage_path: Optional[str] # External storage

    # Helper methods
    def add_output_data(key: str, value: Any)  # Add output field
    def add_log(message: str)                  # Add log message
```

#### TaskResultStatus

Enumeration of possible task completion statuses.

```python
class TaskResultStatus(Enum):
    COMPLETED = "COMPLETED"                           # Success
    FAILED = "FAILED"                                # Failure (will retry)
    FAILED_WITH_TERMINAL_ERROR = "FAILED_WITH_TERMINAL_ERROR"  # No retry
    IN_PROGRESS = "IN_PROGRESS"                      # Still running
```

#### PollData

Poll statistics for task queues.

```python
class PollData:
    queue_name: str                # Queue name
    domain: str                    # Task domain
    worker_id: str                 # Worker identifier
    last_poll_time: int           # Last poll timestamp
    queue_depth: int              # Current queue size
```

#### TaskExecLog

Task execution log entry.

```python
class TaskExecLog:
    log: str                      # Log message
    task_id: str                  # Task ID
    created_time: int             # Timestamp (epoch millis)
```

---

## Worker Implementation Examples

### Simple Worker

Basic worker that polls and processes tasks.

```python
import time
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='process_data')
def process_data(input_data: dict) -> dict:
    """Simple worker that processes data"""
    item_count = input_data.get('item_count', 0)

    # Process items
    processed_items = []
    for i in range(item_count):
        processed_items.append(f"item_{i}_processed")

    return {
        "status": "success",
        "processed_count": len(processed_items),
        "items": processed_items
    }
```

### Advanced Worker with Error Handling

Worker with comprehensive error handling and retry logic.

```python
from conductor.client.http.models import Task, TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.exception import NonRetryableException
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='critical_process')
def critical_process(task: Task) -> TaskResult:
    """
    Advanced worker with full control over task result
    """
    task_result = task.to_task_result(TaskResultStatus.IN_PROGRESS)

    try:
        # Add progress logs
        task_result.add_log("Starting critical process")

        # Get input data
        data = task.input_data
        retry_count = task.retry_count

        # Check retry limit
        if retry_count > 3:
            # Terminal failure after too many retries
            task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
            task_result.reason_for_incompletion = "Max retries exceeded"
            return task_result

        # Simulate processing
        if data.get('force_failure'):
            # Retryable failure
            raise Exception("Temporary failure - will retry")

        if data.get('terminal_failure'):
            # Non-retryable failure
            raise NonRetryableException("Critical error - cannot retry")

        # Success case
        task_result.status = TaskResultStatus.COMPLETED
        task_result.add_output_data('processed', True)
        task_result.add_output_data('timestamp', time.time())
        task_result.add_log("Process completed successfully")

    except NonRetryableException as e:
        # Terminal failure
        task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
        task_result.reason_for_incompletion = str(e)
        task_result.add_log(f"Terminal failure: {e}")

    except Exception as e:
        # Retryable failure
        task_result.status = TaskResultStatus.FAILED
        task_result.reason_for_incompletion = str(e)
        task_result.add_log(f"Error (will retry): {e}")

    return task_result
```

### Manual Polling Worker

Worker that manually polls and updates tasks.

```python
import time
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus

def run_manual_worker(task_client: OrkesTaskClient):
    """
    Manual polling worker without decorators
    """
    task_type = "MANUAL_TASK"
    worker_id = "manual-worker-1"

    while True:
        # Poll for task
        task = task_client.poll_task(task_type, worker_id=worker_id)

        if not task:
            time.sleep(1)  # No task available, wait
            continue

        print(f"Received task: {task.task_id}")

        try:
            # Add log
            task_client.add_task_log(task.task_id, "Starting processing")

            # Process task
            result = process_task_logic(task.input_data)

            # Update with success
            task_result = TaskResult(
                workflow_instance_id=task.workflow_instance_id,
                task_id=task.task_id,
                status=TaskResultStatus.COMPLETED,
                output_data=result
            )

            task_client.update_task(task_result)
            print(f"Task {task.task_id} completed")

        except Exception as e:
            # Update with failure
            task_result = TaskResult(
                workflow_instance_id=task.workflow_instance_id,
                task_id=task.task_id,
                status=TaskResultStatus.FAILED,
                reason_for_incompletion=str(e)
            )

            task_client.update_task(task_result)
            print(f"Task {task.task_id} failed: {e}")

def process_task_logic(input_data: dict) -> dict:
    """Business logic for task processing"""
    # Your processing logic here
    return {"result": "processed"}
```

---

## Error Handling

### Common Errors

```python
from conductor.client.worker.exception import NonRetryableException

# Polling errors
try:
    task = task_client.poll_task("INVALID_TYPE")
except Exception as e:
    if "404" in str(e):
        print("Task type not registered")
    else:
        print(f"Polling error: {e}")

# Update errors
try:
    task_client.update_task(task_result)
except Exception as e:
    if "400" in str(e):
        print("Invalid task result")
    elif "404" in str(e):
        print("Task or workflow not found")
    else:
        print(f"Update error: {e}")

# Worker error patterns
@worker_task(task_definition_name='robust_worker')
def robust_worker(data: dict) -> dict:
    try:
        # Validation
        if not data.get('required_field'):
            raise NonRetryableException("Missing required field")

        # Temporary failures (will retry)
        if external_service_down():
            raise Exception("Service temporarily unavailable")

        # Process
        return {"status": "success"}

    except NonRetryableException:
        # Don't catch - let it propagate for terminal failure
        raise
    except Exception as e:
        # Log and re-raise for retry
        print(f"Retryable error: {e}")
        raise
```

### Retry Strategies

```python
# Configure retry policy in task definition
task_def = {
    "name": "retry_task",
    "retryCount": 3,
    "retryLogic": "EXPONENTIAL_BACKOFF",
    "retryDelaySeconds": 60,
    "timeoutSeconds": 3600,
    "responseTimeoutSeconds": 600
}

# Handle retries in worker
@worker_task(task_definition_name='retry_task')
def retry_aware_worker(task: Task) -> dict:
    retry_count = task.retry_count

    if retry_count == 0:
        print("First attempt")
    else:
        print(f"Retry attempt {retry_count}")
        # Maybe use different strategy on retry

    # Fail fast on too many retries
    if retry_count >= 3:
        raise NonRetryableException("Max retries exceeded")

    return {"attempt": retry_count + 1}
```

---

## Best Practices

### 1. Worker Design

```python
# ✅ Good: Idempotent worker
@worker_task(task_definition_name='idempotent_task')
def idempotent_worker(order_id: str) -> dict:
    # Check if already processed
    if is_already_processed(order_id):
        return get_existing_result(order_id)

    # Process and store result
    result = process_order(order_id)
    store_result(order_id, result)
    return result

# ❌ Bad: Non-idempotent worker
@worker_task(task_definition_name='bad_task')
def non_idempotent_worker(amount: float) -> dict:
    # This could charge multiple times on retry!
    charge_credit_card(amount)
    return {"charged": amount}
```

### 2. Error Handling

```python
# ✅ Good: Proper error classification
@worker_task(task_definition_name='error_aware_task')
def error_aware_worker(data: dict) -> dict:
    try:
        # Validation errors are terminal
        validate_input(data)  # Raises NonRetryableException

        # Process with retryable errors
        result = process_with_external_service(data)
        return result

    except ValidationError as e:
        # Terminal - bad input won't get better
        raise NonRetryableException(str(e))
    except NetworkError as e:
        # Transient - might work on retry
        raise Exception(str(e))
```

### 3. Logging and Monitoring

```python
# ✅ Good: Comprehensive logging
@worker_task(task_definition_name='logged_task')
def logged_worker(task: Task) -> TaskResult:
    result = task.to_task_result(TaskResultStatus.IN_PROGRESS)

    # Add structured logs
    result.add_log(f"Starting processing for workflow {task.workflow_instance_id}")
    result.add_log(f"Input data: {task.input_data}")

    try:
        # Process with progress updates
        for step in range(5):
            result.add_log(f"Step {step+1}/5 completed")
            # Process step...

        result.status = TaskResultStatus.COMPLETED
        result.add_output_data("steps_completed", 5)

    except Exception as e:
        result.add_log(f"ERROR: {e}")
        result.status = TaskResultStatus.FAILED
        result.reason_for_incompletion = str(e)

    return result
```

### 4. Performance Optimization

```python
# ✅ Good: Batch processing
tasks = task_client.batch_poll_tasks(
    task_type="BATCH_TASK",
    count=10,
    timeout_in_millisecond=100
)

# Process in parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(process_task, tasks)

# ✅ Good: Connection pooling
class WorkerWithPool:
    def __init__(self):
        self.connection_pool = create_connection_pool()

    @worker_task(task_definition_name='pooled_task')
    def process_with_pool(self, data: dict) -> dict:
        conn = self.connection_pool.get_connection()
        try:
            return process_with_connection(conn, data)
        finally:
            self.connection_pool.release(conn)
```

---

## Advanced Usage

### External Storage for Large Payloads

```python
# Store large outputs externally
@worker_task(task_definition_name='large_output_task')
def large_output_worker(task: Task) -> TaskResult:
    result = task.to_task_result(TaskResultStatus.COMPLETED)

    # Generate large output
    large_data = generate_large_dataset()

    # Store externally and reference
    storage_path = upload_to_s3(large_data)
    result.external_output_payload_storage_path = storage_path

    # Add summary in output
    result.add_output_data("summary", {"rows": len(large_data), "path": storage_path})

    return result
```

### Domain-Based Task Routing

```python
# Route tasks to specific worker groups
domains = ["payments", "inventory", "shipping"]

for domain in domains:
    task = task_client.poll_task(
        task_type="PROCESS_ORDER",
        domain=domain,
        worker_id=f"worker-{domain}"
    )

    if task:
        # Process based on domain
        process_domain_specific(task, domain)
```

---

## Complete Working Example

For a comprehensive example covering task workers with various patterns, see [task_workers.py](../examples/task_workers.py).

```python
# Quick example
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.configuration.configuration import Configuration

config = Configuration(server_api_url="http://localhost:8080/api")
task_client = OrkesTaskClient(config)

# Poll, process, and update tasks
# Full implementation in examples/task_workers.py
```

---

## See Also

- [Workflow Management](./WORKFLOW.md) - Creating workflows that generate tasks
- [Worker Documentation](./WORKER.md) - Worker implementation patterns
- [Metadata Management](./METADATA.md) - Task definition management
- [Examples](../examples/) - Complete working examples