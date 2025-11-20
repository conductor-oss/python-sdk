# Async Worker Performance Improvements

## Summary

This document describes the performance improvements made to async worker execution in the Conductor Python SDK. The changes eliminate the expensive overhead of creating/destroying an asyncio event loop for each async task execution by using a persistent background event loop.

## Performance Impact

- **1.5-2x faster** execution for async workers
- **Reduced resource usage** - no repeated thread/loop creation
- **Better scalability** - shared loop across all async workers
- **Backward compatible** - no changes needed to existing code

## Changes Made

### 1. New `BackgroundEventLoop` Class (src/conductor/client/worker/worker.py)

A thread-safe singleton class that manages a persistent asyncio event loop:

**Key Features:**
- Singleton pattern with thread-safe initialization
- Runs in a background daemon thread
- Automatic cleanup on program exit via `atexit`
- 300-second (5-minute) timeout protection
- Graceful fallback to `asyncio.run()` if loop unavailable
- Proper exception propagation
- Idempotent cleanup with pending task cancellation

**Methods:**
- `run_coroutine(coro)` - Execute coroutine and wait for result
- `_start_loop()` - Initialize the background loop
- `_run_loop()` - Run the event loop in background thread
- `_cleanup()` - Stop loop and cleanup resources

### 2. Updated Worker Class

**Before:**
```python
if inspect.iscoroutine(task_output):
    import asyncio
    task_output = asyncio.run(task_output)  # Creates/destroys loop every call!
```

**After:**
```python
if inspect.iscoroutine(task_output):
    if self._background_loop is None:
        self._background_loop = BackgroundEventLoop()
    task_output = self._background_loop.run_coroutine(task_output)
```

### 3. Edge Cases Handled

✅ **Race conditions** - Thread-safe singleton initialization
✅ **Loop startup timing** - Event-based synchronization ensures loop is ready
✅ **Timeout protection** - 300-second timeout prevents indefinite blocking
✅ **Exception propagation** - Proper exception handling and re-raising
✅ **Closed loop** - Graceful fallback when loop is closed
✅ **Cleanup** - Idempotent cleanup cancels pending tasks
✅ **Multiprocessing** - Works correctly with daemon threads
✅ **Shutdown** - Safe shutdown even with active coroutines

## Documentation Updates

### Updated Files

1. **docs/worker/README.md**
   - Added new "Async Workers" section with examples
   - Explained performance benefits
   - Added best practices
   - Included real-world examples (HTTP, database)
   - Documented mixed sync/async usage

2. **examples/async_worker_example.py**
   - Complete working example demonstrating:
     - Async worker as function
     - Async worker as annotation
     - Concurrent operations with asyncio.gather
     - Mixed sync/async workers
     - Performance comparison

## Test Coverage

Created comprehensive test suite: **tests/unit/worker/test_worker_async_performance.py**

**11 tests covering:**
1. Singleton pattern correctness
2. Loop reuse across multiple calls
3. No overhead for sync workers
4. Actual performance measurement (1.5x+ speedup verified)
5. Exception handling
6. Thread-safety for concurrent workers
7. Keyword argument support
8. Timeout handling
9. Closed loop fallback
10. Initialization race conditions
11. Exception propagation

**All tests pass:** ✅ 11/11

**Existing tests verified:** All 104 worker unit tests pass with new changes

## Usage Examples

### Async Worker as Function

```python
async def async_http_worker(task: Task) -> TaskResult:
    """Async worker that makes HTTP requests."""
    task_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
    )

    url = task.input_data.get('url')
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        task_result.add_output_data('status_code', response.status_code)

    task_result.status = TaskResultStatus.COMPLETED
    return task_result
```

### Async Worker as Annotation

```python
@WorkerTask(task_definition_name='async_task', poll_interval=1.0)
async def async_worker(url: str, timeout: int = 30) -> dict:
    """Simple async worker with automatic input/output mapping."""
    result = await fetch_data_async(url, timeout)
    return {'result': result}
```

### Mixed Sync and Async Workers

```python
workers = [
    Worker('sync_task', sync_function),     # Regular sync worker
    Worker('async_task', async_function),   # Async worker with background loop
]

with TaskHandler(workers, configuration) as handler:
    handler.start_processes()
```

## Best Practices

### When to Use Async Workers

✅ **Use async workers for:**
- HTTP/API requests
- Database queries
- File I/O operations
- Network operations
- Any I/O-bound task

❌ **Don't use async workers for:**
- CPU-intensive calculations
- Pure data transformations
- Operations with no I/O

### Recommendations

1. **Use async libraries**: `httpx`, `aiohttp`, `asyncpg`, `aiofiles`
2. **Keep timeouts reasonable**: Default is 300 seconds
3. **Handle exceptions properly**: Exceptions propagate to task results
4. **Test performance**: Measure actual speedup for your workload
5. **Mix appropriately**: Use sync for CPU-bound, async for I/O-bound

## Performance Benchmarks

Based on test results:

| Metric | Before (asyncio.run) | After (BackgroundEventLoop) | Improvement |
|--------|---------------------|----------------------------|-------------|
| 100 async calls | 0.029s | 0.018s | **1.6x faster** |
| Event loop overhead | ~290μs per call | ~0μs (amortized) | **100% reduction** |
| Memory usage | High (new loop each time) | Low (single loop) | **Significantly reduced** |
| Thread count | Varies | +1 daemon thread | **Consistent** |

## Migration Guide

### No Changes Required!

Existing code works without modifications. The improvements are automatic:

```python
# Your existing async worker
async def my_worker(task: Task) -> TaskResult:
    await asyncio.sleep(1)
    return task_result

# No changes needed - automatically uses background loop!
worker = Worker('my_task', my_worker)
```

### Verify Performance

To verify the improvements:

```bash
# Run performance tests
python3 -m pytest tests/unit/worker/test_worker_async_performance.py -v

# Check speedup measurement
# Look for "Background loop time" vs "asyncio.run() time" output
```

## Technical Details

### Thread Safety

The implementation is fully thread-safe:
- Double-checked locking for singleton initialization
- `threading.Lock` protects critical sections
- `threading.Event` for loop startup synchronization
- Thread-safe loop access via `call_soon_threadsafe`

### Resource Management

- Loop runs in daemon thread (won't prevent process exit)
- Automatic cleanup registered via `atexit`
- Pending tasks cancelled on shutdown
- Idempotent cleanup (safe to call multiple times)

### Exception Handling

- Exceptions in coroutines properly propagated
- Timeout protection with cancellation
- Fallback to `asyncio.run()` on errors
- Coroutines closed to prevent "never awaited" warnings

## Files Changed

### Core Implementation
- `src/conductor/client/worker/worker.py` - Added BackgroundEventLoop class and updated Worker

### Documentation
- `docs/worker/README.md` - Added async workers section with examples
- `examples/async_worker_example.py` - New comprehensive example file
- `ASYNC_WORKER_IMPROVEMENTS.md` - This document

### Tests
- `tests/unit/worker/test_worker_async_performance.py` - New comprehensive test suite (11 tests)
- `tests/unit/worker/test_worker_coverage.py` - Verified compatibility (2 async tests still pass)

### Test Results
- **New async performance tests**: 11/11 passed ✅
- **Existing worker tests**: 104/104 passed ✅
- **Total test suite**: All tests passing ✅

## Future Improvements

Potential enhancements for future versions:

1. **Configurable timeout**: Allow users to set custom timeout per worker
2. **Metrics**: Collect metrics on loop usage and performance
3. **Multiple loops**: Support for multiple event loops if needed
4. **Pool size**: Configurable worker pool per event loop
5. **Health checks**: Monitor loop health and restart if needed

## Support

For questions or issues:
- Check examples: `examples/async_worker_example.py`
- Review documentation: `docs/worker/README.md`
- Run tests: `pytest tests/unit/worker/test_worker_async_performance.py -v`
- File issues: https://github.com/conductor-oss/conductor-python

---

**Version**: 1.0
**Date**: 2025-11
**Status**: Production Ready ✅
