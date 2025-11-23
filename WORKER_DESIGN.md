# Worker Design & Implementation

**Version:** 3.2 | **Date:** 2025-01-22 | **SDK:** 1.2.6+

**Recent Updates (v3.2):**
- ✅ HTTP-based metrics serving (built-in server, no file writes)
- ✅ Automatic metric aggregation across processes (no PID labels)
- ✅ Accurate async task execution timing (submission to completion)
- ✅ Async tasks can return `None` (sentinel pattern)
- ✅ Event-driven metrics collection (zero coupling)
- ✅ Batch polling with dynamic capacity calculation

---

## What is a Worker?

Workers are task execution units in Netflix Conductor that poll for and execute tasks within workflows. When a workflow reaches a task, Conductor queues it for execution. Workers continuously poll Conductor for tasks matching their registered task types, execute the business logic, and return results.

**Key Concepts:**
- **Task**: Unit of work in a workflow (e.g., "send_email", "process_payment")
- **Worker**: Python function (sync or async) decorated with `@worker_task` that implements task logic
- **Polling**: Workers actively poll Conductor for pending tasks
- **Execution**: Workers run task logic and return results (success, failure, or in-progress)
- **Scalability**: Multiple workers can process the same task type concurrently

**Example Workflow:**
```
Workflow: Order Processing
├── Task: validate_order (worker: order_validator)
├── Task: charge_payment (worker: payment_processor)
└── Task: send_confirmation (worker: email_sender)
```

Each task is executed by a dedicated worker that polls for that specific task type.

---


## Quick Start

### Sync Worker
```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='process_data', thread_count=5)
def process_data(input_value: int) -> dict:
    result = expensive_computation(input_value)
    return {'result': result}
```

### Async Worker (Automatic High Concurrency)
```python
@worker_task(task_definition_name='fetch_data', thread_count=50)
async def fetch_data(url: str) -> dict:
    # Automatically runs as non-blocking coroutine
    # 10-100x better concurrency for I/O-bound workloads
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return {'data': response.json()}
```

### Start Workers
```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration

with TaskHandler(
    configuration=Configuration(),
    scan_for_annotated_workers=True,
    import_modules=['my_app.workers']
) as handler:
    handler.start_processes()
    handler.join_processes()
```

---

## Worker Execution

Execution mode is **automatically detected** based on function signature:

### Sync Workers (`def`)
- Execute in ThreadPoolExecutor (thread pool)
- Best for: CPU-bound tasks, blocking I/O
- Concurrency: Limited by `thread_count`

### Async Workers (`async def`)
- Execute as non-blocking coroutines in BackgroundEventLoop
- Best for: I/O-bound tasks (HTTP, DB, file operations)
- Concurrency: 10-100x better than sync workers
- Automatic: No configuration needed
- **Can return `None`**: Async tasks can legitimately return `None` as their result

**Key Benefits:**
- **BackgroundEventLoop**: Singleton per process, 1.5-2x faster than `asyncio.run()`
- **Shared Loop**: All async workers in same process share event loop
- **Memory Efficient**: ~3-6 MB per process (regardless of async worker count)
- **Non-Blocking**: Worker continues polling while async tasks execute concurrently
- **Accurate Timing**: Execution time measured from submission to actual completion

**Implementation Details:**
```python
# Async task submission (returns sentinel, not None)
@worker_task(task_definition_name='fetch_data')
async def fetch_data(url: str) -> dict:
    response = await http_client.get(url)
    return response.json()

# Can also return None explicitly
@worker_task(task_definition_name='log_event')
async def log_event(event: str) -> None:
    await logger.log(event)
    return None  # This works correctly!

# Or no return statement (implicit None)
@worker_task(task_definition_name='notify')
async def notify(message: str):
    await send_notification(message)
    # Implicit None return - works correctly!
```

**Flow:**
1. Worker detects coroutine and submits to BackgroundEventLoop
2. Returns sentinel value (`ASYNC_TASK_RUNNING`) to indicate "running in background"
3. Thread completes immediately, freeing up worker slot
4. Async task runs in background event loop
5. When complete, result is collected (can be `None`, dict, etc.)
6. TaskResult sent to Conductor with actual execution time

---

## Configuration

### Hierarchy (highest priority first)
1. Worker-specific env: `conductor.worker.<worker_name>.<property>`
2. Global env: `conductor.worker.all.<property>`
3. Code: `@worker_task(property=value)`

### Supported Properties
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `poll_interval_millis` | int | 100 | Polling interval (ms) |
| `thread_count` | int | 1 | Concurrent tasks (sync) or concurrency limit (async) |
| `domain` | str | None | Worker domain |
| `worker_id` | str | auto | Worker identifier |
| `poll_timeout` | int | 100 | Poll timeout (ms) |
| `lease_extend_enabled` | bool | True | Auto-extend lease |
| `register_task_def` | bool | False | Auto-register task |

### Examples

**Code:**
```python
@worker_task(
    task_definition_name='process_order',
    poll_interval_millis=1000,
    thread_count=5,
    domain='dev'
)
def process_order(order_id: str): pass
```

**Environment Variables:**
```bash
# Global
export conductor.worker.all.domain=production
export conductor.worker.all.thread_count=20

# Worker-specific (overrides global)
export conductor.worker.process_order.thread_count=50
```

**Result:** `domain=production`, `thread_count=50`

---

## Worker Discovery

### Auto-Discovery
```python
# Option 1: TaskHandler auto-discovery
handler = TaskHandler(
    configuration=config,
    scan_for_annotated_workers=True,
    import_modules=['my_app.workers']
)

# Option 2: Explicit WorkerLoader
from conductor.client.worker.worker_loader import auto_discover_workers
loader = auto_discover_workers(packages=['my_app.workers'])
handler = TaskHandler(configuration=config)
```

### WorkerLoader API
```python
from conductor.client.worker.worker_loader import WorkerLoader

loader = WorkerLoader()
loader.scan_packages(['my_app.workers', 'shared.workers'])
loader.scan_module('my_app.workers.order_tasks')
loader.scan_path('/app/workers', package_prefix='my_app.workers')

workers = loader.get_workers()
print(f"Found {len(workers)} workers")
```

---

## Metrics & Monitoring

The SDK provides comprehensive Prometheus metrics collection with two deployment modes:

### Configuration

**HTTP Mode (Recommended - Metrics served from memory):**
```python
from conductor.client.configuration.settings.metrics_settings import MetricsSettings

metrics_settings = MetricsSettings(
    directory="/tmp/conductor-metrics",  # .db files for multiprocess coordination
    update_interval=0.1,                 # Update every 100ms
    http_port=8000                       # Expose metrics via HTTP
)

with TaskHandler(
    configuration=config,
    metrics_settings=metrics_settings
) as handler:
    handler.start_processes()
```

**File Mode (Metrics written to file):**
```python
metrics_settings = MetricsSettings(
    directory="/tmp/conductor-metrics",
    file_name="metrics.prom",
    update_interval=1.0,
    http_port=None  # No HTTP server - write to file instead
)
```

### Modes

| Mode | HTTP Server | File Writes | Use Case |
|------|-------------|-------------|----------|
| HTTP (`http_port` set) | ✅ Built-in | ❌ Disabled | Prometheus scraping, production |
| File (`http_port=None`) | ❌ Disabled | ✅ Enabled | File-based monitoring, testing |

**HTTP Mode Benefits:**
- Metrics served directly from memory (no file I/O)
- Built-in HTTP server with `/metrics` and `/health` endpoints
- Automatic aggregation across worker processes (no PID labels)
- Ready for Prometheus scraping out-of-the-box

### Key Metrics

**Task Metrics:**
- `task_poll_time_seconds{taskType,quantile}` - Poll latency (includes batch polling)
- `task_execute_time_seconds{taskType,quantile}` - Actual execution time (async tasks: from submission to completion)
- `task_execute_error_total{taskType,exception}` - Execution errors by type
- `task_poll_total{taskType}` - Total poll count
- `task_result_size_bytes{taskType,quantile}` - Task output size

**API Metrics:**
- `http_api_client_request{method,uri,status,quantile}` - API request latency
- `http_api_client_request_count{method,uri,status}` - Request count by endpoint
- `http_api_client_request_sum{method,uri,status}` - Total request time

**Labels:**
- `taskType`: Task definition name
- `method`: HTTP method (GET, POST, PUT)
- `uri`: API endpoint path
- `status`: HTTP status code
- `exception`: Exception type (for errors)
- `quantile`: 0.5, 0.75, 0.9, 0.95, 0.99

**Important Notes:**
- **No PID labels**: Metrics are automatically aggregated across processes
- **Async execution time**: Includes actual execution time, not just coroutine submission time
- **Multiprocess safe**: Uses SQLite .db files in `directory` for coordination

### Prometheus Integration

**Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'conductor-workers'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
```

**Accessing Metrics:**
```bash
# Metrics endpoint
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health

# Watch specific metric
watch -n 1 'curl -s http://localhost:8000/metrics | grep task_execute_time_seconds'
```

**PromQL Examples:**
```promql
# Average execution time
rate(task_execute_time_seconds_sum[5m]) / rate(task_execute_time_seconds_count[5m])

# Success rate
sum(rate(task_execute_time_seconds_count{status="SUCCESS"}[5m])) / sum(rate(task_execute_time_seconds_count[5m]))

# p95 latency
task_execute_time_seconds{quantile="0.95"}

# Error rate
sum(rate(task_execute_error_total[5m])) by (taskType)
```

---

## Polling Loop

### Implementation
```python
def run_once(self):
    # Check completed async tasks (non-blocking)
    check_completed_async_tasks()

    # Cleanup completed tasks
    cleanup_completed_tasks()

    # Check capacity
    if running_tasks + pending_async >= thread_count:
        time.sleep(0.001)
        return

    # Adaptive backoff when empty
    if consecutive_empty_polls > 0:
        delay = min(0.001 * (2 ** consecutive_empty_polls), poll_interval)
        # apply delay

    # Batch poll
    tasks = batch_poll(available_slots)

    if tasks:
        for task in tasks:
            executor.submit(execute_and_update, task)
        consecutive_empty_polls = 0
    else:
        consecutive_empty_polls += 1
```

### Optimizations
- **Immediate cleanup:** Completed tasks removed immediately
- **Adaptive backoff:** 1ms → 2ms → 4ms → 8ms → poll_interval
- **Batch polling:** ~65% API call reduction
- **Non-blocking checks:** Async results checked without waiting

---

## Best Practices

### Worker Selection
```python
# CPU-bound
@worker_task(thread_count=4)
def cpu_task(): pass

# I/O-bound sync
@worker_task(thread_count=20)
def io_sync(): pass

# I/O-bound async (automatic high concurrency)
@worker_task(thread_count=50)
async def io_async(): pass
```

### Configuration
```bash
# Development
export conductor.worker.all.domain=dev
export conductor.worker.all.poll_interval_millis=1000

# Production
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval_millis=250
export conductor.worker.all.thread_count=20
```

### Long-Running Tasks
```python
@worker_task(
    task_definition_name='long_task',
    lease_extend_enabled=True  # Prevents timeout
)
def long_task():
    time.sleep(300)  # 5 minutes
```

---

## Event-Driven Interceptors

The SDK uses a fully event-driven architecture for observability, metrics collection, and custom monitoring. All metrics are collected through event listeners, making the system extensible and decoupled from worker logic.

### Overview

**Architecture:**
```
Worker Execution → Event Publishing → Multiple Listeners
                                     ├─ MetricsCollector (Prometheus)
                                     ├─ Custom Monitoring
                                     └─ Audit Logging
```

**Key Features:**
- **Fully Decoupled**: Zero coupling between worker logic and observability
- **Event-Driven Metrics**: Prometheus metrics collected via event listeners
- **Synchronous Events**: Events published synchronously (no async overhead)
- **Extensible**: Add custom listeners without SDK changes
- **Multiple Backends**: Support Prometheus, Datadog, CloudWatch simultaneously

**How Metrics Work:**
The built-in `MetricsCollector` is implemented as an event listener that responds to task execution events. When you enable metrics, it's automatically registered as a listener.

### Event Types

**Task Runner Events:**
- `PollStarted(task_type, worker_id, poll_count)` - When batch poll starts
- `PollCompleted(task_type, duration_ms, tasks_received)` - When batch poll succeeds
- `PollFailure(task_type, duration_ms, cause)` - When batch poll fails
- `TaskExecutionStarted(task_type, task_id, worker_id, workflow_instance_id)` - When task execution begins
- `TaskExecutionCompleted(task_type, task_id, worker_id, workflow_instance_id, duration_ms, output_size_bytes)` - When task completes (includes actual async execution time)
- `TaskExecutionFailure(task_type, task_id, worker_id, workflow_instance_id, cause, duration_ms)` - When task fails

**Event Properties:**
- All events are dataclasses with type hints
- `duration_ms`: Actual execution time (for async tasks: from submission to completion)
- `output_size_bytes`: Size of task result payload
- `poll_count`: Number of tasks requested in batch poll

### Basic Usage

```python
from conductor.client.event.task_runner_events import TaskRunnerEventsListener, TaskExecutionCompleted

class CustomMonitor(TaskRunnerEventsListener):
    def on_task_execution_completed(self, event: TaskExecutionCompleted):
        print(f"Task {event.task_id} completed in {event.duration_ms}ms")
        print(f"Output size: {event.output_size_bytes} bytes")

# Register with TaskHandler
handler = TaskHandler(
    configuration=config,
    event_listeners=[CustomMonitor()]
)
```

**Built-in Metrics Listener:**
```python
# MetricsCollector is automatically registered when metrics_settings is provided
handler = TaskHandler(
    configuration=config,
    metrics_settings=MetricsSettings(http_port=8000)  # MetricsCollector auto-registered
)
```

### Advanced Examples

**SLA Monitoring:**
```python
class SLAMonitor(TaskRunnerEventsListener):
    def __init__(self, threshold_ms: float):
        self.threshold_ms = threshold_ms

    def on_task_execution_completed(self, event: TaskExecutionCompleted):
        if event.duration_ms > self.threshold_ms:
            alert(f"SLA breach: {event.task_type} took {event.duration_ms}ms")
```

**Cost Tracking:**
```python
class CostTracker(TaskRunnerEventsListener):
    def __init__(self, cost_per_second: dict):
        self.cost_per_second = cost_per_second
        self.total_cost = 0.0

    def on_task_execution_completed(self, event: TaskExecutionCompleted):
        rate = self.cost_per_second.get(event.task_type, 0.0)
        cost = rate * (event.duration_ms / 1000.0)
        self.total_cost += cost
```

**Multiple Listeners:**
```python
handler = TaskHandler(
    configuration=config,
    event_listeners=[
        PrometheusMetricsCollector(),
        SLAMonitor(threshold_ms=5000),
        CostTracker(cost_per_second={'ml_task': 0.05}),
        CustomAuditLogger()
    ]
)
```

### Benefits

- **Performance**: Synchronous event publishing (minimal overhead)
- **Error Isolation**: Listener failures don't affect worker execution
- **Flexibility**: Implement only the events you need
- **Type Safety**: Protocol-based with full type hints
- **Metrics Integration**: Built-in Prometheus metrics via `MetricsCollector` listener

**Implementation:**
- Events are published synchronously (not async)
- `SyncEventDispatcher` used for task runner events
- All metrics collected through event listeners
- Zero coupling between worker logic and observability

---

## Troubleshooting

### High Memory
**Cause:** Too many worker processes
**Fix:** Increase `thread_count` per worker, reduce worker count

### Async Tasks Not Running Concurrently
**Cause:** Function defined as `def` instead of `async def`
**Fix:** Change function signature to `async def` to enable automatic async execution

### Async Task Execution Time Shows 0ms
**Cause:** Old SDK version that measured submission time instead of actual execution time
**Fix:** Upgrade to SDK 1.2.6+ which correctly measures async task execution time from submission to completion

### Async Task Returns None Not Working
**Issue:** SDK version < 1.2.6 couldn't distinguish between "task submitted" and "task returned None"
**Fix:** Upgrade to SDK 1.2.6+ which uses sentinel pattern (`ASYNC_TASK_RUNNING`) to allow async tasks to return `None`

### Tasks Not Picked Up
**Check:**
1. Domain: `export conductor.worker.all.domain=production`
2. Worker registered: `loader.print_summary()`
3. Not paused: `export conductor.worker.my_task.paused=false`

### Timeouts
**Fix:** Enable lease extension or increase task timeout in Conductor

### Empty Metrics
**Check:**
1. `metrics_settings` passed to TaskHandler
2. Workers actually executing tasks
3. Directory has write permissions

---

## Implementation Files

**Core:**
- `src/conductor/client/automator/task_handler.py` - Orchestrator
- `src/conductor/client/automator/task_runner.py` - Polling loop
- `src/conductor/client/worker/worker.py` - Worker + BackgroundEventLoop
- `src/conductor/client/worker/worker_task.py` - @worker_task decorator
- `src/conductor/client/worker/worker_config.py` - Config resolution
- `src/conductor/client/worker/worker_loader.py` - Discovery
- `src/conductor/client/telemetry/metrics_collector.py` - Metrics

**Examples:**
- `examples/asyncio_workers.py`
- `examples/compare_multiprocessing_vs_asyncio.py`
- `examples/worker_configuration_example.py`

---

**Issues:** https://github.com/conductor-oss/conductor-python/issues
