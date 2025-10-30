# Authentication Retry Policy and Exponential Backoff

## Overview

The Conductor Python SDK implements an intelligent retry policy with exponential backoff for handling authentication errors (401 Unauthorized). This feature is available in both synchronous and asynchronous clients, helping maintain reliable connections to the Conductor server by automatically retrying failed requests with progressively increasing delays, preventing overwhelming the authentication service during transient failures.

## How It Works

When a request receives a 401 (Unauthorized) response, the SDK automatically:

1. **Detects the authentication failure** on auth-dependent endpoints
2. **Applies exponential backoff** with configurable delays between retries
3. **Refreshes the authentication token** (with race condition protection in async client)
4. **Retries the request** with the new token
5. **Tracks attempts per endpoint** to handle persistent failures gracefully

### Race Condition Protection (Async Client)

The async client includes built-in protection against race conditions when multiple concurrent requests receive 401 errors:

- Uses an async lock (`asyncio.Lock`) to synchronize token refresh operations
- Checks if another coroutine already refreshed the token before performing a refresh
- Validates token freshness using `token_update_time` and `auth_token_ttl_sec`
- Ensures only one token refresh occurs even with multiple simultaneous 401 responses

### Synchronous vs Asynchronous Behavior

**Async Client (`conductor.asyncio_client`)**:
- Uses `asyncio.sleep()` for non-blocking delays
- Includes race condition protection with `asyncio.Lock`
- Ideal for high-concurrency scenarios and modern async applications

**Sync Client (`conductor.client`)**:
- Uses `time.sleep()` for delays (blocks the current thread)
- Simpler implementation without lock-based synchronization
- Suitable for traditional synchronous applications and scripts

## Configuration

Both sync and async clients share the same configuration parameters.

### Async Client Configuration

For the async client (`conductor.asyncio_client`), configure the retry policy during initialization:

```python
from conductor.asyncio_client.configuration import Configuration

configuration = Configuration(
    server_url="https://your-conductor-server.com/api",
    auth_key="your_key_id",
    auth_secret="your_key_secret",
    # 401 retry configuration
    auth_401_max_attempts=5,              # Maximum retry attempts per endpoint
    auth_401_base_delay_ms=1000.0,        # Base delay in milliseconds
    auth_401_max_delay_ms=60000.0,        # Maximum delay cap in milliseconds
    auth_401_jitter_percent=0.2,          # Random jitter (20%)
    auth_401_stop_behavior="stop_worker"  # Behavior after max attempts
)
```

### Sync Client Configuration

For the sync client (`conductor.client`), configuration is identical:

```python
from conductor.client.configuration.configuration import Configuration

configuration = Configuration(
    server_url="https://your-conductor-server.com/api",
    auth_key="your_key_id",
    auth_secret="your_key_secret",
    # 401 retry configuration (same parameters as async client)
    auth_401_max_attempts=5,
    auth_401_base_delay_ms=1000.0,
    auth_401_max_delay_ms=60000.0,
    auth_401_jitter_percent=0.2,
    auth_401_stop_behavior="stop_worker"
)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auth_401_max_attempts` | `int` | `6` | Maximum number of retry attempts per endpoint before giving up |
| `auth_401_base_delay_ms` | `float` | `1000.0` | Initial delay in milliseconds before the first retry |
| `auth_401_max_delay_ms` | `float` | `60000.0` | Maximum delay cap in milliseconds (prevents excessive waiting) |
| `auth_401_jitter_percent` | `float` | `0.2` | Percentage of random jitter to add (0.0 to 1.0) to prevent thundering herd |
| `auth_401_stop_behavior` | `str` | `"stop_worker"` | Behavior when max attempts reached: `"stop_worker"` or `"continue"` |

### Environment Variables

You can also configure these settings via environment variables:

```bash
export CONDUCTOR_AUTH_401_MAX_ATTEMPTS=5
export CONDUCTOR_AUTH_401_BASE_DELAY_MS=1000.0
export CONDUCTOR_AUTH_401_MAX_DELAY_MS=60000.0
export CONDUCTOR_AUTH_401_JITTER_PERCENT=0.2
export CONDUCTOR_AUTH_401_STOP_BEHAVIOR=stop_worker
```

## Exponential Backoff Formula

The delay between retries follows an exponential backoff algorithm with jitter:

```
delay = min(base_delay * (2 ^ (attempt - 1)) * (1 + random_jitter), max_delay)
```

Where:
- `base_delay`: The base delay in seconds (converted from `auth_401_base_delay_ms`)
- `attempt`: Current retry attempt number (1, 2, 3, ...)
- `random_jitter`: Random value between `-jitter_percent` and `+jitter_percent`
- `max_delay`: Maximum allowed delay (converted from `auth_401_max_delay_ms`)

### Example Delays

With default configuration (`base_delay_ms=1000`, `jitter_percent=0.2`, `max_delay_ms=60000`):

| Attempt | Base Delay | With Jitter (20%) | Capped |
|---------|------------|-------------------|--------|
| 1 | 1s | 0.8s - 1.2s | ✓ |
| 2 | 2s | 1.6s - 2.4s | ✓ |
| 3 | 4s | 3.2s - 4.8s | ✓ |
| 4 | 8s | 6.4s - 9.6s | ✓ |
| 5 | 16s | 12.8s - 19.2s | ✓ |
| 6 | 32s | 25.6s - 38.4s | ✓ |

## Usage Examples

### Basic Usage with Async Client

```python
import asyncio
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.workflow_client import WorkflowClient

async def main():
    # Configuration with custom retry policy
    config = Configuration(
        server_url="https://your-server.com/api",
        auth_key="your_key",
        auth_secret="your_secret",
        auth_401_max_attempts=3,
        auth_401_base_delay_ms=500.0
    )

    workflow_client = WorkflowClient(config)

    # The retry policy is automatically applied to all API calls
    workflow = await workflow_client.start_workflow(
        name="my_workflow",
        version=1,
        input={"key": "value"}
    )

    print(f"Started workflow: {workflow.workflow_id}")

asyncio.run(main())
```

### Basic Usage with Sync Client

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.workflow_client import WorkflowClient

# Configuration with custom retry policy
config = Configuration(
    server_url="https://your-server.com/api",
    auth_key="your_key",
    auth_secret="your_secret",
    auth_401_max_attempts=3,
    auth_401_base_delay_ms=500.0
)

workflow_client = WorkflowClient(config)

# The retry policy is automatically applied to all API calls
workflow_id = workflow_client.start_workflow(
    name="my_workflow",
    version=1,
    input={"key": "value"}
)

print(f"Started workflow: {workflow_id}")
```

### Handling Multiple Concurrent Requests (Async Client)

The async client handles concurrent requests efficiently with race condition protection:

```python
import asyncio
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.workflow_client import WorkflowClient

async def start_multiple_workflows():
    config = Configuration(
        server_url="https://your-server.com/api",
        auth_key="your_key",
        auth_secret="your_secret"
    )

    workflow_client = WorkflowClient(config)

    # Start multiple workflows concurrently
    # If all receive 401, only one token refresh will occur
    tasks = [
        workflow_client.start_workflow(name="workflow1", version=1, input={}),
        workflow_client.start_workflow(name="workflow2", version=1, input={}),
        workflow_client.start_workflow(name="workflow3", version=1, input={})
    ]

    results = await asyncio.gather(*tasks)
    return results

asyncio.run(start_multiple_workflows())
```

### Working with Task Workers

Both sync and async workers benefit from the retry policy:

**Async Worker:**
```python
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.worker.worker import Worker
from conductor.asyncio_client.worker.worker_task import WorkerTask

config = Configuration(
    server_url="https://your-server.com/api",
    auth_key="your_key",
    auth_secret="your_secret",
    auth_401_max_attempts=8,  # More attempts for long-running workers
    auth_401_base_delay_ms=1000.0
)

@WorkerTask(task_definition_name="example_task", worker_id="worker1", domain="test")
async def example_task(task):
    return {"status": "completed"}

# Workers automatically benefit from retry policy
worker = Worker(config)
worker.start_polling()
```

**Sync Worker:**
```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker import Worker
from conductor.client.worker.worker_task import WorkerTask

config = Configuration(
    server_url="https://your-server.com/api",
    auth_key="your_key",
    auth_secret="your_secret",
    auth_401_max_attempts=8,
    auth_401_base_delay_ms=1000.0
)

@WorkerTask(task_definition_name="example_task", worker_id="worker1", domain="test")
def example_task(task):
    return {"status": "completed"}

worker = Worker(config)
worker.start_polling()
```

### Customizing for High-Traffic Scenarios

For high-traffic applications, consider adjusting the retry parameters:

```python
config = Configuration(
    server_url="https://your-server.com/api",
    auth_key="your_key",
    auth_secret="your_secret",
    # Faster retries with more attempts
    auth_401_max_attempts=8,
    auth_401_base_delay_ms=500.0,      # Start with 500ms
    auth_401_max_delay_ms=30000.0,     # Cap at 30 seconds
    auth_401_jitter_percent=0.3        # More jitter to spread load
)
```

### Customizing for Development/Testing

For development environments where you want faster feedback (works for both sync and async):

```python
# Async client
from conductor.asyncio_client.configuration import Configuration
# OR Sync client
# from conductor.client.configuration.configuration import Configuration

config = Configuration(
    server_url="http://localhost:8080/api",
    auth_key="your_key",
    auth_secret="your_secret",
    # Quick retries for development
    auth_401_max_attempts=2,
    auth_401_base_delay_ms=100.0,      # Start with 100ms
    auth_401_max_delay_ms=1000.0       # Cap at 1 second
)
```

## Auth-Dependent vs Non-Auth-Dependent Endpoints

The retry policy distinguishes between different types of endpoints:

### Auth-Dependent Endpoints (With Exponential Backoff)

These endpoints use the full exponential backoff policy:
- `/api/workflow/**` - Workflow operations
- `/api/task/**` - Task operations (except polling)
- `/api/metadata/**` - Metadata operations
- `/api/event/**` - Event operations
- And other authenticated endpoints

### Non-Auth-Dependent Endpoints (Single Retry)

These endpoints get a single retry without exponential backoff:
- `/api/token` - Token generation
- `/api/auth/**` - Authentication endpoints
- `/api/health` - Health check
- `/api/status` - Status endpoints

### Excluded Endpoints (No Retry)

Some endpoints never retry on 401:
- `/token` - Token generation endpoint (to prevent loops)

## Monitoring and Logging

Both sync and async clients log retry attempts and token refresh operations:

```python
import logging

# Enable debug logging to see retry details
logging.basicConfig(level=logging.INFO)

# Example log output (same for both sync and async):
# INFO: 401 error on POST /workflow/start - waiting 2.11s before retry (attempt 1/5)
# DEBUG: New auth token been set
# INFO: 401 error on POST /workflow/start - waiting 4.35s before retry (attempt 2/5)
# ERROR: 401 error on POST /workflow/start - max attempts (5) reached, stopping worker
```

### Differences in Logging Behavior

**Async Client:**
- Non-blocking delays (won't block other coroutines)
- Logs include async-specific context

**Sync Client:**
- Blocking delays (thread will sleep)
- Straightforward sequential logging

## Best Practices

### 1. Set Appropriate Max Attempts

Choose `auth_401_max_attempts` based on your use case:
- **Workers**: 6-10 attempts (allow time for auth issues to resolve)
- **Web applications**: 3-5 attempts (faster feedback to users)
- **Batch jobs**: 8-12 attempts (can tolerate longer delays)

### 2. Tune Delays for Your Environment

- **High-latency networks**: Increase `auth_401_base_delay_ms`
- **Low-latency networks**: Decrease `auth_401_base_delay_ms`
- **Rate-limited services**: Increase `auth_401_max_delay_ms`

### 3. Use Jitter to Prevent Thundering Herd

Always keep `auth_401_jitter_percent` > 0 (default 0.2 is good) to prevent multiple clients from retrying simultaneously.

### 4. Monitor Token Refresh Operations

In production, monitor how often token refreshes occur:
- Frequent refreshes might indicate auth service issues
- Consider increasing token TTL if refreshes are too frequent

### 5. Handle Persistent Failures

When `auth_401_max_attempts` is reached:
- Log the failure for monitoring
- Alert operations team if this happens frequently
- Consider implementing circuit breaker patterns

## Troubleshooting

### Issue: Too Many Token Refreshes

**Symptom**: Logs show frequent token refresh operations

**Solutions**:
1. Check if `auth_token_ttl_min` is too low (default: 45 minutes)
2. Verify server clock synchronization
3. Check for token validation issues on the server

### Issue: Requests Failing After Max Attempts

**Symptom**: All retries exhausted, 401 errors persist

**Solutions**:
1. Verify `auth_key` and `auth_secret` are correct
2. Check if credentials are expired or revoked
3. Verify network connectivity to auth service
4. Check server-side auth service logs

### Issue: Concurrent Requests Causing Multiple Token Refreshes (Async Client)

**Symptom**: Multiple token refresh operations for simultaneous requests (should not happen with race condition protection in async client)

**Solutions**:
1. Verify you're using the SDK version with race condition fixes (async client only)
2. Check if you're sharing the same `Configuration` instance across requests
3. Ensure `asyncio.Lock` is working correctly in your environment
4. Note: Sync client doesn't have this protection as it's not designed for concurrent requests

## Technical Details

### Implementation

The retry policy is implemented in:
- **Async Client**: `src/conductor/asyncio_client/adapters/api_client_adapter.py`
- **Sync Client**: `src/conductor/client/adapters/api_client_adapter.py`
- **Shared Policy**: `src/conductor/client/exceptions/auth_401_policy.py` - Policy configuration and backoff calculation

### Thread Safety and Concurrency

**Async Client:**
- Uses `asyncio.Lock` for token refresh synchronization
- Safe for concurrent coroutines
- Tokens are checked and refreshed atomically
- Race condition protection prevents duplicate token refreshes

**Sync Client:**
- Designed for single-threaded sequential execution
- No explicit locking (not needed for sequential requests)
- Thread-safe when used within a single thread
- For multi-threaded sync applications, ensure separate client instances per thread

### Performance Considerations

**Both Clients:**
- Token refresh operations are minimized through caching and validation
- Exponential backoff prevents overwhelming the auth service
- Jitter prevents synchronized retry storms
- Per-endpoint attempt tracking allows independent retry logic

**Async Client Specific:**
- Non-blocking delays don't prevent other operations from executing
- Ideal for high-concurrency scenarios (workers polling multiple tasks)
- Lower overall latency in concurrent scenarios

**Sync Client Specific:**
- Blocking delays pause the current thread
- Simpler to reason about (sequential execution)
- More suitable for scripts and batch processing

## Choosing Between Sync and Async

Use the **Async Client** when:
- Building high-concurrency applications (web servers, API gateways)
- Running workers that poll multiple tasks simultaneously
- Need non-blocking I/O operations
- Want maximum throughput with concurrent requests
- Working with modern async frameworks (FastAPI, aiohttp, etc.)

Use the **Sync Client** when:
- Writing simple scripts or batch jobs
- Working with traditional synchronous code
- Don't need concurrent request handling
- Prefer simpler, more straightforward code
- Integrating with existing sync-only libraries

Both clients provide the same retry policy functionality with identical configuration options.

## Migration Between Sync and Async

The configuration is compatible between both clients, making migration easier:

```python
# Shared configuration
config_params = {
    "server_url": "https://your-server.com/api",
    "auth_key": "your_key",
    "auth_secret": "your_secret",
    "auth_401_max_attempts": 5,
    "auth_401_base_delay_ms": 1000.0,
}

# Use with async client
from conductor.asyncio_client.configuration import Configuration as AsyncConfig
async_config = AsyncConfig(**config_params)

# Or with sync client
from conductor.client.configuration.configuration import Configuration as SyncConfig
sync_config = SyncConfig(**config_params)
```

## Related Documentation

- [Authorization & Access Control](README.md)
- [Worker Documentation](../worker/README.md)
- [Workflow Client Documentation](../workflow/README.md)
- [Testing Guide](../testing/README.md)
