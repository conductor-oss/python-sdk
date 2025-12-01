# Integration Tests

End-to-end integration tests that run against a **real Conductor server**.

**NO MOCKS** - These tests validate actual behavior with real API calls.

---

## Prerequisites

### 1. Conductor Server Running

**Option A: Local Conductor (Docker)**
```bash
docker run --init -p 8080:8080 -p 5000:5000 conductoross/conductor-standalone:3.15.0
```

**Option B: Orkes Cloud**
```bash
# Get credentials from: https://orkes.io
export CONDUCTOR_SERVER_URL="https://developer.orkescloud.com/api"
export CONDUCTOR_AUTH_KEY="your-key-id"
export CONDUCTOR_AUTH_SECRET="your-key-secret"
```

### 2. Environment Variables

```bash
# Required
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"

# Optional (for Orkes Cloud)
export CONDUCTOR_AUTH_KEY="your-key"
export CONDUCTOR_AUTH_SECRET="your-secret"
```

---

## Running Tests

### Run All Integration Tests

```bash
python3 -m pytest tests/integration/ -v -s
```

### Run Specific Test

```bash
python3 -m pytest tests/integration/test_worker_framework_e2e.py -v -s
```

### Run with Detailed Logging

```bash
python3 -m pytest tests/integration/test_worker_framework_e2e.py -v -s --log-cli-level=DEBUG
```

---

## Test: Worker Framework E2E

**File:** `test_worker_framework_e2e.py`

**Duration:** 2-3 minutes (real workflow execution)

**What It Tests:**

### ✅ Core Features
- [x] Multi-process architecture (one process per worker)
- [x] Sync workers (ThreadPoolExecutor)
- [x] Async workers (AsyncTaskRunner with event loop)
- [x] Auto-detection (def vs async def)
- [x] Polling loop (continuous with backoff)
- [x] Task execution (concurrent)
- [x] Task update (with retries)

### ✅ Configuration
- [x] Environment variable override
- [x] Hierarchical resolution (worker > global > code)
- [x] Unix format (CONDUCTOR_WORKER_ALL_*)
- [x] Domain configuration
- [x] Thread count configuration
- [x] Poll interval configuration

### ✅ Advanced Features
- [x] Dynamic batch polling
- [x] Capacity management (semaphore)
- [x] Domain-based task routing
- [x] Task definition auto-registration
- [x] JSON Schema generation (draft-07)
- [x] Complex types (dataclasses, Optional, List)
- [x] strict_schema flag
- [x] overwrite_task_def flag
- [x] task_def parameter (retry, timeout, rate limits)

### ✅ Long-Running Tasks
- [x] TaskInProgress support
- [x] Lease extension (callback_after_seconds)
- [x] Multiple polls for same task
- [x] Context preservation across polls

### ✅ Event System
- [x] All 7 event types published
  * PollStarted
  * PollCompleted
  * PollFailure
  * TaskExecutionStarted
  * TaskExecutionCompleted
  * TaskExecutionFailure
  * TaskUpdateFailure
- [x] Event listeners receive events
- [x] Event data accuracy

### ✅ Error Handling
- [x] Worker exceptions caught
- [x] Execution failures logged
- [x] Workers continue after errors
- [x] Graceful degradation

### ✅ Metrics
- [x] Metrics collected
- [x] Prometheus format
- [x] Task execution time
- [x] Poll time
- [x] Error counts

### ✅ Schema Features
- [x] Nested dataclasses
- [x] Optional[T] parameters (not required)
- [x] Parameters with defaults (not required)
- [x] List types
- [x] Complex nested structures
- [x] additionalProperties control (strict_schema)

---

## Test Workflow

The test creates and executes a workflow with these tasks:

1. **sync_worker_domain_a** - Sync worker in domain A
2. **async_worker_domain_b** - Async worker in domain B
3. **complex_schema_worker** - Complex dataclass input with schema
4. **long_running_task** - Uses TaskInProgress (3 polls)
5. **batch_test_worker** x5 - Tests batch polling (5 parallel instances)
6. **optional_params_worker** - Tests Optional[T] schema generation
7. **failing_worker** - Tests error handling

**Total:** 12 tasks in workflow

---

## Test Assertions

### Workflow Level
- Workflow completes successfully
- All tasks reach COMPLETED status
- Domain routing works correctly

### Task Level
- Sync tasks execute correctly
- Async tasks execute correctly
- Complex schema tasks receive correct input
- Long-running task polls multiple times (≥3)
- Batch tasks execute concurrently

### Event Level
- Poll started events: > 0
- Poll completed events: > 0
- Execution started events: > 0
- Execution completed events: ≥ 12 (one per task)
- Execution failed events: ≥ 1 (from failing_worker)

### Configuration Level
- Environment overrides applied
- Domain configuration working
- Thread count configured correctly

### Schema Level
- Task definitions registered
- Input/output schemas linked
- Complex types converted correctly
- Optional fields handled properly

---

## Expected Output

```
================================================================================
TEST 1: Workflow and Task Definition Registration
================================================================================
✓ Registered workflow: worker_framework_e2e_test
✓ Task definitions will be auto-registered when workers start

================================================================================
TEST 2: Worker Startup with Configuration
================================================================================
✓ Workers started with event collector
✓ Environment variable overrides applied
✓ Workers running in background

================================================================================
TEST 3: Workflow Execution
================================================================================
✓ Started workflow: abc-123-def-456
  Workflow status: RUNNING (elapsed: 0s)
  Workflow status: RUNNING (elapsed: 2s)
  Workflow status: COMPLETED (elapsed: 4s)

✓ Final workflow status: COMPLETED
  - sync_task_ref: COMPLETED
  - async_task_ref: COMPLETED
  - complex_schema_ref: COMPLETED
  - long_running_ref: COMPLETED
  - batch_test_ref_0: COMPLETED
  - batch_test_ref_1: COMPLETED
  - batch_test_ref_2: COMPLETED
  - batch_test_ref_3: COMPLETED
  - batch_test_ref_4: COMPLETED
  - optional_params_ref: COMPLETED
  - success_task_ref: COMPLETED

✓ All tasks completed successfully
✓ Long-running task used TaskInProgress (lease extension)
✓ Batch tasks processed concurrently

================================================================================
TEST 4: Event System Verification
================================================================================
Total events collected: 157
  Poll started: 45
  Poll completed: 45
  Execution started: 12
  Execution completed: 12
  Execution failed: 1
  Update failed: 0

✓ All event types published
✓ Verified 157 total events

================================================================================
TEST 5: Task Definition & Schema Registration
================================================================================
✓ Task definition exists: sync_worker_domain_a
  - Has input schema: {'name': 'sync_worker_domain_a_input', 'version': 1}
  - Has output schema: {'name': 'sync_worker_domain_a_output', 'version': 1}
✓ Task definition exists: async_worker_domain_b
  - Has input schema: {'name': 'async_worker_domain_b_input', 'version': 1}
  - Has output schema: {'name': 'async_worker_domain_b_output', 'version': 1}
✓ Task definition exists: complex_schema_worker
  - Has input schema: {'name': 'complex_schema_worker_input', 'version': 1}
  - Has output schema: {'name': 'complex_schema_worker_output', 'version': 1}
✓ Task definition exists: batch_test_worker
✓ Task definition exists: optional_params_worker

✓ All task definitions registered
✓ Schemas linked to task definitions

================================================================================
TEST 6: Domain Isolation
================================================================================
✓ Domain isolation verified (tasks routed correctly)
  - domain_a tasks → sync_worker_domain_a
  - domain_b tasks → async_worker_domain_b

================================================================================
TEST 7: Configuration Override
================================================================================
✓ Configuration override verified
  - Global poll_interval: 100ms (from env)
  - sync_worker_domain_a thread_count: 3 (from worker-specific env)

================================================================================
TEST 8: Failure Handling
================================================================================
✓ Task status: FAILED
  Reason: Intentional failure for testing (count: 1)
✓ Worker failure handled gracefully
✓ TaskExecutionFailure event published

================================================================================
TEST 9: Metrics Collection
================================================================================
✓ Metrics files found: 2
  ✓ task_poll metrics present
  ✓ task_execute metrics present

  Sample metrics:
    task_poll_total{taskType="sync_worker_domain_a"} 15.0

================================================================================
TEST 10: Comprehensive Validation Summary
================================================================================

Test Results:
  Workflow Execution            ✓ PASS
  Sync Workers                  ✓ PASS
  Async Workers                 ✓ PASS
  Domain Isolation              ✓ PASS
  Task Registration             ✓ PASS
  Schema Generation             ✓ PASS
  Event Publishing              ✓ PASS
  Configuration Override        ✓ PASS
  TaskInProgress                ✓ PASS
  Batch Polling                 ✓ PASS
  Error Handling                ✓ PASS
  Metrics Collection            ✓ PASS

================================================================================
ALL TESTS PASSED ✅
================================================================================

Features Validated:
  ✓ Multi-process architecture (one process per worker)
  ✓ Sync workers (ThreadPoolExecutor)
  ✓ Async workers (AsyncTaskRunner with event loop)
  ✓ Auto-detection (def vs async def)
  ✓ Dynamic batch polling
  ✓ Domain-based task routing
  ✓ Task definition auto-registration
  ✓ JSON Schema generation (draft-07)
  ✓ Complex types (dataclasses, Optional, List)
  ✓ strict_schema flag (additionalProperties)
  ✓ overwrite_task_def flag
  ✓ TaskInProgress (lease extension)
  ✓ Event system (7 event types)
  ✓ Event listeners (custom monitoring)
  ✓ Metrics collection (Prometheus)
  ✓ Configuration (env var override)
  ✓ Hierarchical config (worker > global > code)
  ✓ Unix format env vars (CONDUCTOR_WORKER_ALL_*)
  ✓ Error handling (graceful degradation)
  ✓ Update retries (4 attempts with backoff)
  ✓ Concurrent execution
  ✓ Capacity management (semaphore)
  ✓ Logging configuration

================================================================================
CLEANUP
================================================================================
✓ Environment variables cleaned up
✓ Metrics directory removed
```

---

## Troubleshooting

### Server Not Reachable

**Error:** `Cannot connect to Conductor server`

**Solution:**
```bash
# Verify server is running
curl http://localhost:8080/api/health

# Check environment variable
echo $CONDUCTOR_SERVER_URL

# Start local server
docker run --init -p 8080:8080 -p 5000:5000 conductoross/conductor-standalone:3.15.0
```

### Tests Timeout

**Error:** Workflow doesn't complete

**Possible Causes:**
- Workers not starting
- Domain mismatch
- Network issues

**Solution:**
- Check worker logs for errors
- Verify task names match in workflow
- Increase timeout in test (max_wait variable)

### Metrics Not Found

**Error:** No metrics files

**Possible Causes:**
- Metrics not written yet (timing issue)
- Permission issues

**Solution:**
- Wait longer before checking
- Check /tmp/conductor_e2e_test_metrics permissions

---

## Test Execution Time

- **Setup:** ~5 seconds
- **Workflow execution:** ~10-30 seconds (depends on task complexity)
- **Validation:** ~5 seconds
- **Total:** 2-3 minutes

---

## What Gets Tested

### Happy Path ✅
- Normal workflow execution
- All tasks complete
- Results returned correctly
- Schemas validated
- Events published
- Metrics collected

### Edge Cases ✅
- Empty domain handling
- Optional parameters (null values)
- TaskInProgress (multiple polls)
- Concurrent batch execution

### Failure Scenarios ✅
- Worker exceptions
- Task failures
- Error event publishing
- Graceful degradation

### Configuration ✅
- Environment variable override
- Hierarchical resolution
- Unix format (CONDUCTOR_WORKER_ALL_*)
- Worker-specific overrides

---

## Extending Tests

To add more test scenarios:

1. **Add worker** to test_worker_framework_e2e.py
2. **Add task** to workflow in test_01
3. **Add validation** in test_03 or test_10
4. **Run tests** to verify

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      conductor:
        image: conductoross/conductor-standalone:3.15.0
        ports:
          - 8080:8080
          - 5000:5000

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -e .

      - name: Wait for Conductor
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8080/api/health; do sleep 2; done'

      - name: Run integration tests
        env:
          CONDUCTOR_SERVER_URL: http://localhost:8080/api
        run: python3 -m pytest tests/integration/ -v -s
```

---

## Important Notes

1. **Real Server Required:** These tests will not work without a Conductor server
2. **Test Isolation:** Tests should clean up after themselves
3. **Idempotent:** Tests should be re-runnable
4. **Network Dependent:** May be slower on poor connections
5. **Resource Intensive:** Spawns multiple worker processes

---

## Maintenance

- Update tests when adding new features
- Keep workflow definitions up to date
- Ensure backward compatibility
- Document breaking changes

---

**Status:** Ready for use
**Last Updated:** 2025-11-30
**Maintainer:** SDK Team
