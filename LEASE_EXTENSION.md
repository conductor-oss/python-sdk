# Lease Extension (Automatic Heartbeat)

When a worker picks up a task, the Conductor server starts a `responseTimeoutSeconds` timer. If the worker doesn't send an update before the timer expires, the server marks the task as timed out and re-queues it for retry.

For long-running tasks (agent tool calls, LLM inference, data processing, batch jobs), the worker is actively executing but the server thinks it's dead. **Lease extension** solves this by automatically sending heartbeats that reset the timeout timer.

## How It Works

When `lease_extend_enabled=True`:

1. Worker picks up a task with `responseTimeoutSeconds > 0`
2. SDK starts tracking the task for heartbeats
3. At **80% of `responseTimeoutSeconds`**, SDK sends a heartbeat (`TaskResult.extend_lease=True`)
4. Server resets the task's `updateTime` to now, giving a fresh `responseTimeoutSeconds` window
5. Heartbeats continue until the task completes, fails, or the worker shuts down

```
Timeline (responseTimeoutSeconds=120s):
  0s          96s         192s        288s
  |-----------|-----------|-----------|--→ task completes
  poll      heartbeat   heartbeat   heartbeat
             (80%)       (80%)       (80%)
```

The heartbeat fires at 80% of `responseTimeoutSeconds` (matching the Java SDK). This gives a 20% safety margin — if a heartbeat is slightly delayed, the task still has time before the server times it out.

## Quick Start

```python
from conductor.client.worker.worker_task import worker_task

@worker_task(
    task_definition_name='long_running_analysis',
    lease_extend_enabled=True,  # Enable automatic heartbeat
)
def analyze_dataset(dataset_id: str) -> dict:
    """This task takes 5 minutes but responseTimeoutSeconds is 60s.
    Heartbeats keep it alive automatically."""
    results = run_expensive_analysis(dataset_id)
    return {'results': results}
```

That's it. The SDK handles heartbeats automatically in the background.

## Enabling Lease Extension

Lease extension is **disabled by default** (matching the Java SDK). Enable it per-worker or globally:

### Per-Worker (Decorator)

```python
@worker_task(
    task_definition_name='my_task',
    lease_extend_enabled=True,
)
def my_task(data: str) -> dict:
    ...
```

### Per-Worker (Class)

```python
from conductor.client.worker.worker import Worker

worker = Worker(
    task_definition_name='my_task',
    execute_function=my_function,
    lease_extend_enabled=True,
)
```

### Per-Worker (Environment Variable)

```shell
export conductor_worker_my_task_lease_extend_enabled=true
```

### Global (All Workers)

```shell
export conductor_worker_all_lease_extend_enabled=true
```

### Precedence

Environment variables override decorator/constructor arguments:

1. Task-specific env var (`conductor_worker_<task>_lease_extend_enabled`)
2. Global env var (`conductor_worker_all_lease_extend_enabled`)
3. Worker constructor / decorator argument

## When to Use

**Enable lease extension when:**
- Task execution time may exceed `responseTimeoutSeconds`
- Tasks involve external calls with unpredictable latency (LLM APIs, data pipelines)
- You want the worker to hold the task continuously (not yield and re-poll)

**You don't need lease extension when:**
- Tasks always complete within `responseTimeoutSeconds`
- You're using `TaskInProgress` with `callbackAfterSeconds` (the task is yielded back to the queue)
- `responseTimeoutSeconds` is 0 (no timeout configured)

## Lease Extension vs TaskInProgress

These are two different strategies for long-running tasks:

| | Lease Extension | TaskInProgress |
|---|---|---|
| **How it works** | Worker holds the task, heartbeats keep it alive | Worker yields the task, re-polls later |
| **Task state** | IN_PROGRESS the whole time | Returned to queue between polls |
| **When to use** | Continuous execution (LLM calls, streaming) | Incremental processing (batch chunks, polling external status) |
| **Enable with** | `lease_extend_enabled=True` | Return `TaskInProgress(callback_after_seconds=N)` |
| **Worker memory** | Task stays in worker memory | Task is released, re-polled with fresh context |

You can combine both — enable `lease_extend_enabled` for safety while also using `TaskInProgress` for incremental polling.

## Important Constraints

- **`responseTimeoutSeconds`** is the time between updates. This is what heartbeats reset.
- **`timeoutSeconds`** is the overall SLA wall-clock ceiling. **Cannot be extended by heartbeat.** Once exceeded, the task is TIMED_OUT regardless of heartbeats.
- Heartbeats only fire when `responseTimeoutSeconds > 0` and `lease_extend_enabled = True`.
- If the heartbeat interval would be less than 1 second (i.e., `responseTimeoutSeconds < 1.25`), heartbeats are skipped.

## Retry on Failure

If a heartbeat API call fails, the SDK retries up to 3 times with backoff (`1s`, `1.5s`, `2s`). If all retries fail, the error is logged and the SDK tries again on the next poll loop iteration. If the network is truly partitioned, the server will eventually time out the task — this is correct behavior.

## Example

See [examples/lease_extension_example.py](examples/lease_extension_example.py) for a complete runnable example that:
- Defines a long-running worker with `lease_extend_enabled=True`
- Creates a workflow with a short `responseTimeoutSeconds`
- Runs the workflow and proves the task completes despite sleeping longer than the timeout
