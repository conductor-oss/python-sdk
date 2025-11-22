# Worker Concurrency Design

> **📖 This document has been consolidated into [WORKER_ARCHITECTURE.md](WORKER_ARCHITECTURE.md)**
>
> Please refer to the main architecture document for comprehensive, up-to-date information.

---

## Quick Navigation

For specific topics, jump to:

- [Architecture Overview](WORKER_ARCHITECTURE.md#architecture-overview) - Core design principles
- [Async Execution Modes](WORKER_ARCHITECTURE.md#two-async-execution-modes) - Blocking vs non-blocking
- [Usage Examples](WORKER_ARCHITECTURE.md#usage-examples) - Code examples
- [Configuration](WORKER_ARCHITECTURE.md#configuration) - Hierarchical config system
- [Performance](WORKER_ARCHITECTURE.md#performance-characteristics) - Benchmarks and tuning
- [Best Practices](WORKER_ARCHITECTURE.md#best-practices) - Production recommendations
- [Troubleshooting](WORKER_ARCHITECTURE.md#troubleshooting) - Common issues

---

## Architecture Overview

The Conductor Python SDK uses a **unified multiprocessing architecture**:

```
┌─────────────────────────────────────────────────┐
│           TaskHandler (Main Process)            │
│  - Discovers workers via @worker_task decorator │
│  - Spawns one Process per worker                │
│  - Each process has ThreadPoolExecutor          │
└─────────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │Process 1│  │Process 2│  │Process 3│  │Process N│
   │ Worker1 │  │ Worker2 │  │ Worker3 │  │ WorkerN │
   │ ThreadPool│ │ ThreadPool│ │ ThreadPool│ │ ThreadPool│
   └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

### Two Async Execution Modes

**1. Blocking Async (default, `non_blocking_async=False`)**
- Async tasks block worker thread until complete
- Simple, predictable behavior
- Best for: Most use cases, < 5 concurrent async tasks

**2. Non-Blocking Async (`non_blocking_async=True`)**
- Async tasks run concurrently in background
- Worker thread continues polling immediately
- 10-100x better async concurrency
- Best for: I/O-heavy async workloads, many concurrent tasks

## Quick Start

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.worker.worker_task import worker_task

# Blocking async (default)
@worker_task(
    task_definition_name='io_task',
    thread_count=10,
    non_blocking_async=False  # Default
)
async def io_task(data: dict) -> dict:
    await asyncio.sleep(1)
    return {'status': 'completed'}

# Non-blocking async (high concurrency)
@worker_task(
    task_definition_name='high_concurrency_task',
    thread_count=10,
    non_blocking_async=True  # Enable non-blocking
)
async def high_concurrency_task(data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(data['url'])
    return {'data': response.json()}

# Start worker
with TaskHandler(configuration=config) as handler:
    handler.start_processes()
    handler.join_processes()
```

## Performance Comparison

**10 concurrent async tasks (I/O-bound)**:

| Mode | Throughput | Latency (P95) | Best For |
|------|-----------|--------------|----------|
| Blocking | 50 tasks/sec | 200ms | General use, simple workflows |
| Non-blocking | 500 tasks/sec | 20ms | High-throughput I/O, many concurrent tasks |

**Improvement**: 10x throughput, 10x lower latency with non-blocking mode

## Configuration

### Via Decorator
```python
@worker_task(
    task_definition_name='my_task',
    non_blocking_async=True  # Enable non-blocking
)
async def my_worker(data: dict) -> dict:
    pass
```

### Via Environment Variables
```bash
# Global setting for all workers
export conductor.worker.all.non_blocking_async=true

# Worker-specific setting
export conductor.worker.my_task.non_blocking_async=true
```

## When to Use Which Mode

**Use Blocking (default)** when:
- General use cases
- Few concurrent async tasks (< 5)
- Quick async operations (< 1s)
- You want simplicity

**Use Non-Blocking** when:
- Many concurrent async tasks (10+)
- I/O-heavy workloads (HTTP calls, DB queries)
- Long-running async operations (> 1s)
- You need maximum throughput

---

## Why This Redirect?

As of SDK version 1.2.6, the architecture was simplified:

- **Before**: Two separate implementations (TaskHandler + TaskHandlerAsyncIO)
- **After**: Single unified TaskHandler with flexible async modes

The new architecture:
- ✅ Simpler to use and understand
- ✅ Better performance (BackgroundEventLoop)
- ✅ Flexible async execution (blocking or non-blocking)
- ✅ Same multiprocessing foundation
- ✅ Backward compatible

All relevant information has been consolidated into [WORKER_ARCHITECTURE.md](WORKER_ARCHITECTURE.md) for easier maintenance and better organization.

---

## Document Information

**Version**: 2.0 (Redirect)
**Last Updated**: 2025-01-21
**Status**: Redirect to [WORKER_ARCHITECTURE.md](WORKER_ARCHITECTURE.md)
**Superseded By**: WORKER_ARCHITECTURE.md v2.0

For questions or issues, see: https://github.com/conductor-oss/conductor-python/issues
