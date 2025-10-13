# Task Options Decorator Examples

The `@task_options` decorator provides a declarative way to configure task execution parameters directly on your worker functions.

## Quick Start

```python
from conductor.client.worker.worker_task import worker_task
from conductor.shared.worker.task_options import task_options

@task_options(
    timeout_seconds=3600,
    response_timeout_seconds=120,
    retry_count=3,
    retry_logic="EXPONENTIAL_BACKOFF"
)
@worker_task(task_definition_name="my_task")
def my_task(task):
    return {"result": "success"}
```

## Available Parameters

### Timeout Settings

| Parameter                  | Type | Description                                                |
| -------------------------- | ---- | ---------------------------------------------------------- |
| `timeout_seconds`          | int  | Maximum time (in seconds) for task execution               |
| `response_timeout_seconds` | int  | Time to wait for task response (must be < timeout_seconds) |
| `poll_timeout_seconds`     | int  | Timeout for polling the task                               |

**Important**: `response_timeout_seconds` must be less than `timeout_seconds`

### Retry Configuration

| Parameter              | Type | Values                                           | Description                        |
| ---------------------- | ---- | ------------------------------------------------ | ---------------------------------- |
| `retry_count`          | int  | ≥ 0                                              | Number of retry attempts           |
| `retry_logic`          | str  | `FIXED`, `LINEAR_BACKOFF`, `EXPONENTIAL_BACKOFF` | Retry strategy                     |
| `retry_delay_seconds`  | int  | ≥ 0                                              | Initial delay between retries      |
| `backoff_scale_factor` | int  | ≥ 1                                              | Multiplier for exponential backoff |

### Rate Limiting

| Parameter                         | Type | Description                    |
| --------------------------------- | ---- | ------------------------------ |
| `rate_limit_per_frequency`        | int  | Max executions per time window |
| `rate_limit_frequency_in_seconds` | int  | Time window for rate limiting  |
| `concurrent_exec_limit`           | int  | Max concurrent executions      |

### Other Options

| Parameter        | Type | Values                               | Description       |
| ---------------- | ---- | ------------------------------------ | ----------------- |
| `timeout_policy` | str  | `TIME_OUT_WF`, `ALERT_ONLY`, `RETRY` | Action on timeout |
| `owner_email`    | str  | -                                    | Task owner email  |
| `description`    | str  | -                                    | Task description  |

## Examples

### 1. Simple Task with Retry

```python
@task_options(
    timeout_seconds=3600,
    response_timeout_seconds=120,
    retry_count=3,
    retry_logic="FIXED",
    retry_delay_seconds=5
)
@worker_task(task_definition_name="simple_task")
def simple_task(task):
    return {"status": "completed"}
```

### 2. High Throughput Task with Rate Limiting

```python
@task_options(
    timeout_seconds=3600,
    response_timeout_seconds=60,
    concurrent_exec_limit=100,
    rate_limit_per_frequency=1000,
    rate_limit_frequency_in_seconds=60,
    description="High throughput task with rate limiting"
)
@worker_task(task_definition_name="bulk_process")
def bulk_process(task):
    items = task.input_data.get("items", [])
    return {"processed": len(items)}
```

### 3. Aggressive Retry with Exponential Backoff

```python
@task_options(
    timeout_seconds=7200,
    response_timeout_seconds=300,
    retry_count=10,
    retry_logic="EXPONENTIAL_BACKOFF",
    retry_delay_seconds=5,
    backoff_scale_factor=3,
    timeout_policy="RETRY"
)
@worker_task(task_definition_name="critical_task")
def critical_task(task):
    # Critical operation that needs aggressive retry
    return {"status": "completed"}
```

### 4. Alert Only on Timeout

```python
@task_options(
    timeout_seconds=600,
    response_timeout_seconds=60,
    timeout_policy="ALERT_ONLY",
    description="Non-critical task"
)
@worker_task(task_definition_name="monitoring_task")
def monitoring_task(task):
    # This will alert but not fail the workflow on timeout
    return {"metrics": {...}}
```

## Retry Logic Comparison

### FIXED

- Same delay between each retry
- Example: 5s → 5s → 5s

### LINEAR_BACKOFF

- Linearly increasing delay
- Example: 5s → 10s → 15s

### EXPONENTIAL_BACKOFF

- Exponentially increasing delay (uses `backoff_scale_factor`)
- Example with scale factor 2: 5s → 10s → 20s → 40s

## Timeout Policy Comparison

### TIME_OUT_WF

- Timeout causes the entire workflow to fail
- Use for critical tasks

### ALERT_ONLY

- Timeout generates an alert but doesn't fail the workflow
- Use for monitoring/metrics tasks

### RETRY

- Timeout triggers a retry attempt
- Use when temporary issues might resolve

## Running the Examples

### Simple Example

```bash
python examples/task_options_simple.py
```

### Comprehensive Example

```bash
python examples/task_options_example.py
```

## Best Practices

1. **Always set both timeout values**: Set `response_timeout_seconds` < `timeout_seconds` to avoid validation errors

2. **Choose appropriate retry logic**:

   - Use `FIXED` for predictable retry intervals
   - Use `LINEAR_BACKOFF` for gradual backoff
   - Use `EXPONENTIAL_BACKOFF` for aggressive retry with longer delays

3. **Set rate limits for high-volume tasks**: Prevent overwhelming downstream systems

4. **Use concurrent execution limits**: Control resource usage

5. **Add descriptions**: Document task purpose for better maintenance

## Integration with Task Registration

The `@task_options` decorator works seamlessly with task registration. When a task is registered with the metadata service, the options are automatically applied:

```python
from conductor.client.http.models.task_def import TaskDef
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.shared.worker.task_definition_helper import apply_task_options_to_task_def
from conductor.shared.worker.task_options import get_task_options

# Get options from decorated function
task_opts = get_task_options(my_task)

# Create task definition
task_def = TaskDef(name="my_task")

# Apply options
apply_task_options_to_task_def(task_def, task_opts)

# Register
metadata_client = OrkesMetadataClient(config)
metadata_client.register_task_def(task_def)
```
