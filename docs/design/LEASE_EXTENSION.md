# Task Lease Extension in Conductor Python SDK

## Overview

Task lease extension is a mechanism that allows long-running tasks to maintain their ownership and prevent timeouts during execution. When a worker polls a task from Conductor, it receives a "lease" for that task with a specific timeout period. If the task execution exceeds this timeout, Conductor may assume the worker has failed and reassign the task to another worker.

Lease extension prevents this by periodically informing Conductor that the task is still being actively processed.

## How Lease Extension Works

### The Problem

Consider a worker executing a long-running task:

```python
@worker_task(task_definition_name='long_processing_task')
def process_large_dataset(dataset_id: str) -> dict:
    # This takes 10 minutes
    result = expensive_ml_model_training(dataset_id)
    return {'model_id': result.id}
```

If the task's `responseTimeoutSeconds` is set to 300 seconds (5 minutes) but execution takes 10 minutes, Conductor will timeout the task after 5 minutes and potentially reassign it to another worker, causing:
- Duplicate work
- Resource waste
- Inconsistent results

### The Solution: Automatic Lease Extension

The Python SDK automatically extends the task lease when `lease_extend_enabled=True` (the default):

```python
@worker_task(
    task_definition_name='long_processing_task',
    lease_extend_enabled=True  # Default: enabled
)
def process_large_dataset(dataset_id: str) -> dict:
    # SDK automatically extends lease every 80% of responseTimeoutSeconds
    result = expensive_ml_model_training(dataset_id)
    return {'model_id': result.id}
```

## How It Works Internally

### 1. Task Polling with Lease

When a worker polls a task, it receives:
- **Task data**: Input parameters, task ID, workflow ID
- **Lease timeout**: Based on `responseTimeoutSeconds` in task definition
- **Poll count**: Number of times this task has been polled

### 2. Automatic Extension Trigger

The SDK extends the lease automatically when **both** conditions are met:
1. `lease_extend_enabled=True` (worker configuration)
2. Task execution time approaches the response timeout threshold

### 3. Extension Mechanism

The SDK uses the `IN_PROGRESS` status with `extendLease=true`:

```python
# Internally, the SDK does this:
task_result = TaskResult(
    task_id=task.task_id,
    workflow_instance_id=task.workflow_instance_id,
    status=TaskResultStatus.IN_PROGRESS  # Tells Conductor: still working
)
task_result.extend_lease = True  # Request lease extension
task_result.callback_after_seconds = 60  # Re-queue after 60 seconds
```

### 4. Callback Pattern

When lease is extended:
1. Worker returns `IN_PROGRESS` status to Conductor
2. Conductor re-queues the task after `callback_after_seconds`
3. Worker polls the same task again (identified by `poll_count`)
4. Worker continues execution from where it left off

## Usage Patterns

### Pattern 1: Automatic Extension (Recommended)

**Default behavior** - SDK handles everything automatically:

```python
@worker_task(
    task_definition_name='ml_training',
    lease_extend_enabled=True  # Default
)
def train_model(dataset: dict) -> dict:
    # Just write your business logic
    # SDK automatically extends lease if needed
    model = train_neural_network(dataset)
    return {'model_id': model.id, 'accuracy': model.accuracy}
```

**When to use:**
- Long-running tasks (>5 minutes)
- Unpredictable execution time
- Tasks that shouldn't be interrupted

### Pattern 2: Manual Control with TaskInProgress

For fine-grained control, explicitly return `TaskInProgress`:

```python
from conductor.client.context.task_context import TaskInProgress
from typing import Union

@worker_task(task_definition_name='batch_processor')
def process_batch(batch_id: str) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    # Process 100 items per poll
    processed = process_next_100_items(batch_id, offset=poll_count * 100)

    if processed < 100:
        # All done
        return {'status': 'completed', 'total_processed': poll_count * 100 + processed}
    else:
        # More work to do - extend lease
        return TaskInProgress(
            callback_after_seconds=30,  # Re-queue in 30s
            output={'progress': poll_count * 100 + processed}
        )
```

**When to use:**
- Multi-step processing with checkpoints
- Tasks that can report progress
- Need to limit single execution duration

### Pattern 3: Disable Lease Extension

For short, predictable tasks:

```python
@worker_task(
    task_definition_name='quick_validation',
    lease_extend_enabled=False  # Disable automatic extension
)
def validate_data(data: dict) -> dict:
    # Fast validation - always completes in <1 second
    is_valid = data.get('required_field') is not None
    return {'valid': is_valid}
```

**When to use:**
- Fast tasks (<30 seconds)
- Tasks with strict SLA requirements
- Guaranteed completion time

## Configuration

### Code-Level Configuration

```python
@worker_task(
    task_definition_name='my_task',
    lease_extend_enabled=True  # Enable/disable lease extension
)
def my_worker(input_data: dict) -> dict:
    ...
```

### Environment Variable Configuration

Override at runtime:

```bash
# Global default for all workers
export conductor.worker.all.lease_extend_enabled=true

# Worker-specific override
export conductor.worker.my_task.lease_extend_enabled=false
```

### Configuration Priority

Highest to lowest:
1. **Environment variables** (per-worker or global)
2. **Code-level defaults** (in `@worker_task`)

## Task Definition Requirements

Lease extension works in conjunction with task definition settings:

```json
{
  "name": "long_processing_task",
  "responseTimeoutSeconds": 300,  // 5 minutes
  "timeoutSeconds": 3600,         // 1 hour total timeout
  "timeoutPolicy": "RETRY",
  "retryCount": 3
}
```

**Key parameters:**
- **responseTimeoutSeconds**: Worker's lease duration (per execution)
- **timeoutSeconds**: Total workflow timeout (all retries)
- **timeoutPolicy**: What happens on timeout (RETRY, ALERT_ONLY, TIME_OUT_WF)

### Relationship Between Settings

```
timeoutSeconds (1 hour) = total allowed time
    ↓
responseTimeoutSeconds (5 min) = per-execution lease
    ↓
Lease extension = automatically renews the 5-min lease
    ↓
Task can run for up to timeoutSeconds with multiple lease extensions
```

## Best Practices

### 1. Enable for Long-Running Tasks

```python
# Good: Enable for tasks that may take a while
@worker_task(
    task_definition_name='video_encoding',
    lease_extend_enabled=True
)
def encode_video(video_id: str) -> dict:
    # May take 10-30 minutes depending on video size
    return encode_large_video(video_id)
```

### 2. Set Appropriate responseTimeoutSeconds

```json
{
  "name": "video_encoding",
  "responseTimeoutSeconds": 300,  // 5 min lease
  "timeoutSeconds": 3600          // 1 hour max total
}
```

**Rule of thumb:**
- `responseTimeoutSeconds` = Expected execution time / number of expected polls
- `timeoutSeconds` = Maximum acceptable total time (with retries)

### 3. Use TaskInProgress for Checkpointing

```python
@worker_task(task_definition_name='data_migration')
def migrate_data(source: str) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    offset = ctx.get_poll_count() * 1000

    # Migrate 1000 records per iteration
    migrated = migrate_records(source, offset, limit=1000)

    if migrated == 1000:
        # More records to migrate
        return TaskInProgress(
            callback_after_seconds=10,
            output={'migrated': offset + 1000}
        )
    else:
        # Done
        return {'status': 'completed', 'total_migrated': offset + migrated}
```

**Benefits:**
- Fault tolerance (can resume from checkpoint)
- Progress reporting
- Controlled execution duration per poll

### 4. Monitor Poll Count

```python
@worker_task(task_definition_name='retry_aware_task')
def process_with_limit(data: dict) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    # Limit to 10 retries
    if poll_count >= 10:
        raise Exception("Task exceeded maximum retry limit")

    # Normal processing with lease extension
    if not is_complete():
        return TaskInProgress(callback_after_seconds=60)

    return {'status': 'completed'}
```

### 5. Set Appropriate callback_after_seconds

```python
# Fast polling for time-sensitive tasks
return TaskInProgress(callback_after_seconds=10)  # 10s

# Standard polling
return TaskInProgress(callback_after_seconds=60)  # 1 min

# Slow polling for tasks waiting on external systems
return TaskInProgress(callback_after_seconds=300) # 5 min
```

## Common Patterns

### Pattern: Polling External System

```python
@worker_task(task_definition_name='wait_for_approval')
def wait_for_approval(request_id: str) -> Union[dict, TaskInProgress]:
    approval_status = check_approval_system(request_id)

    if approval_status == 'PENDING':
        # Still waiting - extend lease
        return TaskInProgress(
            callback_after_seconds=30,
            output={'status': 'waiting', 'checked_at': datetime.now().isoformat()}
        )
    elif approval_status == 'APPROVED':
        return {'status': 'approved', 'approved_at': datetime.now().isoformat()}
    else:
        raise Exception(f"Request rejected: {approval_status}")
```

### Pattern: Batch Processing with Progress

```python
@worker_task(task_definition_name='bulk_email_sender')
def send_bulk_emails(campaign_id: str) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    batch_number = ctx.get_poll_count()
    batch_size = 100

    # Get emails for this batch
    emails = get_emails(campaign_id, offset=batch_number * batch_size, limit=batch_size)

    # Send emails
    sent = send_emails(emails)
    total_sent = batch_number * batch_size + sent

    if len(emails) == batch_size:
        # More batches to process
        ctx.add_log(f"Sent batch {batch_number}: {sent} emails")
        return TaskInProgress(
            callback_after_seconds=5,
            output={'sent': total_sent, 'batch': batch_number}
        )
    else:
        # Last batch completed
        return {'status': 'completed', 'total_sent': total_sent}
```

### Pattern: Long Computation with Heartbeat

```python
@worker_task(task_definition_name='ml_model_training')
async def train_model(config: dict) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    epoch = ctx.get_poll_count()
    total_epochs = config['epochs']

    if epoch >= total_epochs:
        # Training complete
        model = load_checkpoint('final_model')
        return {'model_id': model.id, 'accuracy': model.accuracy}

    # Train one epoch
    ctx.add_log(f"Training epoch {epoch}/{total_epochs}")
    metrics = await train_one_epoch(config, epoch)
    save_checkpoint(epoch, metrics)

    # Continue to next epoch
    return TaskInProgress(
        callback_after_seconds=30,
        output={
            'epoch': epoch,
            'loss': metrics['loss'],
            'accuracy': metrics['accuracy']
        }
    )
```

## Troubleshooting

### Issue: Task Times Out Despite Lease Extension

**Symptoms:**
- Task marked as timed out after `responseTimeoutSeconds`
- Worker still processing when timeout occurs

**Possible causes:**
1. `lease_extend_enabled=False`
2. Worker not returning `TaskInProgress` or setting `callback_after_seconds`
3. `timeoutSeconds` (total timeout) exceeded

**Solution:**
```python
# Verify lease extension is enabled
@worker_task(
    task_definition_name='my_task',
    lease_extend_enabled=True  # Must be True
)
def my_task(data: dict) -> dict:
    ...

# Or check environment variable
# conductor.worker.my_task.lease_extend_enabled=true
```

### Issue: Task Polls Too Frequently

**Symptoms:**
- High API call rate
- Excessive logging from repeated polls

**Solution:**
```python
# Increase callback_after_seconds
return TaskInProgress(
    callback_after_seconds=300,  # 5 minutes instead of 60s
    output={'status': 'processing'}
)
```

### Issue: Task Never Completes

**Symptoms:**
- Task polls indefinitely
- Always returns `IN_PROGRESS`

**Solution:**
```python
# Add completion condition
@worker_task(task_definition_name='my_task')
def my_task(data: dict) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    # Add safety limit
    if poll_count > 100:
        raise Exception("Task exceeded maximum iterations")

    if is_complete():
        return {'status': 'completed'}
    else:
        return TaskInProgress(callback_after_seconds=60)
```

## Performance Considerations

### Memory Usage

Each `IN_PROGRESS` response with lease extension causes:
- Task re-queue in Conductor
- New poll from worker
- Maintained task state

**Recommendation:** Use reasonable `callback_after_seconds` values (30-300s).

### API Call Volume

Frequent lease extensions increase API calls:

```
Total API calls = (execution_time / callback_after_seconds) * 2
                  (one poll + one update per iteration)
```

**Example:**
- Execution time: 1 hour (3600s)
- callback_after_seconds: 60s
- API calls: (3600 / 60) * 2 = 120 calls

**Optimization:** Use longer `callback_after_seconds` for less time-sensitive tasks.

## Summary

**Key Points:**
- ✅ Lease extension prevents long-running tasks from timing out
- ✅ Enabled by default (`lease_extend_enabled=True`)
- ✅ Works automatically for most use cases
- ✅ Use `TaskInProgress` for fine-grained control
- ✅ Configure `responseTimeoutSeconds` and `timeoutSeconds` appropriately
- ✅ Monitor `poll_count` to prevent infinite loops
- ✅ Balance `callback_after_seconds` between responsiveness and API call volume

**Quick Reference:**

| Use Case | Configuration | Pattern |
|----------|--------------|---------|
| Fast task (<30s) | `lease_extend_enabled=False` | Simple return |
| Medium task (1-5 min) | `lease_extend_enabled=True` | Automatic extension |
| Long task (>5 min) | `lease_extend_enabled=True` | Automatic extension |
| Checkpointed processing | `lease_extend_enabled=True` | Return `TaskInProgress` |
| External system polling | `lease_extend_enabled=True` | Return `TaskInProgress` |

For more information, see:
- [Worker Documentation](docs/worker/README.md)
- [Task Context](examples/task_context_example.py)
- [Worker Configuration](WORKER_CONFIGURATION.md)
