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

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `poll_interval` | float | Polling interval in milliseconds | `1000` |
| `domain` | string | Worker domain for task routing | `production` |
| `worker_id` | string | Unique worker identifier | `worker-1` |
| `thread_count` | int | Number of concurrent threads/coroutines | `10` |
| `register_task_def` | bool | Auto-register task definition | `true` |
| `poll_timeout` | int | Poll request timeout in milliseconds | `100` |
| `lease_extend_enabled` | bool | Enable automatic lease extension | `true` |
| `paused` | bool | Pause worker from polling/executing tasks | `true` |

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
    poll_interval=1000,
    domain='dev',
    thread_count=5
)
def process_order(order_id: str) -> dict:
    return {'status': 'processed', 'order_id': order_id}
```

### Without Environment Variables
Worker uses code-level defaults:
- `poll_interval=1000`
- `domain='dev'`
- `thread_count=5`

### With Global Override
```bash
export conductor.worker.all.poll_interval=500
export conductor.worker.all.domain=production
```

Worker now uses:
- `poll_interval=500` (from global env)
- `domain='production'` (from global env)
- `thread_count=5` (from code)

### With Worker-Specific Override
```bash
export conductor.worker.all.poll_interval=500
export conductor.worker.all.domain=production
export conductor.worker.process_order.thread_count=20
```

Worker now uses:
- `poll_interval=500` (from global env)
- `domain='production'` (from global env)
- `thread_count=20` (from worker-specific env)

## Common Scenarios

### Production Deployment

Override all workers to use production domain and optimized settings:

```bash
# Global production settings
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval=250
export conductor.worker.all.lease_extend_enabled=true

# Critical worker needs more resources
export conductor.worker.process_payment.thread_count=50
export conductor.worker.process_payment.poll_interval=50
```

```python
# Code remains unchanged
@worker_task(task_definition_name='process_order', poll_interval=1000, domain='dev', thread_count=5)
def process_order(order_id: str):
    ...

@worker_task(task_definition_name='process_payment', poll_interval=1000, domain='dev', thread_count=5)
def process_payment(payment_id: str):
    ...
```

Result:
- `process_order`: domain=production, poll_interval=250, thread_count=5
- `process_payment`: domain=production, poll_interval=50, thread_count=50

### Development/Debug Mode

Slow down polling for easier debugging:

```bash
export conductor.worker.all.poll_interval=10000    # 10 seconds
export conductor.worker.all.thread_count=1         # Single-threaded
export conductor.worker.all.poll_timeout=5000      # 5 second timeout
```

All workers will use these debug-friendly settings without code changes.

### Staging Environment

Override only domain while keeping code defaults for other properties:

```bash
export conductor.worker.all.domain=staging
```

All workers use staging domain, but keep their code-defined poll intervals, thread counts, etc.

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
export conductor.worker.all.poll_interval=200

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
      - conductor.worker.all.poll_interval=250
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
  conductor.worker.all.poll_interval: "250"
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
        - name: conductor.worker.all.poll_interval
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
        - name: conductor.worker.all.poll_interval
          value: "500"
```

## Programmatic Access

You can also use the configuration resolver programmatically:

```python
from conductor.client.worker.worker_config import resolve_worker_config, get_worker_config_summary

# Resolve configuration for a worker
config = resolve_worker_config(
    worker_name='process_order',
    poll_interval=1000,
    domain='dev',
    thread_count=5
)

print(config)
# {'poll_interval': 500.0, 'domain': 'production', 'thread_count': 5, ...}

# Get human-readable summary
summary = get_worker_config_summary('process_order', config)
print(summary)
# Worker 'process_order' configuration:
#   poll_interval: 500.0 (from conductor.worker.all.poll_interval)
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
export conductor.worker.all.poll_interval=250

# Exception: High-priority worker needs more resources
export conductor.worker.critical_task.thread_count=50
export conductor.worker.critical_task.poll_interval=50
```

### 3. Keep Code Defaults Sensible
Use sensible defaults in code so workers work without environment variables:

```python
@worker_task(
    task_definition_name='process_order',
    poll_interval=1000,      # Reasonable default
    domain='dev',            # Safe default domain
    thread_count=5,          # Moderate concurrency
    lease_extend_enabled=True  # Safe default
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
- `conductor.worker.all.poll_interval=250`
- `conductor.worker.all.lease_extend_enabled=true`

## Worker-Specific Overrides
- `conductor.worker.critical_task.thread_count=50`
- `conductor.worker.critical_task.poll_interval=50`
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
            name  = "conductor.worker.all.poll_interval"
            value = var.worker_poll_interval
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

Configuration priority: **Worker-specific** > **Global** > **Code defaults**
