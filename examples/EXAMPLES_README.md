# Conductor Python SDK Examples

This directory contains comprehensive examples demonstrating various Conductor SDK features and patterns.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Worker Examples](#-worker-examples)
- [Workflow Examples](#-workflow-examples)
- [Advanced Patterns](#-advanced-patterns)
- [Package Structure](#-package-structure)

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install conductor-python httpx requests

# Set environment variables
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
export CONDUCTOR_AUTH_KEY="your-key"      # Optional for Orkes Cloud
export CONDUCTOR_AUTH_SECRET="your-secret" # Optional for Orkes Cloud
```

### Simplest Example

```bash
# Start AsyncIO workers (recommended for most use cases)
python examples/asyncio_workers.py

# Or start multiprocessing workers (for CPU-intensive tasks)
python examples/multiprocessing_workers.py
```

---

## 👷 Worker Examples

### AsyncIO Workers (Recommended for I/O-bound tasks)

**File:** `asyncio_workers.py`

```bash
python examples/asyncio_workers.py
```

**Workers:**
- `calculate` - Fibonacci calculator (CPU-bound, runs in thread pool)
- `long_running_task` - Long-running task with Union[dict, TaskInProgress]
- `greet`, `greet_sync`, `greet_async` - Simple greeting examples (from helloworld package)
- `fetch_user` - HTTP API call (from user_example package)
- `update_user` - Process User dataclass (from user_example package)

**Features:**
- ✓ Low memory footprint (~60-90% less than multiprocessing)
- ✓ Perfect for I/O-bound tasks (HTTP, DB, file I/O)
- ✓ Automatic worker discovery from packages
- ✓ Single-process, event loop based
- ✓ Async/await support

---

### Multiprocessing Workers (Recommended for CPU-bound tasks)

**File:** `multiprocessing_workers.py`

```bash
python examples/multiprocessing_workers.py
```

**Workers:** Same as AsyncIO version (identical code works in both modes!)

**Features:**
- ✓ True parallelism (bypasses Python GIL)
- ✓ Better for CPU-intensive work (ML, data processing, crypto)
- ✓ Automatic worker discovery
- ✓ Multi-process execution
- ✓ Async functions work via asyncio.run() in each process

---

### Comparison: AsyncIO vs Multiprocessing

**File:** `compare_multiprocessing_vs_asyncio.py`

```bash
python examples/compare_multiprocessing_vs_asyncio.py
```

Benchmarks and compares:
- Memory usage
- CPU utilization
- Task throughput
- I/O-bound vs CPU-bound workloads

**Use this to decide which mode is best for your use case!**

| Feature | AsyncIO | Multiprocessing |
|---------|---------|-----------------|
| **Best for** | I/O-bound (HTTP, DB, files) | CPU-bound (compute, ML) |
| **Memory** | Low | Higher |
| **Parallelism** | Concurrent (single process) | True parallel (multi-process) |
| **GIL Impact** | Limited by GIL for CPU work | Bypasses GIL |
| **Startup Time** | Fast | Slower (spawns processes) |
| **Async Support** | Native | Via asyncio.run() |

---

### Task Context Example

**File:** `task_context_example.py`

```bash
python examples/task_context_example.py
```

Demonstrates:
- Accessing task metadata (task_id, workflow_id, retry_count, poll_count)
- Adding logs visible in Conductor UI
- Setting callback delays for long-running tasks
- Type-safe context access

```python
from conductor.client.context import get_task_context

def my_worker(data: dict) -> dict:
    ctx = get_task_context()

    # Access task info
    task_id = ctx.get_task_id()
    poll_count = ctx.get_poll_count()

    # Add logs (visible in UI)
    ctx.add_log(f"Processing task {task_id}")

    return {'result': 'done'}
```

---

### Worker Discovery Examples

#### Basic Discovery

**File:** `worker_discovery_example.py`

```bash
python examples/worker_discovery_example.py
```

Shows automatic discovery of workers from multiple packages:
- `worker_discovery/my_workers/order_tasks.py` - Order processing workers
- `worker_discovery/my_workers/payment_tasks.py` - Payment workers
- `worker_discovery/other_workers/notification_tasks.py` - Notification workers

**Key concept:** Use `import_modules` parameter to automatically discover and register all `@worker_task` decorated functions.

#### Sync + Async Discovery

**File:** `worker_discovery_sync_async_example.py`

```bash
python examples/worker_discovery_sync_async_example.py
```

Demonstrates mixing sync and async workers in the same application.

---

### Legacy Examples

**File:** `multiprocessing_workers_example.py`

Older example showing multiprocessing workers. Use `multiprocessing_workers.py` instead.

**File:** `task_workers.py`

Legacy worker examples. See `asyncio_workers.py` for modern patterns.

---

## 🔄 Workflow Examples

### Dynamic Workflows

**File:** `dynamic_workflow.py`

```bash
python examples/dynamic_workflow.py
```

Shows how to:
- Create workflows programmatically at runtime
- Chain tasks together dynamically
- Execute workflows without pre-registration
- Use idempotency strategies

```python
from conductor.client.workflow.conductor_workflow import ConductorWorkflow

workflow = ConductorWorkflow(name='dynamic_example', version=1)
workflow.add(get_user_email_task)
workflow.add(send_email_task)
workflow.execute(workflow_input={'user_id': '123'})
```

---

### Workflow Operations

**File:** `workflow_ops.py`

```bash
python examples/workflow_ops.py
```

Demonstrates:
- Starting workflows
- Pausing/resuming workflows
- Terminating workflows
- Getting workflow status
- Restarting failed workflows
- Retrying failed tasks

---

### Workflow Status Listener

**File:** `workflow_status_listner.py` *(note: typo in filename)*

```bash
python examples/workflow_status_listner.py
```

Shows how to:
- Listen for workflow status changes
- Handle workflow completion/failure events
- Implement callbacks for workflow lifecycle events

---

### Test Workflows

**File:** `test_workflows.py`

Unit test examples showing how to test workflows and tasks.

---

## 🎯 Advanced Patterns

### Long-Running Tasks

Long-running tasks use `Union[dict, TaskInProgress]` return type:

```python
from typing import Union
from conductor.client.context import get_task_context, TaskInProgress

@worker_task(task_definition_name='long_task')
def long_running_task(job_id: str) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    ctx.add_log(f"Processing {job_id}, poll {poll_count}/5")

    if poll_count < 5:
        # Still working - tell Conductor to callback after 1 second
        return TaskInProgress(
            callback_after_seconds=1,
            output={
                'job_id': job_id,
                'status': 'processing',
                'progress': poll_count * 20  # 20%, 40%, 60%, 80%
            }
        )

    # Completed
    return {
        'job_id': job_id,
        'status': 'completed',
        'result': 'success'
    }
```

**Key benefits:**
- ✓ Semantically correct (not an error condition)
- ✓ Type-safe with Union types
- ✓ Intermediate output visible in Conductor UI
- ✓ Logs preserved across polls
- ✓ Works in both AsyncIO and multiprocessing modes

---

### Task Configuration

**File:** `task_configure.py`

```bash
python examples/task_configure.py
```

Shows how to:
- Define task metadata
- Set retry policies
- Configure timeouts
- Set rate limits
- Define task input/output templates

---

### Shell Worker

**File:** `shell_worker.py`

```bash
python examples/shell_worker.py
```

Demonstrates executing shell commands as Conductor tasks:
- Run arbitrary shell commands
- Capture stdout/stderr
- Handle exit codes
- Set working directory and environment

---

### Kitchen Sink

**File:** `kitchensink.py`

Comprehensive example showing many SDK features together.

---

### Untrusted Host

**File:** `untrusted_host.py`

```bash
python examples/untrusted_host.py
```

Shows how to:
- Connect to Conductor with self-signed certificates
- Disable SSL verification (for testing only!)
- Handle certificate validation errors

**⚠️ Warning:** Only use for development/testing. Never disable SSL verification in production!

---

## 📦 Package Structure

```
examples/
├── EXAMPLES_README.md              # This file
│
├── asyncio_workers.py              # ⭐ Recommended: AsyncIO workers
├── multiprocessing_workers.py      # ⭐ Recommended: Multiprocessing workers
├── compare_multiprocessing_vs_asyncio.py  # Performance comparison
│
├── task_context_example.py         # TaskContext usage
├── worker_discovery_example.py     # Worker discovery patterns
├── worker_discovery_sync_async_example.py
│
├── dynamic_workflow.py             # Dynamic workflow creation
├── workflow_ops.py                 # Workflow operations
├── workflow_status_listner.py      # Workflow events
│
├── task_configure.py               # Task configuration
├── shell_worker.py                 # Shell command execution
├── untrusted_host.py               # SSL/certificate handling
├── kitchensink.py                  # Comprehensive example
├── test_workflows.py               # Testing examples
│
├── helloworld/                     # Simple greeting workers
│   └── greetings_worker.py
│
├── user_example/                   # HTTP + dataclass examples
│   ├── models.py                   # User dataclass
│   └── user_workers.py             # fetch_user, update_user
│
├── worker_discovery/               # Multi-package discovery
│   ├── my_workers/
│   │   ├── order_tasks.py
│   │   └── payment_tasks.py
│   └── other_workers/
│       └── notification_tasks.py
│
├── orkes/                          # Orkes Cloud specific examples
│   └── ...
│
└── (legacy files)
    ├── multiprocessing_workers_example.py
    └── task_workers.py
```

---

## 🎓 Learning Path

### 1. **Start Here** (Beginner)
```bash
# Learn basic worker patterns
python examples/asyncio_workers.py
```

### 2. **Learn Context** (Beginner)
```bash
# Understand task context
python examples/task_context_example.py
```

### 3. **Learn Discovery** (Intermediate)
```bash
# Package-based worker organization
python examples/worker_discovery_example.py
```

### 4. **Learn Workflows** (Intermediate)
```bash
# Create and manage workflows
python examples/dynamic_workflow.py
python examples/workflow_ops.py
```

### 5. **Optimize Performance** (Advanced)
```bash
# Choose the right execution mode
python examples/compare_multiprocessing_vs_asyncio.py

# Then use the appropriate mode:
python examples/asyncio_workers.py          # For I/O-bound
python examples/multiprocessing_workers.py  # For CPU-bound
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"

# Optional (for Orkes Cloud)
export CONDUCTOR_AUTH_KEY="your-key-id"
export CONDUCTOR_AUTH_SECRET="your-key-secret"

# Optional (for on-premise with auth)
export CONDUCTOR_AUTH_TOKEN="your-jwt-token"
```

### Programmatic Configuration

```python
from conductor.client.configuration.configuration import Configuration

# Option 1: Use environment variables
config = Configuration()

# Option 2: Explicit configuration
config = Configuration(
    server_api_url='http://localhost:8080/api',
    authentication_settings=AuthenticationSettings(
        key_id='your-key',
        key_secret='your-secret'
    )
)
```

---

## 🐛 Troubleshooting

### Workers Not Polling

**Problem:** Workers start but don't pick up tasks

**Solutions:**
1. Check task definition names match between workflow and workers
2. Verify Conductor server URL is correct
3. Check authentication credentials
4. Ensure tasks are in `SCHEDULED` state (not `COMPLETED` or `FAILED`)

### Context Not Available

**Problem:** `get_task_context()` raises error

**Solution:** Only call `get_task_context()` from within worker functions decorated with `@worker_task`.

### Async Functions Not Working in Multiprocessing

**Solution:** This now works automatically! The SDK runs async functions with `asyncio.run()` in multiprocessing mode.

### Import Errors

**Problem:** `ModuleNotFoundError` for worker modules

**Solutions:**
1. Ensure packages have `__init__.py`
2. Use correct module paths in `import_modules` parameter
3. Add parent directory to `sys.path` if needed

---

## 📚 Additional Resources

- [Main Documentation](../README.md)
- [Worker Guide](../WORKER_DISCOVERY.md)
- [API Reference](https://orkes.io/content/reference-docs/api/python-sdk)
- [Conductor Documentation](https://orkes.io/content)

---

## 🤝 Contributing

Have a useful example? Please contribute!

1. Create your example file
2. Add clear docstrings and comments
3. Test it works standalone
4. Update this README
5. Submit a PR

---

## 📝 License

Apache 2.0 - See [LICENSE](../LICENSE) for details
