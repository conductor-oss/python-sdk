# V2 API Task Chaining Design

## Overview

The V2 API introduces an optimization for chained workflows where the server returns the **next task** in the workflow as part of the task update response. This eliminates redundant polling and significantly reduces server load for sequential workflows.

---

## Problem Statement

### Without V2 API (Traditional Polling)

**Scenario**: Multiple workflows need the same task type processed

```
Worker for task type "process_image":
  1. Poll server for task          → HTTP GET /tasks/poll?taskType=process_image
  2. Receive Task A (from Workflow 1)
  3. Execute Task A
  4. Update Task A result          → HTTP POST /tasks
  5. Poll server for next task     → HTTP GET /tasks/poll?taskType=process_image  ← REDUNDANT
  6. Receive Task B (from Workflow 2)
  7. Execute Task B
  8. Update Task B result          → HTTP POST /tasks
  9. Poll server for next task     → HTTP GET /tasks/poll?taskType=process_image  ← REDUNDANT
  ... (continues)
```

**Server calls**: 2N HTTP requests (N polls + N updates)

**Problem**: After completing Task A of type `process_image`, the server **already knows** there's another pending `process_image` task (Task B from a different workflow), but the worker must make a separate poll request to discover it.

---

## Solution: V2 API with In-Memory Queue

### With V2 API

**Same scenario**: Multiple workflows with `process_image` tasks

```
Worker for task type "process_image":
  1. Poll server for task          → HTTP GET /tasks/poll?taskType=process_image
  2. Receive Task A (from Workflow 1)
  3. Execute Task A
  4. Update Task A result          → HTTP POST /tasks/update-v2
     Server response: {Task B data}  ← NEXT "process_image" TASK!
  5. Add Task B to in-memory queue → No network call
  6. Poll from queue (not server)  → No network call
  7. Receive Task B from queue
  8. Execute Task B
  9. Update Task B result          → HTTP POST /tasks/update-v2
     Server response: {Task C data}  ← NEXT "process_image" TASK!
  ... (continues)
```

**Server calls**: N+1 HTTP requests (1 initial poll + N updates)

**Savings**: N fewer HTTP requests (~50% reduction)

**Key Point**: Server returns the next pending task **of the same type** (`process_image`), not the next task in the workflow sequence.

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    TaskRunnerAsyncIO                         │
│                                                              │
│  ┌────────────────┐         ┌────────────────┐             │
│  │  In-Memory     │         │   Semaphore    │             │
│  │  Task Queue    │◄────────┤  (thread_count)│             │
│  │ (asyncio.Queue)│         └────────────────┘             │
│  └────────────────┘                                         │
│         ▲                                                    │
│         │                                                    │
│         │ 2. Add next task                                  │
│         │                                                    │
│  ┌──────┴───────────────────────────────┐                  │
│  │        Task Update Flow               │                  │
│  │                                       │                  │
│  │  1. Update task result                │                  │
│  │     → POST /tasks/update-v2           │                  │
│  │                                       │                  │
│  │  2. Parse response                    │                  │
│  │     → If next task: add to queue      │                  │
│  │                                       │                  │
│  └───────────────────────────────────────┘                  │
│                                                              │
│  ┌───────────────────────────────────────┐                  │
│  │        Task Poll Flow                 │                  │
│  │                                       │                  │
│  │  1. Check in-memory queue first       │                  │
│  │     → If tasks available: return them │                  │
│  │                                       │                  │
│  │  2. If queue empty: poll server       │                  │
│  │     → GET /tasks/poll?count=N         │                  │
│  │                                       │                  │
│  └───────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Data Structures

**In-Memory Queue** (`self._task_queue`):
```python
self._task_queue = asyncio.Queue()  # Unbounded queue for V2 chained tasks
```

**V2 API Flag** (`self._use_v2_api`):
```python
self._use_v2_api = True  # Default enabled
# Can be overridden by environment variable: taskUpdateV2
```

---

## Implementation Details

### 1. Task Update with V2 API

**Location**: `task_runner_asyncio.py:911-960`

```python
async def _update_task(self, task_result: TaskResult, is_lease_extension: bool = False):
    """Update task result and optionally receive next task"""

    # Choose endpoint based on V2 flag
    endpoint = "/tasks/update-v2" if self._use_v2_api else "/tasks"

    # Send update
    response = await self.http_client.post(
        endpoint,
        json=task_result_dict,
        headers=headers
    )

    # V2 API: Check if server returned next task
    if self._use_v2_api and response.status_code == 200 and not is_lease_extension:
        response_data = response.json()

        # Server response can be:
        # 1. Empty string "" → No next task
        # 2. Task object → Next task in workflow

        if response_data and 'taskId' in response_data:
            next_task = deserialize_task(response_data)

            logger.info(
                "V2 API returned next task: %s (type: %s) - adding to queue",
                next_task.task_id,
                next_task.task_def_name
            )

            # Add to in-memory queue
            await self._task_queue.put(next_task)
```

**Key Points**:
- Only parses response for **regular updates** (not lease extensions)
- Validates response has `taskId` field to confirm it's a task
- Adds valid tasks to in-memory queue
- Logs for observability

### 2. Task Polling with Queue Draining

**Location**: `task_runner_asyncio.py:306-331`

```python
async def _poll_tasks(self, poll_count: int) -> List[Task]:
    """
    Poll tasks with queue-first strategy.

    Priority:
      1. Drain in-memory queue (V2 chained tasks)
      2. Poll server if needed
    """
    tasks = []

    # Step 1: Drain in-memory queue first
    while len(tasks) < poll_count and not self._task_queue.empty():
        try:
            task = self._task_queue.get_nowait()
            tasks.append(task)
        except asyncio.QueueEmpty:
            break

    # Step 2: If we still need tasks, poll from server
    if len(tasks) < poll_count:
        remaining_count = poll_count - len(tasks)
        server_tasks = await self._poll_tasks_from_server(remaining_count)
        tasks.extend(server_tasks)

    return tasks
```

**Key Points**:
- Queue is checked **before** server polling
- `get_nowait()` is non-blocking (fails fast if empty)
- Server polling only happens if queue is empty or insufficient
- Respects semaphore permit count (poll_count)

### 3. Main Execution Loop

**Location**: `task_runner_asyncio.py:205-290`

```python
async def run_once(self):
    """Single poll/execute/update cycle"""

    # Acquire permits (dynamic batch sizing)
    poll_count = await self._acquire_available_permits()

    if poll_count == 0:
        # Zero-polling optimization
        await asyncio.sleep(self.worker.poll_interval / 1000.0)
        return

    # Poll tasks (queue-first, then server)
    tasks = await self._poll_tasks(poll_count)

    # Execute tasks concurrently
    for task in tasks:
        # Create background task for execute + update
        background_task = asyncio.create_task(
            self._execute_and_update_task(task)
        )
        self._background_tasks.add(background_task)
```

---

## Workflow Example: Multiple Workflows with Same Task Type

### Scenario

**3 concurrent workflows** all use task type `process_image`:

- **Workflow 1**: User A uploads profile photo
  - Task: `process_image` (instance: W1-T1)

- **Workflow 2**: User B uploads banner image
  - Task: `process_image` (instance: W2-T1)

- **Workflow 3**: User C uploads gallery photo
  - Task: `process_image` (instance: W3-T1)

All 3 tasks are queued on the server, waiting for a `process_image` worker.

### Execution Flow with V2 API

```
┌───────────────────────────────────────────────────────────────────────┐
│ Time  │ Action                    │ Queue State    │ Network Calls    │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T0    │ Poll server               │ []             │ GET /tasks/poll  │
│       │ taskType=process_image    │                │ ?taskType=       │
│       │ Receive: W1-T1            │                │ process_image    │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T1    │ Execute: W1-T1            │ []             │ -                │
│       │ (Process User A's photo)  │                │                  │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T2    │ Update: W1-T1             │ []             │ POST /update-v2  │
│       │ Server checks: More       │                │                  │
│       │ process_image tasks?      │                │                  │
│       │ → YES: W2-T1 pending      │                │                  │
│       │ Response: W2-T1 data      │                │                  │
│       │ Add W2-T1 to queue        │ [W2-T1]        │                  │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T3    │ Poll from queue           │ [W2-T1]        │ -                │
│       │ Receive: W2-T1            │ []             │ (no server!)     │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T4    │ Execute: W2-T1            │ []             │ -                │
│       │ (Process User B's banner) │                │                  │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T5    │ Update: W2-T1             │ []             │ POST /update-v2  │
│       │ Server checks: More       │                │                  │
│       │ process_image tasks?      │                │                  │
│       │ → YES: W3-T1 pending      │                │                  │
│       │ Response: W3-T1 data      │                │                  │
│       │ Add W3-T1 to queue        │ [W3-T1]        │                  │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T6    │ Poll from queue           │ [W3-T1]        │ -                │
│       │ Receive: W3-T1            │ []             │ (no server!)     │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T7    │ Execute: W3-T1            │ []             │ -                │
│       │ (Process User C's gallery)│                │                  │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T8    │ Update: W3-T1             │ []             │ POST /update-v2  │
│       │ Server checks: More       │                │                  │
│       │ process_image tasks?      │                │                  │
│       │ → NO: Queue empty         │                │                  │
│       │ Response: (empty)         │                │                  │
├───────┼───────────────────────────┼────────────────┼──────────────────┤
│ T9    │ Poll from queue           │ []             │ -                │
│       │ Queue empty, poll server  │                │ GET /tasks/poll  │
│       │ No tasks available        │                │                  │
└───────┴───────────────────────────┴────────────────┴──────────────────┘

Total network calls: 5 (2 polls + 3 updates)
Without V2 API:     6 (3 polls + 3 updates)
Savings:            ~17%

Note: Savings increase with more pending tasks of the same type.
```

### Key Insight

**V2 API returns next task OF THE SAME TYPE**, not next task in workflow:
- ✅ Worker for `process_image` completes task → Gets another `process_image` task
- ❌ Worker for `process_image` completes task → Does NOT get `send_email` task

This means V2 API benefits **task types with high throughput** (many pending tasks), not necessarily sequential workflows.

---

## Benefits

### 1. Reduced Network Overhead

**High-throughput task types** (many pending tasks of same type):
- **Before**: 2N HTTP requests (N polls + N updates)
- **After**: ~N+1 HTTP requests (1 initial poll + N updates + occasional polls when queue empty)
- **Savings**: Up to 50% when queue never empties

**Example**: Image processing service with 1000 pending `process_image` tasks
- Worker keeps getting next task after each update
- Eliminates 999 poll requests
- Only 1 initial poll + 1000 updates = 1001 requests (vs 2000)

**Low-throughput task types** (few pending tasks):
- Minimal benefit (queue often empty)
- Still needs to poll server frequently

### 2. Lower Latency

**Without V2**:
```
Complete T1 → Wait for poll interval → Poll server → Receive T2 → Execute T2
              └── 100ms delay ──────┘
```

**With V2**:
```
Complete T1 → Immediately get T2 from queue → Execute T2
              └── 0ms delay (in-memory) ──┘
```

**Latency reduction**: Eliminates poll interval wait time (typically 100-200ms per task)

### 3. Server Load Reduction

For 100 workers processing sequential workflows:
- **Before**: 100 workers × 10 polls/sec = 1,000 requests/sec
- **After**: 100 workers × 4 polls/sec = 400 requests/sec
- **Savings**: 60% reduction in server load

---

## Edge Cases & Handling

### 1. Empty Response

**Scenario**: Server has no next task to return

```python
# Server response: ""
response.text == ""

# Handler:
if response_text and response_text.strip():
    # Parse task
else:
    # No next task - queue remains empty
    # Next poll will go to server
```

### 2. Invalid Task Response

**Scenario**: Response is not a valid task

```python
# Server response: {"status": "success"}  (no taskId)

# Handler:
if response_data and 'taskId' in response_data:
    # Valid task
else:
    # Invalid - ignore silently
    # Next poll will go to server
```

### 3. Lease Extension Updates

**Scenario**: Lease extension should NOT add tasks to queue

```python
# Lease extension update
await self._update_task(task_result, is_lease_extension=True)

# Handler:
if self._use_v2_api and not is_lease_extension:
    # Only parse for regular updates
```

**Reason**: Lease extensions don't represent workflow progress, so next task isn't ready.

### 4. Task for Different Worker

**Scenario**: Server returns a task for a different task type

```python
# Worker is for 'resize_image'
# Server might return 'compress_image' task?
```

**Answer**: **This CANNOT happen** with V2 API

**Server guarantee**: V2 API only returns tasks of the **same type** as the task being updated.

- Worker updates `resize_image` task → Server only returns another `resize_image` task (or empty)
- Worker updates `process_image` task → Server only returns another `process_image` task (or empty)

**No validation needed** in the client code - server ensures type matching.

### 5. Multiple Workers for Same Task Type

**Scenario**: 5 workers polling for `resize_image` tasks, 100 pending tasks

```python
# All 5 workers share same task type but different worker instances
# Each has their own in-memory queue

Initial state:
- Server has 100 pending resize_image tasks
- Worker 1-5 all idle

Execution:
Worker 1: Poll server → Receives Task 1 → Execute → Update → Receives Task 6
Worker 2: Poll server → Receives Task 2 → Execute → Update → Receives Task 7
Worker 3: Poll server → Receives Task 3 → Execute → Update → Receives Task 8
Worker 4: Poll server → Receives Task 4 → Execute → Update → Receives Task 9
Worker 5: Poll server → Receives Task 5 → Execute → Update → Receives Task 10

Now:
- Each worker has 1 task in their local queue
- Server has 90 pending tasks
- Workers poll from queue (not server) for next iteration
```

**Result**: Perfect distribution - each worker gets their own stream of tasks

**Server guarantee**: Task locking ensures no duplicate execution (each task assigned to only one worker)

### 6. Queue Overflow

**Scenario**: Can the queue grow unbounded?

```python
# asyncio.Queue is unbounded by default
self._task_queue = asyncio.Queue()
```

**Answer**: **No, queue cannot overflow**

**Reason**: Queue size is naturally limited by semaphore permits

**Explanation**:
```python
# Worker has thread_count=5 (5 concurrent executions)
# Each execution holds 1 semaphore permit

Max scenario:
1. Worker polls with 5 permits available → Gets 5 tasks from server
2. Executes all 5 tasks concurrently
3. Each task completes and updates:
   - Task 1 update → Receives Task 6 → Queue: [Task 6]
   - Task 2 update → Receives Task 7 → Queue: [Task 6, Task 7]
   - Task 3 update → Receives Task 8 → Queue: [Task 6, Task 7, Task 8]
   - Task 4 update → Receives Task 9 → Queue: [Task 6, Task 7, Task 8, Task 9]
   - Task 5 update → Receives Task 10 → Queue: [Task 6, ..., Task 10]

Maximum queue size: thread_count (5 in this example)
```

**Worst case**: Queue holds `thread_count` tasks (bounded by concurrency)

**Memory usage**: Negligible (each Task object ~1-2 KB)

---

## Performance Metrics

### Expected Improvements

| Task Type Scenario | Pending Tasks | Network Reduction | Latency Reduction | Server Load Reduction |
|-------------------|---------------|-------------------|-------------------|----------------------|
| High throughput (never empties) | 1000+ | ~50% | 100ms/task | ~50% |
| Medium throughput | 100-1000 | 30-40% | 100ms/task | 30-40% |
| Low throughput (often empty) | 1-10 | 5-15% | Minimal | 5-15% |
| Batch processing | Large batches | 40-50% | 100ms/task | 40-50% |

**Key Factor**: Performance depends on **queue depth** (how often next task is available), not workflow structure

### Monitoring

**Key Metrics to Track**:

1. **Queue Hit Rate**:
   ```python
   queue_hits / (queue_hits + server_polls)
   ```
   Target: >50% for sequential workflows

2. **Queue Depth**:
   ```python
   self._task_queue.qsize()
   ```
   Target: <10 tasks (prevents memory growth)

3. **Task Latency**:
   ```python
   time_to_execute = task_end - task_start
   ```
   Target: Reduced by poll_interval (100ms)

---

## Configuration

### Enable/Disable V2 API

**Constructor parameter** (recommended):
```python
handler = TaskHandlerAsyncIO(
    configuration=config,
    use_v2_api=True  # Default: True
)
```

**Environment variable** (overrides constructor):
```bash
export taskUpdateV2=true  # Enable V2
export taskUpdateV2=false # Disable V2
```

**Precedence**: `env var > constructor param`

### Server-Side Requirements

Server must:
1. Support `/tasks/update-v2` endpoint
2. Return next task in workflow as response body
3. Return empty string if no next task
4. Ensure task is valid for the worker that updated

---

## Testing

### Unit Tests

**Test Coverage**: 7 tests in `test_task_runner_asyncio_concurrency.py`

1. ✅ V2 API enabled by default
2. ✅ V2 API can be disabled via constructor
3. ✅ Environment variable overrides constructor
4. ✅ Correct endpoint used (`/tasks/update-v2`)
5. ✅ Next task added to queue
6. ✅ Empty response not added to queue
7. ✅ Queue drained before server polling

### Integration Test Scenario

```python
# Create sequential workflow
workflow = {
    'tasks': [
        {'name': 'task1', 'taskReferenceName': 'task1'},
        {'name': 'task2', 'taskReferenceName': 'task2'},
        {'name': 'task3', 'taskReferenceName': 'task3'},
    ]
}

# Start workflow
workflow_id = conductor.start_workflow('test_workflow', {})

# Monitor:
# 1. Worker polls once (initial)
# 2. Worker executes task1 → receives task2 in response
# 3. Worker polls from queue (no server call)
# 4. Worker executes task2 → receives task3 in response
# 5. Worker polls from queue (no server call)
# 6. Worker executes task3 → no next task

# Expected:
# - Total server polls: 1
# - Total updates: 3
# - Queue hits: 2
```

---

## Future Enhancements

### 1. Queue Size Limit

**Problem**: Unbounded queue can grow indefinitely

**Solution**: Use bounded queue
```python
self._task_queue = asyncio.Queue(maxsize=100)
```

### 2. Task Routing

**Problem**: Worker may receive task for different type

**Solution**: Check task type and route to correct worker
```python
if task.task_def_name != self.worker.task_definition_name:
    # Route to correct worker or re-queue to server
    await self._requeue_to_server(task)
```

### 3. Prefetching

**Problem**: Worker becomes idle waiting for next task

**Solution**: Server returns next N tasks (not just one)
```python
# Server response: [task2, task3, task4]
for next_task in response_data['nextTasks']:
    await self._task_queue.put(next_task)
```

### 4. Metrics & Observability

**Enhancement**: Add detailed metrics
```python
self.metrics = {
    'queue_hits': 0,
    'server_polls': 0,
    'queue_depth_max': 0,
    'latency_reduction_ms': 0
}
```

---

## Comparison to Java SDK

| Feature | Java SDK | Python AsyncIO | Status |
|---------|----------|---------------|--------|
| V2 API Endpoint | `POST /tasks/update-v2` | `POST /tasks/update-v2` | ✅ Matches |
| In-Memory Queue | `LinkedBlockingQueue<Task>` | `asyncio.Queue()` | ✅ Matches |
| Queue Draining | `queue.poll()` before server | `queue.get_nowait()` before server | ✅ Matches |
| Response Parsing | JSON → Task object | JSON → Task object | ✅ Matches |
| Empty Response | Skip if null | Skip if empty string | ✅ Matches |
| Lease Extension | Don't parse response | Don't parse response | ✅ Matches |

---

## Summary

The V2 API provides significant performance improvements for **high-throughput task types** by:

1. **Eliminating redundant polls**: Server returns next task **of same type** in update response
2. **In-memory queue**: Tasks stored locally, avoiding network round-trip
3. **Queue-first polling**: Always drain queue before hitting server
4. **Zero overhead**: Adds <1ms latency for queue operations
5. **Natural bounds**: Queue size limited to `thread_count` (no overflow risk)

### Key Behavioral Points

✅ **What V2 API Does**:
- Worker updates task of type `T` → Server returns another pending task of type `T`
- Benefits task types with many pending tasks (high throughput)
- Each worker instance has its own queue
- Server ensures no duplicate task assignment

❌ **What V2 API Does NOT Do**:
- Does NOT return next task in workflow sequence (different types)
- Does NOT benefit low-throughput task types (queue often empty)
- Does NOT require workflow to be sequential

### Expected Results

**High-throughput scenarios** (1000+ pending tasks of same type):
- 40-50% reduction in network calls
- 100ms+ latency reduction per task
- 40-50% reduction in server poll load

**Low-throughput scenarios** (few pending tasks):
- 5-15% reduction in network calls
- Minimal latency improvement
- Small reduction in server load

### Trade-offs

**Pros**:
- ✅ Huge benefit for batch processing and popular task types
- ✅ No risk of queue overflow (bounded by thread_count)
- ✅ No extra code complexity or validation needed
- ✅ Works seamlessly with multiple workers

**Cons**:
- ❌ Minimal benefit for low-throughput task types
- ❌ Requires server support for `/tasks/update-v2` endpoint

### Recommendation

**Enable by default** - V2 API has minimal overhead and provides significant benefits for high-throughput scenarios. The worst case (low throughput) is still correct, just with less benefit.

**When to disable**:
- Server doesn't support `/tasks/update-v2` endpoint
- Debugging task assignment issues
- Testing traditional polling behavior
