# Conductor Python SDK - Worker Architecture

**Version:** 2.0
**Date:** 2025-01-21
**SDK Version:** 1.2.6+

---

## Table of Contents

1. [TL;DR - Quick Start](#tldr---quick-start)
2. [Architecture Overview](#architecture-overview)
3. [TaskHandler Architecture](#taskhandler-architecture)
4. [Async Worker Support](#async-worker-support)
   - [BackgroundEventLoop](#backgroundeventloop)
   - [Two Async Execution Modes](#two-async-execution-modes)
   - [Performance Comparison](#performance-comparison)
5. [Usage Examples](#usage-examples)
6. [Configuration](#configuration)
7. [Performance Characteristics](#performance-characteristics)
8. [When to Use What](#when-to-use-what)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Summary](#summary)
12. [Related Documentation](#related-documentation)

---

## TL;DR - Quick Start

The Conductor Python SDK uses a **unified multiprocessing architecture** with flexible async support:

### Architecture
- **One Handler**: `TaskHandler` (always uses multiprocessing)
- **One Process per Worker**: Each worker runs in its own Python process
- **ThreadPoolExecutor**: Concurrent task execution within each process
- **BackgroundEventLoop**: Persistent async support (1.5-2x faster than asyncio.run)

### Async Execution Modes
1. **Blocking (default)**: Async tasks run sequentially, simple and predictable
2. **Non-blocking (opt-in)**: Async tasks run concurrently, 10-100x better throughput

### Key Benefits
- ✅ Supports sync and async workers seamlessly
- ✅ Ultra-low latency polling (2-5ms average)
- ✅ Process isolation (crashes don't affect other workers)
- ✅ Easy configuration via decorator or environment variables

---

## Architecture Overview

The SDK provides a unified, production-ready architecture:

### Core Design Principles

1. **Process Isolation**: One Python process per worker for fault isolation
2. **Concurrent Execution**: ThreadPoolExecutor in each process (controlled by `thread_count`)
3. **Synchronous Polling**: Lightweight, efficient polling using the requests library
4. **Async Support**: BackgroundEventLoop for efficient async worker execution
5. **Flexible Modes**: Choice between blocking (simple) and non-blocking (high-throughput) async

### Why This Architecture?

- **Fault Tolerance**: Worker crashes don't affect other workers (process boundaries)
- **True Parallelism**: Bypasses Python's GIL for CPU-bound tasks
- **Predictable Performance**: Each worker has dedicated resources
- **Battle-Tested**: Proven in production environments
- **Simple Mental Model**: Easy to understand and debug

---

## TaskHandler Architecture

```
┌────────────────────────────────────────────┐
│  TaskHandler (Main Process)                │
└────────────────────────────────────────────┘
              │
     ┌────────┼────────┬────────┐
     ▼        ▼        ▼        ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Process 1│ │Process 2│ │Process 3│ │Process N│
│Worker 1 │ │Worker 2 │ │Worker 3 │ │Worker N │
└─────────┘ └─────────┘ └─────────┘ └─────────┘

Each process runs optimized polling loop:
  # Thread pool for concurrent execution (size = thread_count)
  executor = ThreadPoolExecutor(max_workers=thread_count)

  while True:
    # Check completed async tasks (non-blocking)
    check_completed_async_tasks()

    # Cleanup completed tasks immediately for ultra-low latency
    cleanup_completed_tasks()

    if running_tasks + pending_async < thread_count:
      # Adaptive backoff when queue is empty
      if consecutive_empty_polls > 0:
        delay = min(0.001 * (2 ** consecutive_empty_polls), poll_interval)
        if time_since_last_poll < delay:
          sleep(delay - time_since_last_poll)
          continue

      # Batch poll for available slots
      tasks = batch_poll(available_slots)  # SYNC (requests), non-blocking

      if tasks:
        consecutive_empty_polls = 0
        for task in tasks:
          executor.submit(execute_and_update, task)  # Execute in background
        # Continue polling immediately (tight loop!)
      else:
        consecutive_empty_polls += 1
    else:
      sleep(0.001)                     # At capacity, minimal sleep
```

**Key Points:**
- **Polling:** Always sync (requests), continuous, non-blocking
- **Execution:** Thread pool per worker process (size = thread_count)
- **Concurrency:** Polling continues while tasks execute in background
- **Capacity:** Can handle up to thread_count concurrent tasks per worker
- **Ultra-low latency:** 2-5ms average polling delay (immediate cleanup + adaptive backoff)
- **Batch polling:** Fetches multiple tasks per API call when slots available
- **Adaptive backoff:** Exponential backoff when queue empty (1ms→2ms→4ms→poll_interval)
- **Tight loop:** Continuous polling when work available, graceful backoff when empty
- **Memory:** ~60 MB per worker process
- **Isolation:** Process boundaries (one crash doesn't affect others)

---

## Async Worker Support

### BackgroundEventLoop (Singleton - ONE per Process)

**Since v1.2.3**, async workers are supported via a persistent background event loop:

**Architecture:**
```
Process 1                           Process 2
┌─────────────────────────┐        ┌─────────────────────────┐
│ Worker 1 (async) ───┐   │        │ Worker 4 (async) ───┐   │
│ Worker 2 (async) ───┼───┤        │ Worker 5 (sync)     │   │
│ Worker 3 (async) ───┘   │        │ Worker 6 (async) ───┘   │
│         ↓               │        │         ↓               │
│  BackgroundEventLoop    │        │  BackgroundEventLoop    │
│  (SINGLETON)            │        │  (SINGLETON)            │
│  • One thread           │        │  • One thread           │
│  • One event loop       │        │  • One event loop       │
│  • Shared by all workers│        │  • Shared by all workers│
│  • 3-6 MB total         │        │  • 3-6 MB total         │
└─────────────────────────┘        └─────────────────────────┘
```

**Key Point:** All async workers in the same process share ONE BackgroundEventLoop instance (singleton pattern). This provides excellent resource efficiency while maintaining process isolation.

```python
class BackgroundEventLoop:
    """Singleton managing persistent asyncio event loop in background thread.

    Provides 1.5-2x performance improvement for async workers by avoiding
    the expensive overhead of creating/destroying an event loop per task.

    Key Features:
    - **Thread-safe singleton pattern** (ONE instance per Python process)
    - **Shared across all workers** in the same process
    - **Lazy initialization** (loop only starts when first async worker executes)
    - **Zero overhead** for sync workers (never created if not needed)
    - **Runs in daemon thread** (one thread per process, not per worker)
    - **Automatic cleanup** on program exit
    - **Process isolation** (each process has its own singleton)

    Memory Impact:
    - ~3-6 MB per process (regardless of number of async workers)
    - Much more efficient than separate loops (would be 30-60 MB for 10 workers)
    """

    def submit_coroutine(self, coro) -> Future:
        """Non-blocking: Submit coroutine and return Future immediately."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future

    def run_coroutine(self, coro):
        """Blocking: Wait for coroutine result (default behavior)."""
        future = self.submit_coroutine(coro)
        return future.result(timeout=300)
```

### Two Async Execution Modes

The SDK supports two modes for executing async workers:

**Visual Comparison:**

```
Blocking Mode (default):
┌───────────────────────────────────────┐
│ Worker Thread                         │
│  Poll → Execute → [BLOCKED] → Update  │ ← Sequential
└───────────────────────────────────────┘
         ↓
    BackgroundEventLoop runs async task
    (thread waits for completion)

Non-Blocking Mode:
┌───────────────────────────────────────┐
│ Worker Thread                         │
│  Poll → Execute → Continue Polling    │ ← Concurrent
└───────────────────────────────────────┘
         ↓ submit
    BackgroundEventLoop
    ├─ Async Task 1 (running)
    ├─ Async Task 2 (running)
    └─ Async Task 3 (running)
         ↑ check results
    Worker Thread periodically checks
```

#### 1. Blocking Mode (Default)

```python
@worker_task(
    task_definition_name='async_task',
    thread_count=10,
    non_blocking_async=False  # Default
)
async def my_async_worker(data: dict) -> dict:
    result = await async_operation(data)
    return {'result': result}
```

**How it works:**
- Worker thread calls `worker.execute(task)`
- Detects async function, submits to BackgroundEventLoop
- **Blocks** waiting for result
- Returns result, thread picks up next task

**Characteristics:**
- ✅ Simple and predictable
- ✅ 1.5-2x faster than creating new event loops
- ✅ Backward compatible
- ⚠️ Worker thread blocked during async operation
- ⚠️ Sequential async execution

**Best for:**
- General use cases
- Few concurrent async tasks (< 5)
- Quick async operations (< 1s)
- Simplicity and predictability

#### 2. Non-Blocking Mode (Opt-in)

```python
@worker_task(
    task_definition_name='async_task',
    thread_count=10,
    non_blocking_async=True  # Opt-in for better concurrency
)
async def my_async_worker(data: dict) -> dict:
    result = await async_operation(data)
    return {'result': result}
```

**How it works:**
- Worker thread calls `worker.execute(task)`
- Detects async function, submits to BackgroundEventLoop
- **Returns immediately** with Future (non-blocking!)
- Thread continues polling for more tasks
- Separate check retrieves completed async results

**Characteristics:**
- ✅ 10-100x better async concurrency
- ✅ Worker threads continue polling during async operations
- ✅ Multiple async tasks run concurrently in BackgroundEventLoop
- ✅ Better thread utilization
- ⚠️ Slightly more complex state management

**Best for:**
- Many concurrent async tasks (10+)
- I/O-heavy workloads (HTTP calls, DB queries)
- Long-running async operations (> 1s)
- Maximum async throughput

### Performance Comparison

**Scenario: Worker with thread_count=10, each async task takes 5 seconds**

| Metric | Blocking Mode | Non-Blocking Mode | Improvement |
|--------|---------------|-------------------|-------------|
| **Total time (10 tasks)** | 50 seconds | 5 seconds | **10x faster** |
| **Async concurrency** | 1 task at a time | 10 concurrent | **10x more** |
| **Thread utilization** | Low (blocked) | High (polling) | **Much better** |
| **Throughput** | 0.2 tasks/sec | 2 tasks/sec | **10x higher** |

**Key Insight**: Non-blocking mode allows async tasks to run concurrently in the BackgroundEventLoop while worker threads continue polling for new work.

---

## Usage Examples

### Example 1: Sync Worker (Traditional)

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='process_data')
def process_data(data: dict) -> dict:
    """Sync worker for CPU-bound work."""
    result = expensive_computation(data)
    return {'result': result}

# Start handler
handler = TaskHandler(configuration=config)
handler.start_processes()
handler.join_processes()
```

### Example 2: Async Worker - Blocking Mode (Default)

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.worker.worker_task import worker_task
import httpx

@worker_task(task_definition_name='fetch_data')
async def fetch_data(url: str) -> dict:
    """Async worker - automatically uses BackgroundEventLoop (blocking mode)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return {'data': response.json()}

# Start handler (handles both sync and async workers)
handler = TaskHandler(configuration=config)
handler.start_processes()
handler.join_processes()
```

**What happens:**
1. TaskHandler spawns one process per worker
2. Each process polls synchronously (using requests)
3. When **first** async worker executes, BackgroundEventLoop singleton is created (lazy)
4. Async function runs in the shared background event loop (1.6x faster than asyncio.run)
5. Worker thread blocks waiting for result
6. **All subsequent async workers in this process reuse the same BackgroundEventLoop**
7. Returns result and continues

### Example 3: Async Worker - Non-Blocking Mode (High Concurrency)

```python
@worker_task(
    task_definition_name='fetch_data',
    thread_count=20,
    non_blocking_async=True  # Enable non-blocking mode
)
async def fetch_data(url: str) -> dict:
    """Async worker with non-blocking execution for high concurrency."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return {'data': response.json()}

# Start handler
handler = TaskHandler(configuration=config)
handler.start_processes()
handler.join_processes()
```

**What happens:**
1. Worker polls for task
2. Detects async function, submits to BackgroundEventLoop
3. **Returns immediately** - worker continues polling
4. Can handle 20+ async tasks concurrently
5. Completed tasks updated separately
6. 10-100x better async throughput!

### Example 4: Mixed Sync and Async Workers

```python
# CPU-bound sync worker
@worker_task(task_definition_name='cpu_task', thread_count=4)
def cpu_intensive(data: bytes) -> dict:
    """Sync worker for CPU-bound work."""
    processed = expensive_computation(data)
    return {'result': processed}

# I/O-bound async worker (non-blocking for high concurrency)
@worker_task(
    task_definition_name='io_task',
    thread_count=20,
    non_blocking_async=True
)
async def io_intensive(url: str) -> dict:
    """Async worker for I/O-bound work."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return {'data': response.json()}

# Both work together seamlessly!
handler = TaskHandler(configuration=config)
handler.start_processes()
handler.join_processes()
```

---

## Configuration

### Hierarchical Configuration System

Worker configuration follows a three-tier priority system:

1. **Worker-specific environment variables** (highest priority): `conductor.worker.<worker_name>.<property>`
2. **Global environment variables**: `conductor.worker.all.<property>`
3. **Decorator parameters** (lowest priority): Code-level defaults

#### Environment Variables

```bash
# Global configuration (applies to all workers)
export conductor.worker.all.non_blocking_async=true
export conductor.worker.all.poll_interval=500
export conductor.worker.all.thread_count=20

# Worker-specific configuration (overrides global)
export conductor.worker.fetch_data.non_blocking_async=false
export conductor.worker.fetch_data.thread_count=50
```

**Supported Properties:**
- `non_blocking_async` (bool)
- `poll_interval` (int, milliseconds)
- `thread_count` (int)
- `domain` (string)
- `worker_id` (string)
- `poll_timeout` (int, milliseconds)
- `lease_extend_enabled` (bool)

#### Decorator Parameters

```python
@worker_task(
    task_definition_name='my_task',

    # Concurrency
    thread_count=10,              # Thread pool size (concurrent tasks)
    non_blocking_async=True,      # Non-blocking async mode (opt-in)

    # Polling
    poll_interval_millis=100,     # Polling interval
    poll_timeout=100,             # Server-side poll timeout

    # Misc
    domain='my_domain',           # Task domain
    worker_id='custom_id',        # Worker ID
    register_task_def=False,      # Auto-register task def
    lease_extend_enabled=True     # Auto-extend lease
)
async def my_async_worker(data: dict) -> dict:
    return await async_operation(data)
```

---

## Performance Characteristics

### Memory Usage

| Workers | Memory Per Process | Total Memory |
|---------|-------------------|--------------|
| 1       | 62 MB             | 62 MB        |
| 5       | 62 MB             | 310 MB       |
| 10      | 62 MB             | 620 MB       |
| 20      | 62 MB             | 1.2 GB       |
| 50      | 62 MB             | 3.0 GB       |
| 100     | 62 MB             | 6.0 GB       |

### Async Performance (10 async tasks, 5 seconds each)

| Mode | Time | Concurrency | Thread Util |
|------|------|-------------|-------------|
| **Blocking (default)** | 50s | 1 task/time | Low (blocked) |
| **Non-blocking** | 5s | 10 concurrent | High (polling) |
| **Improvement** | **10x faster** | **10x better** | **Much better** |

### Polling Latency (v1.2.5+)

| Metric | Value |
|--------|-------|
| **Average polling delay** | 2-5ms |
| **P95 polling delay** | <15ms |
| **P99 polling delay** | <20ms |
| **Throughput** | 250+ tasks/sec (continuous load, thread_count=10) |
| **Efficiency** | 80-85% of perfect parallelism |
| **API call reduction** | 65% (via batch polling) |

**Before optimizations:** 15-90ms delays between task completion and next pickup
**After optimizations:** 2-5ms average delay (10-18x improvement!)

---

## When to Use What

### Sync Workers

✅ **Use sync workers when:**
- CPU-bound tasks (image processing, ML inference)
- Existing synchronous codebase
- Blocking I/O operations (no async library available)

```python
@worker_task(task_definition_name='cpu_task')
def cpu_worker(data: dict) -> dict:
    return expensive_computation(data)
```

### Async Workers - Blocking Mode (Default)

✅ **Use blocking async when:**
- General async use cases
- Few concurrent async tasks (< 5)
- Quick async operations (< 1s)
- You want simplicity

```python
@worker_task(task_definition_name='async_task')
async def async_worker(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()
```

### Async Workers - Non-Blocking Mode

✅ **Use non-blocking async when:**
- Many concurrent async tasks (10+)
- I/O-heavy workloads (HTTP, DB, file I/O)
- Long-running async operations (> 1s)
- You need maximum async throughput

```python
@worker_task(
    task_definition_name='async_task',
    non_blocking_async=True  # Opt-in
)
async def async_worker(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()
```

---

## Best Practices

### 1. Choose the Right Async Mode

```python
# Default blocking - good for most cases
@worker_task(task_definition_name='simple_async')
async def simple_async(data: dict):
    result = await quick_operation(data)  # < 1s
    return result

# Non-blocking - for high concurrency
@worker_task(
    task_definition_name='high_concurrency',
    thread_count=50,
    non_blocking_async=True
)
async def high_concurrency(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)  # Many concurrent calls
    return response.json()
```

### 2. Set Appropriate Thread Counts

```python
import os

# CPU-bound: 1-2 workers per CPU core
cpu_count = os.cpu_count()
thread_count_cpu = cpu_count * 2

# I/O-bound: Higher counts work well
thread_count_io = 20  # Or higher for async

# Non-blocking async: Even higher
thread_count_async = 50  # Can handle many concurrent async tasks
```

### 3. Monitor Memory Usage

```python
import psutil

def monitor_memory():
    process = psutil.Process()
    children = process.children(recursive=True)

    total_memory = process.memory_info().rss
    for child in children:
        total_memory += child.memory_info().rss

    print(f"Total memory: {total_memory / 1024 / 1024:.0f} MB")
```

### 4. Use Async Libraries

```python
# ✅ Good: Async libraries
import httpx
import aiopg
import aiofiles

@worker_task(task_definition_name='async_task')
async def async_worker(task):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    async with aiopg.create_pool() as pool:
        async with pool.acquire() as conn:
            await conn.execute("INSERT ...")

# ❌ Bad: Sync libraries in async (blocks!)
import requests  # Blocks event loop!

@worker_task(task_definition_name='bad_async')
async def bad_async_worker(task):
    response = requests.get(url)  # ❌ Blocks!
```

### 5. Handle Graceful Shutdown

```python
import signal
import sys

def signal_handler(signum, frame):
    logger.info("Received shutdown signal")
    handler.stop_processes()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

---

## Troubleshooting

### Issue 1: High Memory Usage

**Symptom**: Memory usage grows to gigabytes

**Solution**: Reduce worker count
```python
# Before
workers = [Worker(f'task{i}') for i in range(100)]  # 6 GB!

# After
workers = [Worker(f'task{i}') for i in range(20)]  # 1.2 GB
```

### Issue 2: Async Tasks Not Running Concurrently

**Symptom**: Async tasks run sequentially, not concurrently

**Solution**: Enable non-blocking mode
```python
# Before (blocking - sequential)
@worker_task(task_definition_name='async_task')
async def my_worker(data: dict):
    return await async_operation(data)

# After (non-blocking - concurrent)
@worker_task(
    task_definition_name='async_task',
    non_blocking_async=True  # ✅ Enables concurrency
)
async def my_worker(data: dict):
    return await async_operation(data)
```

### Issue 3: Event Loop Blocked

**Symptom**: Async workers frozen, no tasks processing

**Diagnosis**: Sync blocking call in async worker

**Solution**: Use async equivalent
```python
# ❌ Bad: Blocks event loop
async def worker(task):
    time.sleep(10)  # Blocks entire loop!

# ✅ Good: Async sleep
async def worker(task):
    await asyncio.sleep(10)
```

---

## Summary

### Key Takeaways

✅ **Unified Architecture**
- Single TaskHandler class
- Multiprocessing for isolation
- Supports sync and async workers

✅ **Flexible Async Execution**
- Blocking mode (default): Simple, predictable
- Non-blocking mode (opt-in): 10-100x better concurrency

✅ **High Performance**
- 2-5ms average polling delay
- 250+ tasks/sec throughput
- 1.5-2x faster async (BackgroundEventLoop)
- 10-100x async concurrency (non-blocking mode)

✅ **Easy to Use**
- Simple decorator API
- No code changes for sync workers
- Opt-in for advanced features

✅ **Production Ready**
- Battle-tested multiprocessing
- Comprehensive error handling
- Proper resource cleanup

---

## Related Documentation

### Examples
- **examples/asyncio_workers.py** - Async worker examples
- **examples/compare_multiprocessing_vs_asyncio.py** - Blocking vs non-blocking comparison
- **examples/worker_configuration_example.py** - Configuration examples

### Other Documentation
- **WORKER_CONCURRENCY_DESIGN.md** - Quick reference (redirects here)
- **README.md** - Main SDK documentation
- **src/conductor/client/worker/** - Worker implementation source code

---

## Document Information

**Document Version**: 2.0
**Created**: 2025-01-20
**Last Updated**: 2025-01-21
**Status**: Production-Ready
**Maintained By**: Conductor Python SDK Team

### Changelog

- **v2.0 (2025-01-21)**: Complete rewrite for unified architecture
  - Removed TaskHandlerAsyncIO references (deleted)
  - Documented blocking vs non-blocking async modes
  - Added hierarchical configuration documentation
  - Updated performance metrics
  - Consolidated from multiple documents

- **v1.0 (2025-01-20)**: Initial version

---

**Questions or Issues?**
- GitHub Issues: https://github.com/conductor-oss/conductor-python/issues
- SDK Documentation: https://conductor-oss.github.io/conductor-python/
