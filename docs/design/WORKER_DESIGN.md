# Worker Design & Implementation

**Version:** 4.1 | **Date:** 2025-11-28 | **SDK:** 1.3.0+

**Recent Updates (v4.0):**
- ✅ **AsyncTaskRunner**: Pure async/await execution (zero thread overhead for async workers)
- ✅ **Auto-Detection**: Automatic runner selection based on `def` vs `async def`
- ✅ **Async HTTP**: `httpx.AsyncClient` for non-blocking poll/update operations
- ✅ **Direct Execution**: `await worker_fn()` - no thread context switches
- ✅ **Process Isolation**: One process per worker, clients created after fork
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
    # Higher concurrency for I/O-bound workloads
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

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Main Process: TaskHandler                           │
│  • Discovers workers (@worker_task decorator)                               │
│  • Auto-detects sync (def) vs async (async def)                             │
│  • Spawns one Process per worker                                            │
│  • Manages worker lifecycle                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────────┐  ┌───────────────────────┐  ┌──────────────────────┐
│   Process 1          │  │  Process 2            │  │  Process 3           │
│   Worker: fetch_data │  │  Worker: process_cpu  │  │  Worker: send_email  │
│   Type: async def    │  │  Type: def            │  │  Type: async def     │
├──────────────────────┤  ├───────────────────────┤  ├──────────────────────┤
│                      │  │                       │  │                      │
│  AsyncTaskRunner     │  │  TaskRunner           │  │  AsyncTaskRunner     │
│  ┌────────────────┐  │  │  ┌────────────────┐   │  │  ┌────────────────┐  │
│  │  Event Loop    │  │  │  │ ThreadPool     │   │  │  │  Event Loop    │  │
│  │  (asyncio)     │  │  │  │ (thread_count) │   │  │  │  (asyncio)     │  │
│  └────────────────┘  │  │  └────────────────┘   │  │  └────────────────┘  │
│         │            │  │         │             │  │         │            │
│         │ Polling    │  │         │ Polling     │  │         │ Polling    │
│         ▼            │  │         ▼             │  │         ▼            │
│  ┌────────────────┐  │  │  ┌────────────────┐   │  │  ┌────────────────┐  │
│  │ async def poll │  │  │  │  Sync poll     │   │  │  │ async def poll │  │
│  │ (httpx.Async)  │  │  │  │  (requests)    │   │  │  │ (httpx.Async)  │  │
│  └────────────────┘  │  │  └────────────────┘   │  │  └────────────────┘  │
│         │            │  │         │             │  │         │            │
│         ▼            │  │         ▼             │  │         ▼            │
│  ┌────────────────┐  │  │  ┌────────────────┐   │  │  ┌────────────────┐  │
│  │await worker_fn │  │  │  │executor.submit │   │  │  │await worker_fn │  │
│  │   (direct!)    │  │  │  │  worker_fn()   │   │  │  │   (direct!)    │  │
│  └────────────────┘  │  │  └────────────────┘   │  │  └────────────────┘  │
│         │            │  │         │             │  │         │            │
│    Semaphore         │  │  Executor Capacity    │  │    Semaphore         │
│  (limits execution)  │  │  (limits execution)   │  │  (limits execution)  │
│         │            │  │         │             │  │         │            │
│         ▼            │  │         ▼             │  │         ▼            │
│  ┌────────────────┐  │  │  ┌────────────────┐   │  │  ┌────────────────┐  │
│  │async def update│  │  │  │  Sync update   │   │  │  │async def update│  │
│  │ (httpx.Async)  │  │  │  │  (requests)    │   │  │  │ (httpx.Async)  │  │
│  └────────────────┘  │  │  └────────────────┘   │  │  └────────────────┘  │
│                      │  │                       │  │                      │
│  Threads: 1          │  │  Threads: 1+N         │  │  Threads: 1          │
│  Concurrency: High   │  │  Concurrency: N       │  │  Concurrency: High   │
└──────────────────────┘  └───────────────────────┘  └──────────────────────┘

Legend:
├─ Process boundary (isolation)
│  ├─ AsyncTaskRunner: Pure async/await, single event loop
│  └─ TaskRunner: Thread pool executor
└─ Auto-selected based on function signature (def vs async def)
```

## Worker Execution

Execution mode is **automatically detected** based on function signature:

### Sync Workers (`def`) → TaskRunner
- Execute in ThreadPoolExecutor (thread pool)
- Uses `TaskRunner` for polling/execution
- Blocking poll/update (requests library)
- Best for: CPU-bound tasks, blocking I/O
- Concurrency: Limited by `thread_count` (number of threads)
- Threads: 1 (main) + thread_count (pool)

### Async Workers (`async def`) → AsyncTaskRunner
- Execute directly in async event loop (pure async/await)
- Uses `AsyncTaskRunner` for polling/execution
- Non-blocking poll/update (httpx.AsyncClient)
- Best for: I/O-bound tasks (HTTP, DB, file operations)
- Concurrency: Higher than sync workers for I/O-bound workloads
- Automatic: No configuration needed
- Threads: 1 (event loop only)
- **Can return `None`**: Async tasks can legitimately return `None` as their result

**Key Benefits of AsyncTaskRunner:**
- **Zero Thread Overhead**: Single event loop per process (no ThreadPoolExecutor, no BackgroundEventLoop)
- **Direct Execution**: `await worker_fn()` - no thread context switches
- **Async HTTP**: Uses `httpx.AsyncClient` for non-blocking polling/updates
- **Memory Efficient**: Lower memory footprint per process
- **High Concurrency**: Up to `thread_count` tasks running concurrently via `asyncio.gather()`
- **Accurate Timing**: Execution time measured from start to completion

**Implementation Details:**
```python
# Async worker - automatically uses AsyncTaskRunner
@worker_task(task_definition_name='fetch_data', thread_count=50)
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
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

**Async Flow (AsyncTaskRunner):**
1. TaskHandler detects `async def` worker function
2. Creates `AsyncTaskRunner` instead of `TaskRunner`
3. Process runs `asyncio.run(async_task_runner.run())`
4. Single event loop handles: async poll → async execute → async update
5. Up to `thread_count` tasks run concurrently via `asyncio.gather()`
6. No thread context switches - pure async/await

**Sync Flow (TaskRunner):**
1. TaskHandler detects `def` worker function
2. Creates `TaskRunner` (existing behavior)
3. Process runs thread-based polling/execution
4. Works exactly as before (backward compatible)

---

## AsyncTaskRunner Architecture

### **Design Goals**

The AsyncTaskRunner eliminates thread overhead for async workers by using pure async/await execution:

**Problem with BackgroundEventLoop approach:**
```
Main Thread → polls (blocking httpx.Client)
  → ThreadPoolExecutor thread → detects coroutine
    → BackgroundEventLoop thread → runs async task
```
**Thread count**: 3 threads + 5+ context switches per task

**Solution with AsyncTaskRunner:**
```
Single Event Loop → await async_poll()
  → await async_execute()  (direct!)
    → await async_update()
```
**Thread count**: 1 thread (event loop) + 0 context switches

### **Key Implementation Details**

#### **1. Auto-Detection in TaskHandler**
```python
# task_handler.py:272
is_async_worker = inspect.iscoroutinefunction(worker.execute_function)

if is_async_worker:
    async_task_runner = AsyncTaskRunner(...)
    process = Process(target=self.__run_async_runner, args=(async_task_runner,))
else:
    task_runner = TaskRunner(...)
    process = Process(target=task_runner.run)
```

**User Impact**: None - completely transparent

#### **2. Client Creation After Fork**
```python
# async_task_runner.py:107
async def run(self):
    # Create async HTTP client in subprocess (after fork)
    # httpx.AsyncClient is not picklable, so we defer creation
    self.async_api_client = AsyncApiClient(...)
    self.async_task_client = AsyncTaskResourceApi(...)

    # Create semaphore in event loop
    self._semaphore = asyncio.Semaphore(self._max_workers)
```

**Why**: `httpx.AsyncClient` and `asyncio.Semaphore` are not picklable and must be created in the subprocess

#### **3. Direct Async Execution**
```python
# async_task_runner.py:364
async def __async_execute_task(self, task: Task):
    # Get worker parameters
    task_input = {...}

    # Direct await - NO threads, NO BackgroundEventLoop!
    task_output = await self.worker.execute_function(**task_input)

    # Build TaskResult
    return task_result
```

**Benefit**: Zero thread overhead, direct coroutine execution

#### **4. Concurrency Control & Batch Polling**

**Both TaskRunner and AsyncTaskRunner use dynamic batch polling:**

```python
# Calculate available slots (both runners)
current_capacity = len(self._running_tasks)  # + pending_async for TaskRunner
available_slots = self._max_workers - current_capacity

# Batch poll with dynamic count (both runners)
tasks = batch_poll(available_slots)  # or await async_batch_poll(available_slots)

# As tasks complete, available_slots increases
# As new tasks are polled, available_slots decreases
```

**TaskRunner - ThreadPoolExecutor limits concurrency:**
```python
# Capacity controlled by executor + tracking
for task in tasks:
    future = self._executor.submit(execute_and_update, task)
    self._running_tasks.add(future)  # Track futures
# ThreadPoolExecutor queues excess tasks automatically
```

**AsyncTaskRunner - Semaphore limits execution:**
```python
# Capacity controlled by tracking + semaphore during execution
for task in tasks:
    asyncio_task = asyncio.create_task(execute_and_update(task))
    self._running_tasks.add(asyncio_task)  # Track asyncio tasks

# Inside execute_and_update:
async def __async_execute_and_update_task(self, task):
    async with self._semaphore:  # Limit to thread_count concurrent
        task_result = await self.__async_execute_task(task)
        await self.__async_update_task(task_result)
```

**Key Insight**: Both use the same batch polling logic with dynamic capacity calculation. The difference is in how concurrency is limited:
- TaskRunner: ThreadPoolExecutor naturally limits concurrent threads
- AsyncTaskRunner: Semaphore explicitly limits concurrent executions

**Semantics**: `thread_count` means "max concurrent executions" in both models

#### **5. Task Tracking**
```python
# async_task_runner.py:184
asyncio_task = asyncio.create_task(self.__async_execute_and_update_task(task))
self._running_tasks.add(asyncio_task)
asyncio_task.add_done_callback(self._running_tasks.discard)  # Auto-cleanup
```

**Benefit**: Automatic cleanup, no manual tracking needed

### **Performance Comparison**

| Metric | TaskRunner (Async) | AsyncTaskRunner | Notes |
|--------|-------------------|-----------------|-------|
| Threads per worker | 3 (main + pool + event loop) | 1 (event loop only) | Fewer threads |
| Context switches/task | 5+ | 0 | No context switches |
| Latency overhead | Thread context switches | Direct await | Lower latency |
| Throughput (I/O) | Limited by threads | Limited by event loop | Higher for I/O workloads |

### **Feature Parity**

AsyncTaskRunner has **100% feature parity** with TaskRunner:

| Feature | TaskRunner | AsyncTaskRunner | Notes |
|---------|-----------|-----------------|-------|
| Batch polling | ✅ | ✅ | Uses `AsyncTaskResourceApi` |
| Token refresh | ✅ | ✅ | Identical logic with backoff |
| Event publishing | ✅ | ✅ | All 6 events, same timing |
| Metrics collection | ✅ | ✅ | Via event listeners |
| Custom listeners | ✅ | ✅ | Same `event_listeners` param |
| Configuration | ✅ | ✅ | Same 3-tier hierarchy |
| Adaptive backoff | ✅ | ✅ | Same exponential logic |
| Auth backoff | ✅ | ✅ | Same 2^failures logic |
| Capacity limits | ✅ | ✅ | Semaphore vs ThreadPool |
| Task retry | ✅ | ✅ | 4 attempts, 10s/20s/30s |
| Error handling | ✅ | ✅ | Same exception handling |

### **Critical Implementation Notes**

⚠️ **Pickling Constraints**

AsyncTaskRunner defers creation of non-picklable objects until after fork:

```python
# __init__: Set to None (will be pickled)
self.async_api_client = None
self.async_task_client = None
self._semaphore = None

# run(): Create in subprocess
async def run(self):
    # NOW safe to create (after fork, in event loop)
    self.async_api_client = AsyncApiClient(...)
    self._semaphore = asyncio.Semaphore(...)
```

**Objects that CANNOT be pickled:**
- `httpx.AsyncClient` (contains event loop state)
- `asyncio.Semaphore` (tied to specific event loop)
- Any object with async resources

⚠️ **Token Refresh in Async Context**

The sync version calls `__refresh_auth_token()` in `__init__`, but async cannot use `await` in `__init__`. Solution: lazy token fetch on first API call:

```python
# async_api_client.py:640
async def __get_authentication_headers(self):
    if self.configuration.AUTH_TOKEN is None:
        if self.configuration.authentication_settings is None:
            return None
        # Lazy fetch on first call
        token = await self.__get_new_token(skip_backoff=False)
        self.configuration.update_token(token)
```

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
| `lease_extend_enabled` | bool | False | ⚠️ **Not implemented** - use `TaskInProgress` instead |
| `register_task_def` | bool | False | Auto-register task definition with JSON schemas (draft-07) |
| `overwrite_task_def` | bool | True | Overwrite existing task definitions (when register_task_def=True) |
| `strict_schema` | bool | False | Enforce strict schema validation (additionalProperties=false) |
| `paused` | bool | False | Pause worker (env-only, not in decorator) |

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

### Automatic Task Definition Registration

When `register_task_def=True`, the worker automatically registers its task definition with Conductor on startup, including JSON schemas generated from type hints.

**Example:**
```python
from dataclasses import dataclass

@dataclass
class OrderInfo:
    order_id: str
    amount: float
    customer_id: int

@worker_task(
    task_definition_name='process_order',
    register_task_def=True  # Auto-register on startup
)
def process_order(order: OrderInfo, priority: int = 1) -> dict:
    return {'status': 'processed', 'order_id': order.order_id}
```

**What Gets Registered:**

1. **Task Definition**: `process_order`

2. **Input Schema** (`process_order_input`):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "order": {
      "type": "object",
      "properties": {
        "order_id": {"type": "string"},
        "amount": {"type": "number"},
        "customer_id": {"type": "integer"}
      },
      "required": ["order_id", "amount", "customer_id"]
    },
    "priority": {"type": "integer"}
  },
  "required": ["order"]
}
```

3. **Output Schema** (`process_order_output`):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object"
}
```

**Supported Types:**
- Basic: `str`, `int`, `float`, `bool`, `dict`, `list`
- Optional: `Optional[T]`
- Collections: `List[T]`, `Dict[str, T]`
- Dataclasses (with recursive field conversion)
- Union types (filters out TaskInProgress/None for return types)

**Behavior:**
- ✅ Skips if task definition already exists (no overwrite)
- ✅ Skips if schemas already exist (no overwrite)
- ✅ Workers start even if registration fails (just logs warning)
- ✅ Works for both sync and async workers
- ⚠️ Only works for function-based workers (`@worker_task` decorator)
- ⚠️ Class-based workers not supported (no execute_function attribute)

**Environment Override:**
```bash
# Enable for all workers (Unix format - recommended)
export CONDUCTOR_WORKER_ALL_REGISTER_TASK_DEF=true

# Enable for specific worker (Unix format - recommended)
export CONDUCTOR_WORKER_PROCESS_ORDER_REGISTER_TASK_DEF=true

# Control overwrite behavior
export CONDUCTOR_WORKER_ALL_OVERWRITE_TASK_DEF=false  # Don't overwrite existing

# Enable strict schema validation
export CONDUCTOR_WORKER_PROCESS_ORDER_STRICT_SCHEMA=true  # No extra fields allowed

# Alternative: Dot notation (also works)
export conductor.worker.all.register_task_def=true
export conductor.worker.process_order.strict_schema=true
```

### Schema Validation Modes

The `strict_schema` flag controls JSON Schema validation strictness:

**Lenient Mode (default, strict_schema=False):**
```json
{
  "type": "object",
  "properties": {...},
  "additionalProperties": true  ← Extra fields allowed
}
```

**Strict Mode (strict_schema=True):**
```json
{
  "type": "object",
  "properties": {...},
  "additionalProperties": false  ← Extra fields rejected
}
```

**Use Cases:**
- **Lenient (default):** Development, backward compatibility, flexible integrations
- **Strict:** Production, strict validation, contract enforcement

**Example:**
```python
@worker_task(
    task_definition_name='validate_order',
    register_task_def=True,
    strict_schema=True  # Enforce strict validation
)
def validate_order(order_id: str, amount: float) -> dict:
    return {}

# Generated schema will reject inputs with extra fields
```

### Task Definition Overwrite Control

The `overwrite_task_def` flag controls update behavior:

**Overwrite Mode (default, overwrite_task_def=True):**
- Always calls `update_task_def()` (overwrites existing)
- Ensures server has latest configuration from code
- Use in development or when task config changes frequently

**No-Overwrite Mode (overwrite_task_def=False):**
- Checks if task exists first
- Only creates if doesn't exist
- Preserves manual changes on server
- Use when tasks are managed outside code

**Example:**
```python
@worker_task(
    task_definition_name='stable_task',
    register_task_def=True,
    overwrite_task_def=False  # Don't overwrite existing config
)
def stable_worker(data: dict) -> dict:
    return {}

# If task exists on server, keeps existing configuration
# If task doesn't exist, registers new one
```

### Startup Configuration Logging

When workers start, they log their resolved configuration in a compact single-line format:

```
INFO - Conductor Worker[name=process_order, pid=12345, status=active, poll_interval=1000ms, domain=production, thread_count=50, poll_timeout=100ms, lease_extend=false]
```

This shows:
- Worker name and process ID (useful for multi-process debugging)
- Status (active/paused)
- All resolved configuration values
- Configuration source (code, global env, or worker-specific env)

**Benefits:**
- Quick verification of configuration in logs
- Process ID for debugging multi-process issues
- Easy debugging of environment variable issues
- Single-line format for log aggregation tools

**Example logs:**
```
INFO - Conductor Worker[name=greet_sync, pid=63761, status=active, poll_interval=100ms, thread_count=10, poll_timeout=100ms, lease_extend=false]
INFO - Conductor Worker[name=greet_async, pid=63762, status=active, poll_interval=100ms, thread_count=50, poll_timeout=100ms, lease_extend=false]
```

Note: Each worker runs in its own process, so each has a unique PID.

---

## Worker Discovery

Automatic worker discovery from packages, similar to Spring's component scanning in Java.

### Overview

The `WorkerLoader` class provides automatic discovery of workers decorated with `@worker_task` by scanning Python packages. This eliminates the need to manually register each worker.

### Auto-Discovery Methods

**Option 1: TaskHandler auto-discovery (Recommended)**
```python
from conductor.client.automator.task_handler import TaskHandler

handler = TaskHandler(
    configuration=config,
    scan_for_annotated_workers=True,
    import_modules=['my_app.workers', 'my_app.tasks']
)
```

**Option 2: Explicit WorkerLoader**
```python
from conductor.client.worker.worker_loader import auto_discover_workers

# Auto-discover workers from packages
loader = auto_discover_workers(
    packages=['my_app.workers', 'my_app.tasks'],
    print_summary=True
)

# Start task handler with discovered workers
handler = TaskHandler(configuration=config)
```

### WorkerLoader API

```python
from conductor.client.worker.worker_loader import WorkerLoader

loader = WorkerLoader()

# Scan multiple packages (recursive by default)
loader.scan_packages(['my_app.workers', 'shared.workers'])

# Scan specific modules
loader.scan_module('my_app.workers.order_tasks')

# Scan filesystem path
loader.scan_path('/app/workers', package_prefix='my_app.workers')

# Non-recursive scanning
loader.scan_packages(['my_app.workers'], recursive=False)

# Get discovered workers
workers = loader.get_workers()
print(f"Found {len(workers)} workers")

# Print discovery summary
loader.print_summary()
```

### Convenience Functions

```python
from conductor.client.worker.worker_loader import scan_for_workers, auto_discover_workers

# Quick scanning
loader = scan_for_workers('my_app.workers', 'my_app.tasks')

# Auto-discover with summary
loader = auto_discover_workers(
    packages=['my_app.workers'],
    print_summary=True
)
```

### How It Works

1. **Package Scanning**: The loader imports Python packages and modules
2. **Automatic Registration**: `@worker_task` decorators automatically register workers during import
3. **Worker Retrieval**: Loader retrieves registered workers from the global registry
4. **Execution Mode**: Auto-detected from function signature (`def` vs `async def`)

### Best Practices

**1. Organize Workers by Domain**
```
my_app/
├── workers/
│   ├── __init__.py
│   ├── order/          # Order-related workers
│   │   ├── process.py
│   │   └── validate.py
│   ├── payment/        # Payment-related workers
│   │   ├── charge.py
│   │   └── refund.py
│   └── notification/   # Notification workers
│       ├── email.py
│       └── sms.py
```

**2. Environment-Specific Loading**
```python
import os

env = os.getenv('ENV', 'production')

if env == 'production':
    packages = ['my_app.workers']
else:
    packages = ['my_app.workers', 'my_app.test_workers']

loader = auto_discover_workers(packages=packages)
```

**3. Use Package __init__.py Files**
```python
# my_app/workers/__init__.py
"""
Workers package - all worker modules auto-discovered
"""
```

### Troubleshooting

**Workers Not Discovered:**
- Ensure packages have `__init__.py` files
- Check package name is correct
- Verify `@worker_task` decorator is present
- Check for import errors in worker modules

**Import Errors:**
- Verify dependencies are installed
- Check `PYTHONPATH` includes necessary directories
- Look for circular imports

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

### Implementation (Both TaskRunner and AsyncTaskRunner)

**Core polling loop with dynamic batch sizing:**

```python
def run_once(self):
    # 1. Cleanup completed tasks immediately
    cleanup_completed_tasks()  # Removes done futures/asyncio tasks

    # 2. Calculate available capacity dynamically
    current_capacity = len(self._running_tasks)
    if current_capacity >= self._max_workers:
        time.sleep(0.001)  # At capacity, wait briefly
        return

    # 3. Calculate how many tasks we can accept
    available_slots = self._max_workers - current_capacity
    # Example: thread_count=10, running=3 → available_slots=7

    # 4. Adaptive backoff when queue is empty
    if consecutive_empty_polls > 0:
        delay = min(0.001 * (2 ** consecutive_empty_polls), poll_interval)
        # Exponential: 1ms → 2ms → 4ms → 8ms → poll_interval
        if time_since_last_poll < delay:
            time.sleep(delay - time_since_last_poll)
            return

    # 5. Batch poll with available_slots count
    tasks = batch_poll(available_slots)  # Poll up to 7 tasks

    # 6. Submit tasks for execution
    if tasks:
        for task in tasks:
            # TaskRunner: executor.submit() → thread pool
            # AsyncTaskRunner: asyncio.create_task() → event loop
            submit_for_execution(task)
            self._running_tasks.add(task_future)
        consecutive_empty_polls = 0
    else:
        consecutive_empty_polls += 1

    # Loop continues - as tasks complete, available_slots increases
```

### Key Optimizations

**Dynamic Batch Sizing:**
- Batch size = `thread_count - currently_running`
- Automatically adjusts as tasks complete
- Prevents over-polling (respects capacity)
- Example flow with thread_count=10:
  ```
  Poll 1: running=0  → batch_poll(10) → get 10 tasks
  Poll 2: running=10 → skip (at capacity)
  Poll 3: running=7  → batch_poll(3)  → get 3 tasks
  Poll 4: running=2  → batch_poll(8)  → get 8 tasks
  ```

**Other Optimizations:**
- **Immediate cleanup:** Completed tasks removed immediately for accurate capacity
- **Adaptive backoff:** Exponential backoff when queue empty (1ms → 2ms → 4ms → poll_interval)
- **Batch polling:** significant API call reduction vs polling one at a time
- **Non-blocking checks:** Fast capacity calculation (no locks needed)

---

## Best Practices

### Worker Selection

**Choose the right execution mode based on workload:**

```python
# CPU-bound: Use sync workers with low thread_count
# (Python GIL limits CPU parallelism, use multiple processes instead)
@worker_task(task_definition_name='compute_task', thread_count=4)
def cpu_task(data: list) -> dict:
    result = expensive_computation(data)  # CPU-intensive
    return {'result': result}

# I/O-bound sync: Use sync workers with higher thread_count
# (Blocking I/O: file reads, subprocess calls, legacy libraries)
@worker_task(task_definition_name='file_task', thread_count=20)
def io_sync(file_path: str) -> dict:
    with open(file_path) as f:  # Blocking I/O
        data = f.read()
    return {'data': data}

# I/O-bound async: Use async workers with high concurrency
# (Non-blocking I/O: HTTP, database, async file I/O)
# ✅ RECOMMENDED for HTTP/API calls, database queries
@worker_task(task_definition_name='api_task', thread_count=50)
async def io_async(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)  # Non-blocking I/O
    return {'data': response.json()}

# Mixed workload: Use async with moderate concurrency
@worker_task(task_definition_name='mixed_task', thread_count=10)
async def mixed_task(url: str) -> dict:
    # Async I/O
    async with httpx.AsyncClient() as client:
        data = await client.get(url)
    # Some CPU work (still runs in event loop)
    processed = process_data(data.json())
    return {'result': processed}
```

**Performance Guidelines:**

| Workload | Worker Type | thread_count | Runner | Expected Throughput |
|----------|------------|--------------|--------|-------------------|
| CPU-bound | `def` | 1-4 | TaskRunner | Limited by GIL |
| I/O-bound sync | `def` | 10-50 | TaskRunner | Moderate |
| I/O-bound async | `async def` | 50-200 | AsyncTaskRunner | High |

### Configuration

```bash
# Development
export conductor.worker.all.domain=dev
export conductor.worker.all.poll_interval_millis=1000

# Production - Sync Workers
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval_millis=250
export conductor.worker.all.thread_count=20

# Production - Async Workers
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval_millis=100  # Lower for async (less overhead)
export conductor.worker.my_async_task.thread_count=100  # Higher concurrency
```

### Long-Running Tasks & Lease Extension

Task lease extension allows long-running tasks to maintain ownership and prevent timeouts during execution. When a worker polls a task, it receives a "lease" with a timeout period (defined by `responseTimeoutSeconds` in task definition).

**⚠️ Important**: Currently, only **manual lease extension** via `TaskInProgress` is implemented. The `lease_extend_enabled` configuration parameter exists but is **not yet implemented** - no automatic lease extension occurs.

**Manual Lease Extension with TaskInProgress:**

To extend a task lease, explicitly return `TaskInProgress`:
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

**Polling External Systems:**
```python
@worker_task(task_definition_name='wait_for_approval')
def wait_for_approval(request_id: str) -> Union[dict, TaskInProgress]:
    approval_status = check_approval_system(request_id)

    if approval_status == 'PENDING':
        # Still waiting - extend lease
        return TaskInProgress(
            callback_after_seconds=30,
            output={'status': 'waiting'}
        )
    elif approval_status == 'APPROVED':
        return {'status': 'approved'}
    else:
        raise Exception(f"Request rejected: {approval_status}")
```

**Task Definition Requirements:**

Configure appropriate timeouts in your task definition:
```json
{
  "name": "long_processing_task",
  "responseTimeoutSeconds": 300,  // 5 min per execution (before returning TaskInProgress)
  "timeoutSeconds": 3600,         // 1 hour total timeout (all iterations combined)
  "timeoutPolicy": "RETRY",
  "retryCount": 3
}
```

**Key Points:**
- ⚠️ `lease_extend_enabled` parameter exists but is **NOT implemented** - has no effect
- **Manual lease extension only**: Must return `TaskInProgress` to extend lease
- `responseTimeoutSeconds`: How long worker has before returning result/TaskInProgress
- `timeoutSeconds`: Total allowed time (all TaskInProgress callbacks combined)
- Use `TaskInProgress` for checkpointing and progress tracking
- Monitor `poll_count` to prevent infinite loops
- Set `responseTimeoutSeconds` based on your typical TaskInProgress interval

### Choosing thread_count

**For Sync Workers (TaskRunner):**
- `thread_count` = size of ThreadPoolExecutor
- Each task consumes one thread
- Recommendation: 1-4 for CPU, 10-50 for I/O

**For Async Workers (AsyncTaskRunner):**
- `thread_count` = max concurrent async tasks (semaphore limit)
- All tasks share one event loop thread
- Recommendation: 50-200 for I/O workloads
- Higher values possible (event loop handles thousands of concurrent coroutines)

**Example:**
```python
# Async worker with 100 concurrent tasks
@worker_task(task_definition_name='api_calls', thread_count=100)
async def make_api_call(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()

# Only 1 thread (event loop) handles all 100 concurrent tasks!
# vs TaskRunner: would need 100 threads
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
- `TaskUpdateFailure(task_type, task_id, worker_id, workflow_instance_id, cause, retry_count, task_result)` - **Critical!** When task update fails after all retries (4 attempts with 10s/20s/30s backoff)

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

### Update Retry Logic & Failure Handling

**Critical: Task updates are retried with exponential backoff**

Both TaskRunner and AsyncTaskRunner implement robust retry logic for task updates:

**Retry Configuration:**
- **4 attempts total** (0, 1, 2, 3)
- **Exponential backoff**: 10s, 20s, 30s between retries
- **Idempotent**: Safe to retry updates
- **Event on final failure**: `TaskUpdateFailure` published

**Why This Matters:**
Task updates are **critical** - if a worker executes a task successfully but fails to update Conductor, the task result is lost. The retry logic ensures maximum reliability.

**Handling Update Failures:**
```python
class UpdateFailureHandler(TaskRunnerEventsListener):
    """Handle critical update failures after all retries exhausted."""

    def on_task_update_failure(self, event: TaskUpdateFailure):
        # CRITICAL: Task was executed but Conductor doesn't know!
        # External intervention required

        # Option 1: Alert operations team
        send_pagerduty_alert(
            f"CRITICAL: Task update failed after {event.retry_count} attempts",
            task_id=event.task_id,
            workflow_id=event.workflow_instance_id
        )

        # Option 2: Log to external storage for recovery
        backup_db.save_task_result(
            task_id=event.task_id,
            result=event.task_result,  # Contains the actual result that was lost
            timestamp=event.timestamp,
            error=str(event.cause)
        )

        # Option 3: Attempt custom recovery
        try:
            # Custom retry logic with different strategy
            custom_update_service.update_task_with_custom_retry(event.task_result)
        except Exception as e:
            logger.critical(f"Recovery failed: {e}")

# Register handler
handler = TaskHandler(
    configuration=config,
    event_listeners=[UpdateFailureHandler()]
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
**Fix:** Change function signature to `async def` to enable AsyncTaskRunner (automatic)

### Async Worker Using ThreadPoolExecutor Instead of AsyncTaskRunner
**Cause:** Worker function not properly detected as async
**Check:**
1. Function signature is `async def` (not `def`)
2. Check logs for "Created AsyncTaskRunner" vs "Created TaskRunner"
3. Verify `inspect.iscoroutinefunction(worker.execute_function)` returns True

### AsyncClient Pickling Errors
**Error:** `TypeError: cannot pickle 'httpx.AsyncClient' object`
**Cause:** AsyncClient created before fork (in `__init__`)
**Fix:** Already handled in SDK 1.3.0+ - clients created in `run()` after fork
**Note:** If you're implementing custom runners, defer async client creation to after fork

### Semaphore Errors in Async Workers
**Error:** `RuntimeError: no running event loop`
**Cause:** Semaphore created outside event loop
**Fix:** Already handled in SDK 1.3.0+ - semaphore created in `run()` within event loop

### Token Refresh Not Working in Async Workers
**Cause:** Token refresh requires `await` but `__init__` is not async
**Fix:** Already handled in SDK 1.3.0+ - lazy token fetch on first API call in `__get_authentication_headers()`

### Async Task Returns None Not Working
**Issue:** SDK version < 1.3.0 - BackgroundEventLoop approach needed sentinel pattern
**Fix:** Upgrade to SDK 1.3.0+ which uses AsyncTaskRunner (no sentinel needed, direct await)

### Tasks Not Picked Up
**Check:**
1. Domain: `export conductor.worker.all.domain=production`
2. Worker registered: `loader.print_summary()`
3. Not paused: `export conductor.worker.my_task.paused=false`
4. Check logs for runner type: "AsyncTaskRunner" vs "TaskRunner"

### Timeouts
**Fix:** Enable lease extension or increase task timeout in Conductor

### Empty Metrics
**Check:**
1. `metrics_settings` passed to TaskHandler
2. Workers actually executing tasks
3. Directory has write permissions
4. Both sync and async workers publish same metrics via events

---

## Implementation Files

**Core:**
- `src/conductor/client/automator/task_handler.py` - Orchestrator (auto-selects TaskRunner vs AsyncTaskRunner)
- `src/conductor/client/automator/task_runner.py` - Sync polling loop (ThreadPoolExecutor)
- `src/conductor/client/automator/async_task_runner.py` - Async polling loop (pure async/await)
- `src/conductor/client/worker/worker.py` - Worker + BackgroundEventLoop (sync workers only)
- `src/conductor/client/worker/worker_task.py` - @worker_task decorator
- `src/conductor/client/worker/worker_config.py` - Config resolution
- `src/conductor/client/worker/worker_loader.py` - Discovery
- `src/conductor/client/telemetry/metrics_collector.py` - Metrics

**Async HTTP (AsyncTaskRunner only):**
- `src/conductor/client/http/async_rest.py` - AsyncRESTClientObject (httpx.AsyncClient)
- `src/conductor/client/http/async_api_client.py` - AsyncApiClient (token refresh, retries)
- `src/conductor/client/http/api/async_task_resource_api.py` - Async batch_poll/update_task

**Tests:**
- `tests/unit/automator/test_task_runner.py` - TaskRunner unit tests
- `tests/unit/automator/test_async_task_runner.py` - AsyncTaskRunner unit tests (17 tests, mocked HTTP)

**Examples:**
- `examples/asyncio_workers.py`
- `examples/workers_e2e.py` - End-to-end async worker example
- `examples/compare_multiprocessing_vs_asyncio.py`
- `examples/worker_configuration_example.py`

---

## Testing

### Unit Tests

**AsyncTaskRunner Test Suite** (`tests/unit/automator/test_async_task_runner.py`):

```bash
# Run async worker tests
python3 -m pytest tests/unit/automator/test_async_task_runner.py -v

# All tests pass (17/17):
✅ test_async_worker_end_to_end         # Full poll → execute → update flow
✅ test_async_worker_with_none_return   # Workers can return None
✅ test_concurrency_limit_respected     # Semaphore limits concurrent tasks
✅ test_multiple_concurrent_tasks       # Concurrent execution verified
✅ test_capacity_check_prevents_over_polling  # Capacity management
✅ test_worker_exception_handling       # Error handling
✅ test_token_refresh_error_handling    # Auth error handling
✅ test_auth_failure_backoff           # Backoff on failures
✅ test_paused_worker_stops_polling    # Paused worker behavior
✅ test_adaptive_backoff_on_empty_polls # Backoff on empty queue
✅ test_task_result_serialization      # Complex output handling
✅ test_all_event_types_published      # All 6 event types verified
✅ test_custom_event_listener_integration  # Custom SLA monitor
✅ test_multiple_event_listeners       # Multiple listeners receive events
✅ test_event_listener_exception_isolation  # Faulty listeners don't break worker
✅ test_event_data_accuracy            # Event fields validated
✅ test_metrics_collector_receives_events  # MetricsCollector integration
```

**Test Coverage:**
- **Core functionality**: poll, execute, update
- **Concurrency**: semaphore limits, concurrent execution
- **Error handling**: worker exceptions, HTTP errors
- **Token refresh**: lazy fetch, TTL refresh, error backoff
- **Edge cases**: None returns, paused workers, capacity limits
- **Event system**: All 6 event types published correctly
- **Event listeners**: Custom listeners, multiple listeners, exception isolation
- **Event data**: All fields validated (duration, task_id, output_size, etc.)
- **Metrics integration**: MetricsCollector receives events

**Test Strategy:**
- HTTP requests: **Mocked** (AsyncMock)
- Everything else: **Real** (event system, configuration, serialization)
- No external dependencies
- Fast execution

### Integration Tests

For full end-to-end testing with real Conductor server:

```python
# examples/workers_e2e.py
python3 examples/workers_e2e.py
```

---

## Migration Guide

### From SDK < 1.3.0 to SDK 1.3.0+

**Good news: No code changes required!** 🎉

AsyncTaskRunner is automatically selected for async workers. Your existing code will work identically but with better performance.

#### **What Happens Automatically**

**Before (SDK < 1.3.0):**
```python
@worker_task(task_definition_name='fetch_data', thread_count=50)
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()

# Used: TaskRunner + BackgroundEventLoop (3 threads)
```

**After (SDK 1.3.0+):**
```python
@worker_task(task_definition_name='fetch_data', thread_count=50)
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()

# Uses: AsyncTaskRunner (1 event loop) - AUTOMATIC!
```

**Changes:**
- ✅ Same decorator
- ✅ Same code
- ✅ Same configuration
- ✅ Same metrics
- ✅ Same events
- ✅ Better performance (automatic)

#### **Verification**

Check logs on startup to see which runner is used:

```
# Async worker
INFO - Created AsyncTaskRunner for async worker: fetch_data

# Sync worker
INFO - Created TaskRunner for sync worker: process_data
```

#### **Rollback**

If you encounter issues with AsyncTaskRunner, you can temporarily force TaskRunner by changing `async def` to `def`:

```python
# Temporary rollback (not recommended)
@worker_task(task_definition_name='fetch_data')
def fetch_data(url: str) -> dict:  # Changed from async def
    # Will use TaskRunner instead of AsyncTaskRunner
    import asyncio
    return asyncio.run(actual_async_work(url))
```

**Note**: This defeats the purpose - only use for debugging.

#### **Performance Impact**

Expected improvements for I/O-bound async workers:

| Metric | TaskRunner (v3.2) | AsyncTaskRunner (v4.0) | Notes |
|--------|-------------------|----------------------|-------|
| Latency | Thread context switches | Direct await | Lower latency |
| Throughput | Thread pool limited | Event loop concurrent | Higher for I/O |
| Memory | Thread pool overhead | Single event loop | Lower memory |
| CPU usage | Context switching overhead | Pure async execution | Lower CPU |

---

---

## Changelog

### Version 4.1 (2025-11-30)
- Enhanced Worker Discovery section with comprehensive WorkerLoader documentation
- Expanded Long-Running Tasks section with detailed lease extension patterns
- Added practical examples for checkpointing and external system polling
- Consolidated content from WORKER_DISCOVERY.md and LEASE_EXTENSION.md
- **Clarified concurrency control mechanisms:**
  - Both TaskRunner and AsyncTaskRunner use dynamic batch polling
  - Batch size = thread_count - currently_running_tasks
  - TaskRunner: ThreadPoolExecutor capacity limits execution
  - AsyncTaskRunner: Semaphore limits execution (during execute + update)
  - Semaphore held until update succeeds (ensures capacity represents fully-handled tasks)
- **Implemented register_task_def functionality:**
  - Automatically registers task definitions on worker startup
  - Generates JSON Schema (draft-07) from Python type hints
  - Supports dataclasses, Optional, List, Dict, Union types
  - Creates schemas named {task_name}_input and {task_name}_output
  - Works for both TaskRunner and AsyncTaskRunner
  - Added task_def parameter for advanced configuration (retry, timeout, rate limits)
- **Added overwrite_task_def and strict_schema flags:**
  - `overwrite_task_def` (default: True) - Controls whether to overwrite existing task definitions
  - `strict_schema` (default: False) - Controls additionalProperties in JSON schemas
  - Both configurable via environment variables
  - Applies to both sync and async workers
- **Added TaskUpdateFailure event:**
  - Published when task update fails after all retry attempts (4 retries with exponential backoff: 10s/20s/30s)
  - Contains TaskResult for recovery/logging
  - Enables external handling of critical update failures
  - Event count: 7 total events (was 6)
- **Fixed Optional[T] handling:**
  - Optional[T] parameters are NOT required in schema
  - Optional[T] parameters are marked nullable
  - Works correctly with nested dataclasses
- Added detailed polling loop with dynamic batch sizing examples
- Improved troubleshooting guidance
- Fixed class-based worker support in TaskHandler async detection
- Fixed task_def_template passing in scan_for_annotated_workers path

### Version 4.0 (2025-11-28)
- AsyncTaskRunner: Pure async/await execution (zero thread overhead)
- Auto-detection: Automatic runner selection based on function signature
- Async HTTP: httpx.AsyncClient for non-blocking operations
- Process isolation: Clients created after fork
- Comprehensive event system documentation
- HTTP-based metrics serving

---

**Issues:** https://github.com/conductor-oss/conductor-python/issues
