# Design: Task Lease Extension (Heartbeat)

## Problem

When a worker picks up a task, the Conductor server starts a `responseTimeoutSeconds` timer. If the worker doesn't send an update before the timer expires, the server marks the task as timed out and re-queues it for retry.

This is a problem for long-running tasks (e.g., agent tool calls, LLM inference, data processing). The worker is actively executing, but the server thinks it's dead.

Today, the only workaround in the Python SDK is `TaskInProgress` with `callbackAfterSeconds` — which yields the task back to the queue. That doesn't work for continuous execution where the worker must hold the task.

The Java SDK solves this with automatic lease extension: a background thread periodically sends a heartbeat (`extendLease=true`) to reset the `responseTimeoutSeconds` timer. The Python SDK has the `extend_lease` field on `TaskResult` and `lease_extend_enabled` on Worker, but **no background heartbeat loop** — the docs say "Not implemented — reserved for future use."

## Goal

Implement automatic lease extension in the Python SDK, matching the Java SDK's semantics:

- Heartbeat at 80% of `responseTimeoutSeconds`
- Only when `responseTimeoutSeconds > 0` and `lease_extend_enabled = True`
- Retry on failure (3 attempts)
- Automatic stop on task completion
- Graceful shutdown cleanup
- **Disabled by default** — opt-in per-worker or globally via config/env var

## Java SDK Reference

The Java SDK implementation in `TaskRunner.java`:

```java
// Constants
LEASE_EXTEND_RETRY_COUNT = 3
LEASE_EXTEND_DURATION_FACTOR = 0.8

// Disabled by default — Worker interface:
default boolean leaseExtendEnabled() {
    return PropertyFactory.getBoolean(getTaskDefName(), PROP_LEASE_EXTEND_ENABLED, false);
}

// When task is polled and worker has leaseExtendEnabled:
if (task.getResponseTimeoutSeconds() > 0 && worker.leaseExtendEnabled()) {
    long delay = Math.round(task.getResponseTimeoutSeconds() * 0.8);
    leaseExtendFuture = leaseExtendExecutorService.scheduleWithFixedDelay(
        extendLease(task, taskFuture), delay, delay, TimeUnit.SECONDS
    );
    leaseExtendMap.put(task.getTaskId(), leaseExtendFuture);
}

// Cancellation — in processTask() finally block:
cancelLeaseExtension(task.getTaskId())
```

Key properties:
- **Disabled by default** — must be explicitly enabled per worker
- **Only when `responseTimeoutSeconds > 0`** — no heartbeat if there's no timeout
- **Fires at 80%** of `responseTimeoutSeconds` — e.g., 120s timeout → heartbeat at 96s
- **Separate single-threaded executor** — heartbeats never block task execution
- **Retry** — 3 attempts with `500ms * (count+1)` backoff
- **Always cancelled in finally** — whether task succeeds, fails, or throws

## Server-Side Behavior (No Changes Needed)

The server already fully supports lease extension. No server changes required.

### Flow

1. Worker sends `POST /tasks` with `TaskResult.extendLease = true`
2. `WorkflowExecutorOps.updateTask()` checks `isExtendLease()` → short-circuits:
   ```java
   if (taskResult.isExtendLease()) {
       extendLease(taskResult);  // resets updateTime only
       return null;              // no further task processing
   }
   ```
3. `ExecutionDAOFacade.extendLease()` updates **only** `task.updateTime`:
   ```java
   public void extendLease(TaskModel taskModel) {
       taskModel.setUpdateTime(System.currentTimeMillis());
       executionDAO.updateTask(taskModel);
   }
   ```
4. All other fields in the `TaskResult` are ignored

### Timeout Check

The server's `DeciderService.isResponseTimedOut()` runs during workflow evaluation:

```
Task times out when:
  (now - task.updateTime) > (responseTimeoutSeconds + callbackAfterSeconds) * 1000
```

Each heartbeat resets `updateTime` to now → fresh `responseTimeoutSeconds` window.

### Validations

- Task must exist (404 if not)
- Task must NOT be in terminal state — if already COMPLETED/FAILED/TIMED_OUT, heartbeat is silently ignored (handles race conditions)

### Response

- `POST /tasks` → returns task ID (plain text)
- `POST /tasks/update-v2` → returns `204 No Content` (no next-task polling on heartbeat)

### Important Constraints

- **`responseTimeoutSeconds`** — time between updates before timeout. **This is what heartbeat resets.**
- **`timeoutSeconds`** — overall SLA wall-clock ceiling. **Cannot be extended by heartbeat.** Once exceeded, task is TIMED_OUT regardless.

## Design

### Approach: Inline Heartbeat in the Poll Loop

Instead of a dedicated background thread (Java approach), piggyback heartbeats on the existing `run_once()` poll loop that already cycles continuously in each worker process.

```
TaskRunner.run_once() loop (already exists):
  1. Check completed async tasks
  2. Cleanup finished futures
  3. ← NEW: Check in-flight tasks, send heartbeats if due
  4. Batch poll for new tasks
  5. Submit tasks to thread pool
```

**Why this over background threads:**
- No extra threads — uses the existing poll loop infrastructure
- No Timer/ScheduledExecutor complexity, no cancellation logic
- Heartbeat state is naturally cleaned up when tasks complete
- Simpler shutdown — no separate executor to drain
- The poll loop runs frequently enough (adaptive backoff resets when tasks are active)

**Trade-off:** Heartbeat timing is approximate (depends on poll loop frequency), but it doesn't need to be precise — we just need to fire before 100% of `responseTimeoutSeconds`.

### Tracking State

```python
@dataclass
class _LeaseInfo:
    """Tracks when a heartbeat is next due for an in-flight task."""
    task_id: str
    workflow_instance_id: str
    response_timeout_seconds: float
    last_heartbeat_time: float  # time.monotonic() of last heartbeat (or task start)
    interval_seconds: float     # 80% of responseTimeoutSeconds
```

On `TaskRunner.__init__()`:
```python
self._lease_info: dict[str, _LeaseInfo] = {}  # task_id → _LeaseInfo
```

### Core Methods

```python
LEASE_EXTEND_RETRY_COUNT = 3
LEASE_EXTEND_DURATION_FACTOR = 0.8

def _track_lease(self, task: Task) -> None:
    """Start tracking a task for heartbeat. Called when task begins execution."""
    if not self.worker.lease_extend_enabled:
        return
    timeout = task.response_timeout_seconds
    if not timeout or timeout <= 0:
        return
    interval = timeout * LEASE_EXTEND_DURATION_FACTOR
    if interval < 1:
        return
    self._lease_info[task.task_id] = _LeaseInfo(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
        response_timeout_seconds=timeout,
        last_heartbeat_time=time.monotonic(),
        interval_seconds=interval,
    )

def _untrack_lease(self, task_id: str) -> None:
    """Stop tracking a task. Called when task completes or fails."""
    self._lease_info.pop(task_id, None)

def _send_due_heartbeats(self) -> None:
    """Check all tracked tasks and send heartbeats for any that are due.
    Called at the top of each run_once() iteration."""
    if not self._lease_info:
        return
    now = time.monotonic()
    for info in list(self._lease_info.values()):
        elapsed = now - info.last_heartbeat_time
        if elapsed < info.interval_seconds:
            continue
        # Heartbeat is due
        self._send_heartbeat(info)
        info.last_heartbeat_time = time.monotonic()

def _send_heartbeat(self, info: _LeaseInfo) -> None:
    """Send a single lease extension heartbeat with retry."""
    result = TaskResult(
        task_id=info.task_id,
        workflow_instance_id=info.workflow_instance_id,
        extend_lease=True,
    )
    for attempt in range(LEASE_EXTEND_RETRY_COUNT):
        try:
            self.task_client.update_task(body=result)
            logger.debug("Extended lease for task %s", info.task_id)
            return
        except Exception:
            if attempt < LEASE_EXTEND_RETRY_COUNT - 1:
                time.sleep(0.5 * (attempt + 2))
            else:
                logger.error(
                    "Failed to extend lease for task %s after %d attempts",
                    info.task_id, LEASE_EXTEND_RETRY_COUNT,
                )
```

### Integration Points

#### TaskRunner.run_once()

```python
def run_once(self) -> None:
    self.__check_completed_async_tasks()
    self.__cleanup_completed_tasks()
    self._send_due_heartbeats()          # ← NEW: send heartbeats before polling
    # ... existing polling and task submission logic ...
```

#### Task Execution Tracking

In `__execute_and_update_task()`:

```python
def __execute_and_update_task(self, task: Task) -> None:
    self._track_lease(task)                        # ← NEW
    try:
        while task is not None and not self._shutdown:
            task_result = self.__execute_task(task)
            if task_result is None or isinstance(task_result, TaskInProgress):
                return
            self._untrack_lease(task.task_id)       # ← NEW: done with this task
            task = self.__update_task(task_result)
            if task is not None:
                self._track_lease(task)             # ← NEW: v2 returned next task
    finally:
        if task is not None:
            self._untrack_lease(task.task_id)       # ← NEW: always cleanup
```

#### AsyncTaskRunner.run_once()

Same pattern — `_send_due_heartbeats_async()` at the top of `run_once()`, using `await` for the API call:

```python
async def run_once(self) -> None:
    await self._send_due_heartbeats_async()   # ← NEW
    # ... existing async polling and task submission logic ...
```

#### Cleanup on Shutdown

```python
def _cleanup(self) -> None:
    self._lease_info.clear()         # ← NEW: drop all tracking
    # ... existing shutdown logic ...
```

### Configuration

No new configuration surface. The existing plumbing already works end-to-end:

| Layer | How to enable | Default |
|-------|--------------|---------|
| `@worker_task` decorator | `lease_extend_enabled=True` | `False` |
| `Worker` class | `Worker(..., lease_extend_enabled=True)` | `False` |
| Environment variable | `conductor.worker.<taskName>.lease_extend_enabled=true` | `False` |
| Global env override | `conductor.worker.all.lease_extend_enabled=true` | `False` |
| `TaskRunner` | `__set_worker_properties()` resolves and applies | `False` |

Matches Java SDK: **disabled by default**, opt-in per worker or globally.

### Constants

Match Java SDK:

```python
LEASE_EXTEND_RETRY_COUNT = 3          # retries per heartbeat attempt
LEASE_EXTEND_DURATION_FACTOR = 0.8    # heartbeat at 80% of responseTimeoutSeconds
```

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| `lease_extend_enabled = False` (default) | No tracking, no heartbeats — zero overhead for existing users |
| `responseTimeoutSeconds = 0` | No tracking (no timeout to extend) |
| `responseTimeoutSeconds` very small (< 1.25s) | `interval = x * 0.8` — if < 1s, skip (too small to heartbeat meaningfully) |
| Poll loop slower than heartbeat interval | Heartbeat fires on next `run_once()` — slightly late but still within `responseTimeoutSeconds` since we fire at 80% |
| Task completes between heartbeat checks | `_untrack_lease()` removes it; no stale heartbeat sent |
| Heartbeat fails 3 times | Log error, keep tracking — next `run_once()` will retry. Task may timeout server-side if network-partitioned (correct behavior) |
| Worker process crashes | Tracking dict dies with process — server times out task after `responseTimeoutSeconds`, re-queues |
| `_shutdown` set | `run_once()` loop stops → no more heartbeats; `_cleanup()` clears tracking |
| v2 endpoint returns next task | Old task untracked, new task tracked with fresh timestamp |
| Multiple tasks in-flight (thread_count > 1) | Each tracked independently in `_lease_info` dict; `_send_due_heartbeats()` iterates all |

## Files to Change

1. **`src/conductor/client/automator/task_runner.py`**
   - Add `_LeaseInfo` dataclass and constants
   - Add `_lease_info` dict to `__init__()`
   - Add `_track_lease()`, `_untrack_lease()`, `_send_due_heartbeats()`, `_send_heartbeat()`
   - Wire into `run_once()` and `__execute_and_update_task()`
   - Add `_lease_info.clear()` to `_cleanup()`

2. **`src/conductor/client/automator/async_task_runner.py`**
   - Same additions with async variants
   - `_send_due_heartbeats_async()` uses `await` for API calls

3. **`WORKER_CONFIGURATION.md`**
   - Remove "Not implemented — reserved for future use" warning
   - Document heartbeat behavior: 80% interval, retry logic, when to enable

4. **Tests**
   - Verify heartbeat sent when `lease_extend_enabled=True` and `responseTimeoutSeconds > 0`
   - Verify NO heartbeat when `lease_extend_enabled=False`
   - Verify NO heartbeat when `responseTimeoutSeconds = 0`
   - Verify `_untrack_lease()` on task completion prevents further heartbeats
   - Verify retry logic on API failure
   - Integration test: long-running task with short `responseTimeoutSeconds` completes without timeout

## Non-Goals

- **Extending `timeoutSeconds`** — the overall SLA is a hard ceiling, unaffected by lease extension
- **Server-side changes** — server already supports `extendLease` fully
- **Dedicated API endpoint** — uses existing `POST /tasks` with `extendLease` flag (matches Java SDK)
- **Configurable heartbeat factor** — hardcoded to 0.8 (matches Java SDK; can be made configurable later if needed)
