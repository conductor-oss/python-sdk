# Worker Configuration

The Conductor Python SDK supports hierarchical worker configuration, allowing you to override worker settings at deployment time using environment variables without changing code.

## Configuration Hierarchy

Worker properties are resolved using a three-tier hierarchy (from lowest to highest priority):

1. **Code-level defaults** (lowest priority) - Values defined in `@worker_task` decorator
2. **Global worker config** (medium priority) - `conductor.worker.all.<property>` environment variables
3. **Worker-specific config** (highest priority) - `conductor.worker.<worker_name>.<property>` environment variables

This means:
- Worker-specific environment variables override everything
- Global environment variables override code defaults
- Code defaults are used when no environment variables are set

## Configurable Properties

The following properties can be configured via environment variables:

| Property | Type | Description | Example | Decorator? |
|----------|------|-------------|---------|------------|
| `poll_interval_millis` | int | Polling interval in milliseconds | `1000` | ✅ Yes |
| `domain` | string | Worker domain for task routing | `production` | ✅ Yes |
| `worker_id` | string | Unique worker identifier | `worker-1` | ✅ Yes |
| `thread_count` | int | Max concurrent executions (threads for sync, coroutines for async) | `10` | ✅ Yes |
| `register_task_def` | bool | Auto-register task definition with JSON schemas on startup | `true` | ✅ Yes |
| `overwrite_task_def` | bool | Overwrite existing task definitions when registering (default: true) | `false` | ✅ Yes |
| `strict_schema` | bool | Enforce strict schema validation - additionalProperties=false (default: false) | `true` | ✅ Yes |
| `poll_timeout` | int | Poll request timeout in milliseconds | `100` | ✅ Yes |
| `lease_extend_enabled` | bool | ⚠️ **Not implemented** - reserved for future use | `false` | ✅ Yes |
| `paused` | bool | Pause worker from polling/executing tasks | `true` | ❌ **Environment-only** |

**Notes**:
- The `paused` property is intentionally **not available** in the `@worker_task` decorator. It can only be controlled via environment variables, allowing operators to pause/resume workers at runtime without code changes or redeployment.
- The `lease_extend_enabled` parameter is accepted but **not currently implemented**. For lease extension, use manual `TaskInProgress` returns (see below).
- The `register_task_def` parameter automatically registers task definitions with JSON Schema (draft-07) generated from Python type hints.
- The `overwrite_task_def` parameter controls whether to overwrite existing task definitions (default: true).
- The `strict_schema` parameter controls JSON schema validation strictness (default: false for lenient validation).

### Understanding `thread_count`

The `thread_count` parameter has different meanings depending on worker type (automatically detected from function signature):

**Sync Workers (`def`):**
- Controls ThreadPoolExecutor size
- Each task consumes one thread
- Recommended: 1-4 for CPU-bound, 10-50 for I/O-bound

**Async Workers (`async def`):**
- Controls max concurrent async tasks (semaphore limit)
- All tasks share single event loop
- Recommended: 50-200 for I/O-bound (event loop handles thousands)

**Example:**
```python
# Sync worker - thread_count = thread pool size
@worker_task(task_definition_name='cpu_task', thread_count=4)
def cpu_task(data: dict) -> dict:
    return expensive_computation(data)

# Async worker - thread_count = concurrency limit (not threads!)
@worker_task(task_definition_name='api_task', thread_count=100)
async def api_task(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        return await client.get(url)
    # Only 1 thread, but 100 concurrent tasks!
```

**For more details**, see [Worker Design Documentation](docs/design/WORKER_DESIGN.md).

### Lease Extension for Long-Running Tasks

**Current Implementation**: Only manual lease extension via `TaskInProgress` is supported.

```python
from conductor.client.context.task_context import TaskInProgress, get_task_context
from typing import Union

@worker_task(task_definition_name='long_running_task')
def long_task(job_id: str) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    # Process chunk of work
    processed = process_chunk(job_id, poll_count)

    if not is_complete(job_id):
        # More work to do - extend lease by returning TaskInProgress
        return TaskInProgress(
            callback_after_seconds=60,  # Return to queue after 60s
            output={'progress': processed}
        )
    else:
        # Done - return final result
        return {'status': 'completed', 'result': processed}
```

**⚠️ Note**: The `lease_extend_enabled=True` configuration parameter does **not** provide automatic lease extension. You must explicitly return `TaskInProgress` to extend the lease.

**For detailed patterns**, see [Long-Running Tasks & Lease Extension](docs/design/WORKER_DESIGN.md#long-running-tasks--lease-extension).

### Understanding `overwrite_task_def`

Controls whether to overwrite existing task definitions when `register_task_def=True`:

**Overwrite Mode (default, overwrite_task_def=true):**
- Always calls `update_task_def()` to overwrite existing definitions
- Ensures server always has latest configuration from code
- **Use when:** Task configuration changes frequently, development environments

**No-Overwrite Mode (overwrite_task_def=false):**
- Checks if task exists before registering
- Only creates new task if it doesn't exist
- Preserves manual changes made on server
- **Use when:** Tasks managed outside code, production with manual config

```bash
# Global: Never overwrite any task definitions
export conductor.worker.all.overwrite_task_def=false

# Specific: Allow overwrite for this worker only
export conductor.worker.dynamic_task.overwrite_task_def=true
```

### Understanding `strict_schema`

Controls JSON Schema validation strictness when `register_task_def=True`:

**Lenient Mode (default, strict_schema=false):**
- Sets `additionalProperties=true` in schemas
- Allows extra fields beyond defined schema
- **Use when:** Backward compatibility, flexible integrations, development

**Strict Mode (strict_schema=true):**
- Sets `additionalProperties=false` in schemas
- Rejects inputs with extra fields
- **Use when:** Strict contract enforcement, production validation

```bash
# Global: Strict validation for all workers
export conductor.worker.all.strict_schema=true

# Specific: Lenient for this worker (overrides global)
export conductor.worker.flexible_task.strict_schema=false
```

**Example Schemas:**

```json
// strict_schema=false (default)
{
  "type": "object",
  "properties": {"name": {"type": "string"}},
  "additionalProperties": true  // ← Extra fields allowed
}

// strict_schema=true
{
  "type": "object",
  "properties": {"name": {"type": "string"}},
  "additionalProperties": false  // ← Extra fields rejected
}
```

## Environment Variable Format

### Global Configuration (All Workers)
```bash
conductor.worker.all.<property>=<value>
```

### Worker-Specific Configuration
```bash
conductor.worker.<task_definition_name>.<property>=<value>
```

## Basic Example

### Code Definition
```python
from conductor.client.worker.worker_task import worker_task

@worker_task(
    task_definition_name='process_order',
    poll_interval_millis=1000,
    domain='dev',
    thread_count=5
)
def process_order(order_id: str) -> dict:
    return {'status': 'processed', 'order_id': order_id}
```

### Without Environment Variables
Worker uses code-level defaults:
- `poll_interval_millis=1000`
- `domain='dev'`
- `thread_count=5`

### With Global Override
```bash
export conductor.worker.all.poll_interval_millis=500
export conductor.worker.all.domain=production
```

Worker now uses:
- `poll_interval_millis=500` (from global env)
- `domain='production'` (from global env)
- `thread_count=5` (from code)

### With Worker-Specific Override
```bash
export conductor.worker.all.poll_interval_millis=500
export conductor.worker.all.domain=production
export conductor.worker.process_order.thread_count=20
```

Worker now uses:
- `poll_interval_millis=500` (from global env)
- `domain='production'` (from global env)
- `thread_count=20` (from worker-specific env)

## Common Scenarios

### Production Deployment

Override all workers to use production domain and optimized settings:

```bash
# Global production settings
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval_millis=250

# Critical worker needs more resources
export conductor.worker.process_payment.thread_count=50
export conductor.worker.process_payment.poll_interval_millis=50
```

```python
# Code remains unchanged
@worker_task(task_definition_name='process_order', poll_interval_millis=1000, domain='dev', thread_count=5)
def process_order(order_id: str):
    ...

@worker_task(task_definition_name='process_payment', poll_interval_millis=1000, domain='dev', thread_count=5)
def process_payment(payment_id: str):
    ...
```

Result:
- `process_order`: domain=production, poll_interval_millis=250, thread_count=5
- `process_payment`: domain=production, poll_interval_millis=50, thread_count=50

### Development/Debug Mode

Slow down polling for easier debugging:

```bash
export conductor.worker.all.poll_interval_millis=10000  # 10 seconds
export conductor.worker.all.thread_count=1              # Single concurrent task
export conductor.worker.all.poll_timeout=5000           # 5 second timeout
```

All workers will use these debug-friendly settings without code changes.

### Staging Environment

Override only domain while keeping code defaults for other properties:

```bash
export conductor.worker.all.domain=staging
```

All workers use staging domain, but keep their code-defined poll intervals, thread counts, etc.

### High-Concurrency Async Workers

For async I/O-bound workers, increase concurrency significantly:

```bash
# Global settings for async workers
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval_millis=100  # Lower polling delay for async

# Async worker - high concurrency (event loop can handle it!)
export conductor.worker.fetch_api_data.thread_count=200

# Sync worker - keep moderate thread count
export conductor.worker.process_cpu_task.thread_count=10
```

```python
# Async worker - high concurrency with single event loop
@worker_task(task_definition_name='fetch_api_data')
async def fetch_api_data(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)

# Sync worker - traditional thread pool
@worker_task(task_definition_name='process_cpu_task')
def process_cpu_task(data: dict):
    return expensive_computation(data)
```

**Result**:
- `fetch_api_data`: 200 concurrent async tasks in 1 thread!
- `process_cpu_task`: 10 threads for CPU-bound work

### Pausing Workers

Temporarily disable workers without stopping the process:

```bash
# Pause all workers (maintenance mode)
export conductor.worker.all.paused=true

# Pause specific worker only
export conductor.worker.process_order.paused=true
```

When a worker is paused:
- It stops polling for new tasks
- Already-executing tasks complete normally
- The `task_paused_total` metric is incremented for each skipped poll
- No code changes or process restarts required

**Use cases:**
- **Maintenance**: Pause workers during database migrations or system maintenance
- **Debugging**: Pause problematic workers while investigating issues
- **Gradual rollout**: Pause old workers while testing new deployment
- **Resource management**: Temporarily reduce load by pausing non-critical workers

**Unpause workers** by removing or setting the variable to false:
```bash
unset conductor.worker.all.paused
# or
export conductor.worker.all.paused=false
```

**Monitor paused workers** using the `task_paused_total` metric:
```promql
# Check how many times workers were paused
task_paused_total{taskType="process_order"}
```

### Multi-Region Deployment

Route different workers to different regions using domains:

```bash
# US workers
export conductor.worker.us_process_order.domain=us-east
export conductor.worker.us_process_payment.domain=us-east

# EU workers
export conductor.worker.eu_process_order.domain=eu-west
export conductor.worker.eu_process_payment.domain=eu-west
```

### Canary Deployment

Test new configuration on one worker before rolling out to all:

```bash
# Production settings for all workers
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval_millis=200

# Canary worker uses staging domain for testing
export conductor.worker.canary_worker.domain=staging
```

## Boolean Values

Boolean properties accept multiple formats:

**True values**: `true`, `1`, `yes`
**False values**: `false`, `0`, `no`

```bash
export conductor.worker.all.lease_extend_enabled=true
export conductor.worker.critical_task.register_task_def=1
export conductor.worker.background_task.lease_extend_enabled=false
export conductor.worker.maintenance_task.paused=true
```

## Docker/Kubernetes Example

### Docker Compose

```yaml
services:
  worker:
    image: my-conductor-worker
    environment:
      - conductor.worker.all.domain=production
      - conductor.worker.all.poll_interval_millis=250
      - conductor.worker.critical_task.thread_count=50
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: worker-config
data:
  conductor.worker.all.domain: "production"
  conductor.worker.all.poll_interval_millis: "250"
  conductor.worker.critical_task.thread_count: "50"
---
apiVersion: v1
kind: Pod
metadata:
  name: conductor-worker
spec:
  containers:
  - name: worker
    image: my-conductor-worker
    envFrom:
    - configMapRef:
        name: worker-config
```

### Kubernetes Deployment with Namespace-Based Config

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: conductor-worker-prod
  namespace: production
spec:
  template:
    spec:
      containers:
      - name: worker
        image: my-conductor-worker
        env:
        - name: conductor.worker.all.domain
          value: "production"
        - name: conductor.worker.all.poll_interval_millis
          value: "250"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: conductor-worker-staging
  namespace: staging
spec:
  template:
    spec:
      containers:
      - name: worker
        image: my-conductor-worker
        env:
        - name: conductor.worker.all.domain
          value: "staging"
        - name: conductor.worker.all.poll_interval_millis
          value: "500"
```

## Programmatic Access

You can also use the configuration resolver programmatically:

```python
from conductor.client.worker.worker_config import resolve_worker_config, get_worker_config_summary

# Resolve configuration for a worker
config = resolve_worker_config(
    worker_name='process_order',
    poll_interval_millis=1000,
    domain='dev',
    thread_count=5
)

print(config)
# {'poll_interval_millis': 500, 'domain': 'production', 'thread_count': 5, ...}

# Get human-readable summary
summary = get_worker_config_summary('process_order', config)
print(summary)
# Worker 'process_order' configuration:
#   poll_interval_millis: 500 (from conductor.worker.all.poll_interval_millis)
#   domain: production (from conductor.worker.all.domain)
#   thread_count: 5 (from code)
```

## Best Practices

### 1. Use Global Config for Environment-Wide Settings
```bash
# Good: Set domain for entire environment
export conductor.worker.all.domain=production

# Less ideal: Set for each worker individually
export conductor.worker.worker1.domain=production
export conductor.worker.worker2.domain=production
export conductor.worker.worker3.domain=production
```

### 2. Use Worker-Specific Config for Exceptions
```bash
# Global settings for most workers
export conductor.worker.all.thread_count=10
export conductor.worker.all.poll_interval_millis=250

# Exception: High-priority worker needs more resources
export conductor.worker.critical_task.thread_count=50
export conductor.worker.critical_task.poll_interval_millis=50
```

### 3. Keep Code Defaults Sensible
Use sensible defaults in code so workers work without environment variables:

```python
@worker_task(
    task_definition_name='process_order',
    poll_interval_millis=1000,  # Reasonable default (1 second)
    domain='dev',                # Safe default domain
    thread_count=5               # Moderate concurrency
)
def process_order(order_id: str):
    ...
```

### 4. Document Environment Variables
Maintain a README or wiki documenting required environment variables for each deployment:

```markdown
# Production Environment Variables

## Required
- `conductor.worker.all.domain=production`

## Optional (Recommended)
- `conductor.worker.all.poll_interval_millis=250`
- `conductor.worker.all.thread_count=20`

## Worker-Specific Overrides
- `conductor.worker.critical_task.thread_count=50`
- `conductor.worker.critical_task.poll_interval_millis=50`
```

### 5. Use Infrastructure as Code
Manage environment variables through IaC tools:

```hcl
# Terraform example
resource "kubernetes_deployment" "worker" {
  spec {
    template {
      spec {
        container {
          env {
            name  = "conductor.worker.all.domain"
            value = var.environment_name
          }
          env {
            name  = "conductor.worker.all.poll_interval_millis"
            value = var.worker_poll_interval_millis
          }
          env {
            name  = "conductor.worker.all.thread_count"
            value = var.worker_thread_count
          }
        }
      }
    }
  }
}
```

## Troubleshooting

### Configuration Not Applied

**Problem**: Environment variables don't seem to take effect

**Solutions**:
1. Check environment variable names are correctly formatted:
   - Global: `conductor.worker.all.<property>`
   - Worker-specific: `conductor.worker.<exact_task_name>.<property>`

2. Verify the task definition name matches exactly:
```python
@worker_task(task_definition_name='process_order')  # Use this name in env var
```
```bash
export conductor.worker.process_order.domain=production  # Must match exactly
```

3. Check environment variables are exported and visible:
```bash
env | grep conductor.worker
```

### Boolean Values Not Parsed Correctly

**Problem**: Boolean properties not behaving as expected

**Solution**: Use recognized boolean values:
```bash
# Correct
export conductor.worker.all.lease_extend_enabled=true
export conductor.worker.all.register_task_def=false

# Incorrect
export conductor.worker.all.lease_extend_enabled=True  # Case matters
export conductor.worker.all.register_task_def=0        # Use 'false' instead
```

### Integer Values Not Parsed

**Problem**: Integer properties cause errors

**Solution**: Ensure values are valid integers without quotes in code:
```bash
# Correct
export conductor.worker.all.thread_count=10
export conductor.worker.all.poll_interval=500

# Incorrect (in most shells, but varies)
export conductor.worker.all.thread_count="10"
```

## Summary

The hierarchical worker configuration system provides flexibility to:
- **Deploy once, configure anywhere**: Same code works in dev/staging/prod
- **Override at runtime**: No code changes needed for environment-specific settings
- **Fine-tune per worker**: Optimize critical workers without affecting others
- **Simplify management**: Use global settings for common configurations
- **Pause/resume at runtime**: Control worker execution without redeployment

**Configuration priority**: Worker-specific > Global > Code defaults

### Key Configuration Patterns

**Sync Workers (CPU-bound):**
```bash
export conductor.worker.cpu_task.thread_count=4           # Thread pool size
export conductor.worker.cpu_task.poll_interval_millis=500  # Moderate polling
```

**Async Workers (I/O-bound):**
```bash
export conductor.worker.api_task.thread_count=100          # High concurrency
export conductor.worker.api_task.poll_interval_millis=100  # Fast polling
```

**Long-Running Tasks:**
```bash
# Note: Use TaskInProgress for lease extension (lease_extend_enabled not implemented)
export conductor.worker.ml_training.thread_count=2  # Limit concurrent long tasks
export conductor.worker.ml_training.poll_interval_millis=500
```

---

## Additional Resources

- **[Worker Design Documentation](docs/design/WORKER_DESIGN.md)** - Complete worker architecture guide
  - AsyncTaskRunner vs TaskRunner
  - Automatic runner selection (`def` vs `async def`)
  - Performance comparison and best practices
  - Worker discovery and metrics

- **[Examples](examples/)** - Working examples with configuration
  - `examples/worker_configuration_example.py` - Hierarchical configuration demo
  - `examples/workers_e2e.py` - End-to-end example
  - `examples/asyncio_workers.py` - Mixed sync/async workers

---

**Last Updated**: 2025-11-28
**SDK Version**: 1.3.0+
