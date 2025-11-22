# Worker Design & Implementation

**Version:** 3.1 | **Date:** 2025-01-21 | **SDK:** 1.2.6+

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

**Key Benefits:**
- **BackgroundEventLoop**: Singleton per process, 1.5-2x faster than `asyncio.run()`
- **Shared Loop**: All async workers in same process share event loop
- **Memory Efficient**: ~3-6 MB per process (regardless of async worker count)
- **Non-Blocking**: Worker continues polling while async tasks execute concurrently

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

### Configuration
```python
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
import os, shutil

# Clean metrics directory
metrics_dir = '/path/to/metrics'
if os.path.exists(metrics_dir):
    shutil.rmtree(metrics_dir)
os.makedirs(metrics_dir, exist_ok=True)

metrics_settings = MetricsSettings(
    directory=metrics_dir,
    file_name='conductor_metrics.prom',
    update_interval=10
)

with TaskHandler(
    configuration=config,
    metrics_settings=metrics_settings
) as handler:
    handler.start_processes()
```

### Key Metrics

**Task Metrics:**
- `task_poll_time_seconds{taskType,status,quantile}` - Poll latency
- `task_execute_time_seconds{taskType,status,quantile}` - Execution time
- `task_execute_error_total{taskType,exception}` - Errors
- `task_execution_queue_full_total{taskType}` - Queue saturation

**API Metrics:**
- `api_request_time_seconds{method,uri,status,quantile}` - API latency
- `api_request_time_seconds_count{method,uri,status}` - Request count

**Labels:**
- `status`: SUCCESS, FAILURE
- `quantile`: 0.5, 0.75, 0.9, 0.95, 0.99

### Prometheus Integration

**HTTP Server:**
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

class MetricsHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            with open('/path/to/conductor_metrics.prom', 'rb') as f:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.end_headers()
                self.wfile.write(f.read())

threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8000), MetricsHandler).serve_forever(), daemon=True).start()
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

The SDK includes an event-driven interceptor system for observability, metrics collection, and custom monitoring without modifying core worker logic.

### Overview

**Architecture:**
```
Worker Execution → Event Publishing → Multiple Listeners
                                     ├─ Prometheus Metrics
                                     ├─ Custom Monitoring
                                     └─ Audit Logging
```

**Key Features:**
- **Decoupled**: Observability separate from business logic
- **Async**: Non-blocking event publishing
- **Extensible**: Add custom listeners without SDK changes
- **Multiple Backends**: Support Prometheus, Datadog, CloudWatch simultaneously

### Event Types

**Task Runner Events:**
- `PollStarted`, `PollCompleted`, `PollFailure`
- `TaskExecutionStarted`, `TaskExecutionCompleted`, `TaskExecutionFailure`

**Workflow Events:**
- `WorkflowStarted`, `WorkflowInputSize`, `WorkflowPayloadUsed`

**Task Client Events:**
- `TaskPayloadUsed`, `TaskResultSize`

### Basic Usage

```python
from conductor.client.events.listeners import TaskRunnerEventsListener
from conductor.client.events.task_runner_events import *

class CustomMonitor(TaskRunnerEventsListener):
    def on_task_execution_completed(self, event: TaskExecutionCompleted):
        print(f"Task {event.task_id} completed in {event.duration_ms}ms")

# Register with TaskHandler
handler = TaskHandler(
    configuration=config,
    event_listeners=[CustomMonitor()]
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

- **Performance**: Non-blocking async event publishing (<5μs overhead)
- **Error Isolation**: Listener failures don't affect worker execution
- **Flexibility**: Implement only the events you need
- **Type Safety**: Protocol-based with full type hints

**See:** `docs/design/event_driven_interceptor_system.md` for complete architecture and implementation details.

---

## Troubleshooting

### High Memory
**Cause:** Too many worker processes
**Fix:** Increase `thread_count` per worker, reduce worker count

### Async Tasks Not Running Concurrently
**Cause:** Function defined as `def` instead of `async def`
**Fix:** Change function signature to `async def` to enable automatic async execution

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
