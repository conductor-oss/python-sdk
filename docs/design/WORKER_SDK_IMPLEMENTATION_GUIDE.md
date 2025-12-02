# Conductor Worker SDK Implementation Guide
# Language-Agnostic Reference for Building Worker Frameworks

**Version:** 1.0
**Date:** 2025-11-30
**Purpose:** Enable AI agents and developers to implement Conductor worker SDKs in any programming language
**Target Audience:** AI agents (Claude, GPT-4, etc.), SDK developers, architects

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Core Concepts & Terminology](#3-core-concepts--terminology)
4. [Worker Framework Architecture](#4-worker-framework-architecture)
5. [Polling & Execution Loop](#5-polling--execution-loop)
6. [Configuration System](#6-configuration-system)
7. [Event System & Interceptors](#7-event-system--interceptors)
8. [Task Definition & Schema Registration](#8-task-definition--schema-registration)
9. [Error Handling & Resilience](#9-error-handling--resilience)
10. [Performance Optimizations](#10-performance-optimizations)
11. [Testing Strategy](#11-testing-strategy)
12. [Implementation Checklist](#12-implementation-checklist)

---

## 1. Introduction

### 1.1 Purpose

This guide provides a complete specification for implementing a Conductor worker SDK in any programming language. It is designed to be:

- **Language-agnostic**: No language-specific assumptions
- **AI-friendly**: Structured for consumption by LLM agents
- **Complete**: Covers all essential features and edge cases
- **Precise**: Exact algorithms, data structures, and behaviors
- **Actionable**: Enables immediate implementation

### 1.2 What is a Conductor Worker?

A **worker** is a process that:
1. **Polls** Conductor server for pending tasks
2. **Executes** business logic for assigned tasks
3. **Updates** Conductor with task results
4. **Scales** horizontally (multiple workers per task type)
5. **Self-regulates** based on capacity

### 1.3 Design Goals

- **Process Isolation**: One process per worker for fault tolerance
- **Concurrent Execution**: Handle multiple tasks simultaneously
- **Low Latency**: 2-5ms average polling delay
- **High Throughput**: 100-1000+ tasks/second depending on workload
- **Graceful Degradation**: Never crash, always continue
- **Observability**: Comprehensive metrics and events
- **Flexibility**: Support both synchronous and asynchronous execution

---

## 2. High-Level Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Process                            │
│                   TaskHandler                               │
│  • Discovers workers                                        │
│  • Spawns worker processes                                  │
│  • Manages lifecycle                                        │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Process 1   │  │  Process 2   │  │  Process 3   │
│  Worker: W1  │  │  Worker: W2  │  │  Worker: W3  │
│  Type: Async │  │  Type: Sync  │  │  Type: Async │
├──────────────┤  ├──────────────┤  ├──────────────┤
│              │  │              │  │              │
│ TaskRunner   │  │ TaskRunner   │  │ TaskRunner   │
│ (Async or    │  │ (Sync or     │  │ (Async or    │
│  Sync mode)  │  │  Async mode) │  │  Sync mode)  │
│              │  │              │  │              │
│  Polling     │  │  Polling     │  │  Polling     │
│  Loop        │  │  Loop        │  │  Loop        │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 2.2 Process Model

**Key Principle:** One process per worker

**Rationale:**
- Fault isolation (worker crash doesn't affect others)
- True parallelism (bypass GIL-like limitations)
- Independent resource management
- Easier debugging and monitoring

**Process Lifecycle:**
1. Main process spawns child process
2. Child process creates HTTP clients (after fork)
3. Child process runs continuous polling loop
4. On shutdown, gracefully stops processing

### 2.3 Execution Models

**Auto-detection based on worker function signature:**

| Worker Type | Detection | Execution Model | Concurrency |
|-------------|-----------|-----------------|-------------|
| **Synchronous** | Function signature (non-async) | Thread pool | thread_count threads |
| **Asynchronous** | Function signature (async/coroutine) | Event loop | thread_count coroutines |

**Implementation Requirement:** SDK must auto-detect worker type and select appropriate execution model.

---

## 3. Core Concepts & Terminology

### 3.1 Essential Terms

**Task Definition (TaskDef):**
- Metadata about a task type
- Includes: retry policy, timeouts, rate limits, schemas
- Registered with Conductor server
- Can be auto-generated from worker metadata

**Task Instance (Task):**
- Specific execution of a task
- Has: task_id, workflow_id, input_data, status
- Polled by workers
- Updated with results

**Worker:**
- Function or class that implements task logic
- Has: task_definition_name, execute function, configuration
- Self-contained unit of work

**Task Result:**
- Output of task execution
- Contains: output_data, status, logs, callback_after_seconds
- Sent back to Conductor

**Polling:**
- Worker actively requests tasks from server
- Long-polling supported (server waits if no tasks)
- Batch polling (request multiple tasks at once)

**Lease:**
- Time window worker has to complete task
- Defined by responseTimeoutSeconds
- Can be extended via TaskInProgress

**Domain:**
- Optional namespace for task isolation
- Tasks in domain X only visible to workers in domain X
- Used for multi-tenancy

### 3.2 Task States

```
SCHEDULED → IN_PROGRESS → COMPLETED
                       → FAILED (will retry per retry_count)
                       → FAILED_WITH_TERMINAL_ERROR (no retry)
                       → TIMED_OUT
```

**Worker Responsibility:**
- Poll: SCHEDULED tasks
- Update: Set IN_PROGRESS, COMPLETED, FAILED, or FAILED_WITH_TERMINAL_ERROR

**Status Meanings:**
- `COMPLETED`: Task succeeded
- `FAILED`: Task failed but will be retried (regular Exception)
- `FAILED_WITH_TERMINAL_ERROR`: Task failed permanently, no retry (NonRetryableException)
- `IN_PROGRESS`: Task is running or waiting for callback
- `TIMED_OUT`: Task exceeded responseTimeoutSeconds

### 3.3 Worker Lifecycle

```
Initialize → Register Task Def → Start Polling → Execute Tasks → Update Results → Shutdown
     ↓              ↓                  ↓               ↓              ↓            ↓
  Load Config  (Optional)      Continuous Loop   Concurrent    Retry on fail  Graceful
  Create HTTP               with backoff       execution                      cleanup
  Clients
```

---

## 4. Worker Framework Architecture

### 4.1 Core Components

**Must Implement:**

1. **TaskHandler (Orchestrator)**
   - Discovers workers (via annotations/decorators/registration)
   - Spawns one process per worker
   - Manages lifecycle (start, stop, restart)
   - Provides configuration to workers
   - Coordinates metrics collection

2. **TaskRunner (Execution Engine)**
   - Runs in worker process
   - Implements polling loop
   - Executes tasks concurrently
   - Updates Conductor with results
   - Publishes events
   - Two variants: SyncTaskRunner, AsyncTaskRunner

3. **Worker (Task Implementation)**
   - Contains: task_definition_name, execute_function, configuration
   - Provides: execute(task) → task_result
   - Stateless (no workflow-specific logic)
   - Idempotent (can handle retries)

4. **Configuration Resolver**
   - Hierarchical override: worker-specific > global > code
   - Environment variable support
   - Type parsing (int, bool, string, float)
   - Validation and defaults

5. **Event Dispatcher**
   - Decouples metrics from execution
   - Publishes lifecycle events
   - Supports multiple listeners
   - Non-blocking (doesn't slow execution)

### 4.2 Class Structure (Pseudocode)

```
// Main orchestrator
class TaskHandler {
    Configuration config
    List<Worker> workers
    List<Process> processes
    MetricsSettings metricsSettings
    List<EventListener> eventListeners

    // Methods
    discover_workers() → List<Worker>
    start_processes()
    stop_processes()
    join_processes()
}

// Worker metadata
class Worker {
    String taskDefinitionName
    Function executeFunction
    Configuration config
    TaskDef taskDefTemplate  // Optional

    // Configuration fields
    Int threadCount
    String domain
    Int pollIntervalMillis
    Bool registerTaskDef
    Bool overwriteTaskDef
    Bool strictSchema
    Bool paused
}

// Execution engine (one per worker process)
class TaskRunner {
    Worker worker
    Configuration config
    HTTPClient httpClient
    EventDispatcher eventDispatcher
    MetricsCollector metricsCollector

    // Execution
    Executor executor  // Thread pool or event loop
    Set<Future> runningTasks
    Int maxWorkers

    // Methods
    run()  // Main loop
    run_once()  // Single iteration
    batch_poll(count: Int) → List<Task>
    execute_task(task: Task) → TaskResult
    update_task(result: TaskResult)
    register_task_definition()  // If configured
}

// Sync variant
class SyncTaskRunner extends TaskRunner {
    ThreadPoolExecutor executor

    run_once() {
        cleanup_completed()
        if at_capacity(): sleep(1ms); return

        available_slots = max_workers - running_tasks
        tasks = batch_poll(available_slots)

        for task in tasks:
            future = executor.submit(execute_and_update, task)
            running_tasks.add(future)
    }
}

// Async variant
class AsyncTaskRunner extends TaskRunner {
    EventLoop eventLoop
    Semaphore semaphore

    async run_once() {
        cleanup_completed()
        if at_capacity(): await sleep(1ms); return

        available_slots = max_workers - running_tasks
        tasks = await async_batch_poll(available_slots)

        for task in tasks:
            coroutine = create_task(execute_and_update(task))
            running_tasks.add(coroutine)
    }
}
```

### 4.3 Auto-Detection Algorithm

```
FUNCTION detect_worker_type(worker_function):
    IF is_coroutine_function(worker_function):
        RETURN AsyncTaskRunner
    ELSE:
        RETURN SyncTaskRunner
```

**Language-Specific Implementation:**
- Python: `inspect.iscoroutinefunction()`
- Java: Check for `CompletableFuture` return type
- Go: Check for goroutine/channel pattern
- Rust: Check for `async fn` keyword
- JavaScript/TypeScript: Check for `async function`

---

## 5. Polling & Execution Loop

### 5.1 Core Polling Loop Algorithm

```
FUNCTION run():
    apply_logging_config()
    log_worker_configuration()

    IF worker.register_task_def:
        register_task_definition()

    WHILE True:
        run_once()

FUNCTION run_once():
    // 1. Cleanup completed tasks
    cleanup_completed_tasks()

    // 2. Check capacity
    current_capacity = count(running_tasks)
    IF current_capacity >= max_workers:
        sleep(1ms)
        RETURN

    // 3. Calculate available slots
    available_slots = max_workers - current_capacity

    // 4. Adaptive backoff when empty
    IF consecutive_empty_polls > 0:
        delay = min(1ms * (2 ^ consecutive_empty_polls), poll_interval)
        IF time_since_last_poll < delay:
            sleep(delay - time_since_last_poll)
            RETURN

    // 5. Batch poll for tasks
    tasks = batch_poll(available_slots)
    last_poll_time = current_time()

    // 6. Submit tasks for execution
    IF tasks is not empty:
        consecutive_empty_polls = 0
        FOR task IN tasks:
            submit_for_execution(task)
    ELSE:
        consecutive_empty_polls += 1
```

### 5.2 Dynamic Batch Polling

**Key Principle:** Batch size adapts to current capacity

```
FUNCTION batch_poll(count: Int) → List<Task>:
    IF worker.paused:
        RETURN empty_list

    // Apply auth failure backoff
    IF auth_failures > 0:
        backoff_seconds = min(2 ^ auth_failures, 60)
        IF time_since_last_auth_failure < backoff_seconds:
            sleep(100ms)
            RETURN empty_list

    // Publish PollStarted event
    publish_event(PollStarted(task_type, worker_id, count))

    start_time = current_time()

    // Build request parameters
    params = {
        "workerid": worker_id,
        "count": count,
        "timeout": 100  // ms, server-side long poll
    }

    // Only include domain if not null/empty
    IF domain is not null AND domain != "":
        params["domain"] = domain

    // Make HTTP request
    TRY:
        tasks = http_client.batch_poll(task_type, params)
        duration = current_time() - start_time

        // Publish PollCompleted event
        publish_event(PollCompleted(task_type, duration, len(tasks)))

        // Reset auth failures on success
        auth_failures = 0

        RETURN tasks

    CATCH AuthorizationException:
        auth_failures += 1
        last_auth_failure = current_time()
        publish_event(PollFailure(task_type, duration, error))
        RETURN empty_list

    CATCH Exception as error:
        duration = current_time() - start_time
        publish_event(PollFailure(task_type, duration, error))
        RETURN empty_list
```

**Example Batch Sizes:**

```
thread_count=10, running=0  → batch_poll(10)
thread_count=10, running=10 → skip (at capacity)
thread_count=10, running=3  → batch_poll(7)
thread_count=10, running=8  → batch_poll(2)
```

### 5.3 Task Execution Flow

```
FUNCTION execute_and_update(task: Task):
    // Execute with semaphore/capacity protection
    ACQUIRE capacity_limit:
        TRY:
            result = execute_task(task)

            // Don't update if TaskInProgress
            IF result is TaskInProgress:
                RETURN

            // Update Conductor with result
            update_task(result)

        CATCH Exception as error:
            // Handle execution failure
            handle_execution_error(task, error)

        FINALLY:
            RELEASE capacity_limit
```

### 5.4 Task Execution

```
FUNCTION execute_task(task: Task) → TaskResult:
    task_name = worker.task_definition_name

    // Create initial result for context
    initial_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
        worker_id=worker.worker_id
    )

    // Set task context (for worker to access task metadata)
    set_task_context(task, initial_result)

    // Publish TaskExecutionStarted event
    publish_event(TaskExecutionStarted(task_name, task.task_id, worker_id, workflow_id))

    start_time = current_time()

    TRY:
        // Parse input parameters from task.input_data
        input_params = extract_function_parameters(worker.execute_function, task.input_data)

        // Execute worker function
        output = worker.execute_function(input_params)

        // Handle different return types
        IF output is TaskResult:
            task_result = output
        ELSE IF output is TaskInProgress:
            task_result = create_in_progress_result(task, output)
        ELSE:
            task_result = create_completed_result(task, output)

        // Merge context modifications (logs, callback_after_seconds)
        merge_context_modifications(task_result, initial_result)

        duration = current_time() - start_time

        // Publish TaskExecutionCompleted event
        publish_event(TaskExecutionCompleted(
            task_name, task.task_id, worker_id, workflow_id, duration, output_size
        ))

        RETURN task_result

    CATCH NonRetryableException as error:
        // Non-retryable exception - task fails with terminal error (NO RETRIES)
        duration = current_time() - start_time

        // Publish TaskExecutionFailure event
        publish_event(TaskExecutionFailure(
            task_name, task.task_id, worker_id, workflow_id, error, duration
        ))

        // Create FAILED_WITH_TERMINAL_ERROR result
        task_result = TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=worker.worker_id,
            status="FAILED_WITH_TERMINAL_ERROR",  // ← Terminal status, no retry
            reason_for_incompletion=error.message,
            logs=[error.stacktrace]
        )

        log_error("Task failed with terminal error (no retry): {error.message}")

        RETURN task_result

    CATCH Exception as error:
        // Regular exception - task will be retried per TaskDef.retry_count
        duration = current_time() - start_time

        // Publish TaskExecutionFailure event
        publish_event(TaskExecutionFailure(
            task_name, task.task_id, worker_id, workflow_id, error, duration
        ))

        // Create FAILED result
        task_result = TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=worker.worker_id,
            status="FAILED",  // ← Will retry per retry_count
            reason_for_incompletion=error.message,
            logs=[error.stacktrace]
        )

        RETURN task_result

    FINALLY:
        clear_task_context()
```

### 5.5 Task Update with Retries

**Critical:** Updates must be reliable. Task was executed successfully but result could be lost if update fails.

```
FUNCTION update_task(task_result: TaskResult):
    task_name = worker.task_definition_name
    retry_count = 4
    last_exception = null

    FOR attempt IN [0, 1, 2, 3]:
        IF attempt > 0:
            // Exponential backoff: 10s, 20s, 30s
            sleep(attempt * 10 seconds)

        TRY:
            response = http_client.update_task(task_result)

            log_debug("Updated task {task_result.task_id} successfully")
            RETURN response

        CATCH Exception as error:
            last_exception = error

            // Increment error metric
            increment_metric("task_update_error", task_name, error.type)

            log_error("Failed to update task (attempt {attempt+1}/{retry_count}): {error}")

    // All retries exhausted - CRITICAL FAILURE
    log_critical("Task update failed after {retry_count} attempts. Task result LOST for task_id={task_result.task_id}")

    // Publish TaskUpdateFailure event (enables external recovery)
    publish_event(TaskUpdateFailure(
        task_name,
        task_result.task_id,
        worker_id,
        workflow_id,
        last_exception,
        retry_count,
        task_result  // Include result for recovery
    ))

    RETURN null
```

**Why This Matters:** Task was executed successfully, but Conductor doesn't know. External systems must handle recovery.

### 5.6 Capacity Management

**Key Principle:** Capacity represents end-to-end task handling (execute + update)

```
// Semaphore/capacity held during BOTH execute and update
FUNCTION execute_and_update_task(task: Task):
    ACQUIRE semaphore:  // Blocks if at capacity
        result = execute_task(task)

        IF result is not TaskInProgress:
            update_task(result)

        // Semaphore released here
        // Only then can new task be polled
```

**Why:** Ensures we don't poll more tasks than we can fully handle (execute AND update).

---

## 6. Configuration System

### 6.1 Hierarchical Configuration

**Priority (Highest to Lowest):**
1. Worker-specific environment variable
2. Global environment variable
3. Code-level default

### 6.2 Configurable Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `poll_interval_millis` | Int | 100 | Polling interval in milliseconds |
| `thread_count` | Int | 1 | Max concurrent tasks (threads or coroutines) |
| `domain` | String | null | Task domain for isolation |
| `worker_id` | String | auto | Unique worker identifier |
| `poll_timeout` | Int | 100 | Server-side long poll timeout (ms) |
| `register_task_def` | Bool | false | Auto-register task definition |
| `overwrite_task_def` | Bool | true | Overwrite existing task definitions |
| `strict_schema` | Bool | false | Enforce strict JSON schema validation |
| `paused` | Bool | false | Pause worker (stop polling) |

### 6.3 Environment Variable Format

**Support ALL of these formats (tested compatibility):**

```
// Format 1: Dot notation
conductor.worker.all.{property}
conductor.worker.{task_name}.{property}

// Format 2: Unix format (UPPERCASE_WITH_UNDERSCORES) - RECOMMENDED
CONDUCTOR_WORKER_ALL_{PROPERTY}
CONDUCTOR_WORKER_{TASK_NAME}_{PROPERTY}

// Format 3: Old format (backward compatibility)
conductor_worker_{property}
CONDUCTOR_WORKER_{PROPERTY}
CONDUCTOR_WORKER_{TASK_NAME}_{PROPERTY}
```

**Examples:**
```bash
# Global configuration
export CONDUCTOR_WORKER_ALL_STRICT_SCHEMA=true
export conductor.worker.all.thread_count=20

# Worker-specific
export CONDUCTOR_WORKER_PROCESS_ORDER_THREAD_COUNT=50
export conductor.worker.validate_order.strict_schema=true
```

### 6.4 Configuration Resolution Algorithm

```
FUNCTION resolve_worker_config(
    worker_name: String,
    code_defaults: Map<String, Any>
) → Map<String, Any>:

    resolved = {}

    FOR property IN all_properties:
        // 1. Check worker-specific env var (multiple formats)
        value = get_env_value(worker_name, property)

        IF value is not null:
            resolved[property] = parse_value(value, property.type)
            CONTINUE

        // 2. Use code default if provided
        IF code_defaults contains property:
            resolved[property] = code_defaults[property]
        ELSE:
            // 3. Use system default
            resolved[property] = get_default_value(property)

    RETURN resolved

FUNCTION get_env_value(worker_name: String, property: String) → String:
    // Check in priority order:

    // 1. Worker-specific (dot notation)
    value = getenv("conductor.worker.{worker_name}.{property}")
    IF value: RETURN value

    // 2. Worker-specific (Unix format)
    value = getenv("CONDUCTOR_WORKER_{WORKER_NAME_UPPER}_{PROPERTY_UPPER}")
    IF value: RETURN value

    // 3. Global (dot notation)
    value = getenv("conductor.worker.all.{property}")
    IF value: RETURN value

    // 4. Global (Unix format)
    value = getenv("CONDUCTOR_WORKER_ALL_{PROPERTY_UPPER}")
    IF value: RETURN value

    // 5. Old formats (backward compatibility)
    value = getenv("CONDUCTOR_WORKER_{PROPERTY_UPPER}")
    IF value: RETURN value

    RETURN null
```

### 6.5 Bool Parsing

```
FUNCTION parse_bool(value: String) → Bool:
    lowercase = value.toLowerCase()

    IF lowercase IN ["true", "1", "yes"]:
        RETURN true
    ELSE IF lowercase IN ["false", "0", "no"]:
        RETURN false
    ELSE:
        THROW ParseException("Invalid boolean value: {value}")
```

---

## 7. Event System & Interceptors

### 7.1 Event Architecture

**Design Pattern:** Observer Pattern with Event Dispatcher

```
Worker Execution → Event Publishing → Multiple Listeners
                                    ├─ MetricsCollector
                                    ├─ SLA Monitor
                                    ├─ Audit Logger
                                    └─ Custom Handlers
```

### 7.2 Event Types

**Must Implement ALL 7 events:**

```
// Polling events
class PollStarted extends Event {
    String taskType
    String workerId
    Int pollCount  // Number of tasks requested
    Timestamp timestamp
}

class PollCompleted extends Event {
    String taskType
    Float durationMs
    Int tasksReceived
    Timestamp timestamp
}

class PollFailure extends Event {
    String taskType
    Float durationMs
    Exception cause
    Timestamp timestamp
}

// Execution events
class TaskExecutionStarted extends Event {
    String taskType
    String taskId
    String workerId
    String workflowInstanceId
    Timestamp timestamp
}

class TaskExecutionCompleted extends Event {
    String taskType
    String taskId
    String workerId
    String workflowInstanceId
    Float durationMs
    Int outputSizeBytes
    Timestamp timestamp
}

class TaskExecutionFailure extends Event {
    String taskType
    String taskId
    String workerId
    String workflowInstanceId
    Exception cause
    Float durationMs
    Timestamp timestamp
}

// Update events
class TaskUpdateFailure extends Event {
    String taskType
    String taskId
    String workerId
    String workflowInstanceId
    Exception cause
    Int retryCount
    TaskResult taskResult  // For recovery
    Timestamp timestamp
}
```

### 7.3 Event Dispatcher

```
class EventDispatcher {
    Map<EventType, List<EventListener>> listeners

    FUNCTION register(eventType: Type, listener: Function):
        listeners[eventType].append(listener)

    FUNCTION publish(event: Event):
        event_listeners = listeners[event.type]

        // Publish synchronously (simple) or asynchronously (non-blocking)
        // Choice depends on language capabilities

        FOR listener IN event_listeners:
            TRY:
                listener(event)
            CATCH Exception as error:
                // Isolate listener failures - don't affect task execution
                log_error("Event listener failed: {error}")
}
```

### 7.4 Event Listener Protocol

```
interface TaskRunnerEventsListener {
    on_poll_started(event: PollStarted)
    on_poll_completed(event: PollCompleted)
    on_poll_failure(event: PollFailure)
    on_task_execution_started(event: TaskExecutionStarted)
    on_task_execution_completed(event: TaskExecutionCompleted)
    on_task_execution_failure(event: TaskExecutionFailure)
    on_task_update_failure(event: TaskUpdateFailure)
}
```

**All methods optional** - implement only what's needed.

---

## 8. Task Definition & Schema Registration

### 8.1 Task Definition Registration

**When:** Worker startup (if `register_task_def=true`)

```
FUNCTION register_task_definition():
    task_name = worker.task_definition_name

    log_info("Registering task definition: {task_name}")

    TRY:
        metadata_client = create_metadata_client()

        // Generate JSON schemas from function signature
        schemas = generate_json_schemas(worker.execute_function, strict_schema)

        // Register schemas if generated
        input_schema_name = null
        output_schema_name = null

        IF schemas.input is not null:
            input_schema_name = "{task_name}_input"
            register_schema(input_schema_name, version=1, data=schemas.input)
            log_info("Registered input schema: {input_schema_name}")

        IF schemas.output is not null:
            output_schema_name = "{task_name}_output"
            register_schema(output_schema_name, version=1, data=schemas.output)
            log_info("Registered output schema: {output_schema_name}")

        // Create TaskDef
        IF worker.task_def_template is not null:
            // Use provided template (retry, timeout, rate limits)
            task_def = deep_copy(worker.task_def_template)
            task_def.name = task_name  // Override name
        ELSE:
            // Create minimal TaskDef
            task_def = TaskDef(name=task_name)

        // Link schemas
        IF input_schema_name:
            task_def.input_schema = {name: input_schema_name, version: 1}
        IF output_schema_name:
            task_def.output_schema = {name: output_schema_name, version: 1}

        // Register or update based on overwrite_task_def flag
        IF worker.overwrite_task_def:
            // Always update (overwrites existing)
            TRY:
                metadata_client.update_task_def(task_def)
                log_info("Registered/Updated task definition: {task_name}")
            CATCH NotFoundError:
                // Task doesn't exist, register new
                metadata_client.register_task_def(task_def)
                log_info("Registered task definition: {task_name}")
        ELSE:
            // Only create if doesn't exist
            existing = metadata_client.get_task_def(task_name)
            IF existing:
                log_info("Task definition exists - skipping (overwrite=false)")
                RETURN

            metadata_client.register_task_def(task_def)
            log_info("Registered task definition: {task_name}")

        // Log success with URL
        log_info("View at: {ui_host}/taskDef/{task_name}")

    CATCH 404Error:
        log_warning("Schema registry not available on server (404)")
        // Continue without schemas - worker still starts

    CATCH Exception as error:
        log_warning("Failed to register task definition: {error}")
        // Don't crash - worker continues
```

### 8.2 JSON Schema Generation

**Format:** JSON Schema draft-07

**Algorithm:**

```
FUNCTION generate_json_schemas(
    func: Function,
    task_name: String,
    strict_schema: Bool
) → {input: Schema, output: Schema}:

    signature = get_function_signature(func)

    // Generate input schema from parameters
    input_schema = generate_input_schema(signature.parameters, strict_schema)

    // Generate output schema from return type
    output_schema = generate_output_schema(signature.return_type, strict_schema)

    RETURN {input: input_schema, output: output_schema}

FUNCTION generate_input_schema(
    parameters: List<Parameter>,
    strict_schema: Bool
) → Schema:

    properties = {}
    required = []

    FOR param IN parameters:
        // Skip if no type hint
        IF param.type is unknown:
            RETURN null

        // Convert type to JSON schema
        param_schema = type_to_json_schema(param.type, strict_schema)
        IF param_schema is null:
            RETURN null

        properties[param.name] = param_schema

        // Parameter is required if:
        // 1. No default value AND
        // 2. Not Optional type
        has_default = param.default is not MISSING
        is_optional = is_optional_type(param.type)

        IF not has_default AND not is_optional:
            required.append(param.name)

    RETURN {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": not strict_schema  // false if strict, true if lenient
    }

FUNCTION type_to_json_schema(
    type_hint: Type,
    strict_schema: Bool
) → Schema:

    // Handle Optional[T] (Union[T, None])
    IF is_optional_type(type_hint):
        inner_type = extract_non_none_type(type_hint)
        inner_schema = type_to_json_schema(inner_type, strict_schema)
        inner_schema["nullable"] = true
        RETURN inner_schema

    // Handle List[T]
    IF is_list_type(type_hint):
        item_type = extract_list_item_type(type_hint)
        item_schema = type_to_json_schema(item_type, strict_schema)
        RETURN {
            "type": "array",
            "items": item_schema
        }

    // Handle Dict[String, T]
    IF is_dict_type(type_hint):
        value_type = extract_dict_value_type(type_hint)
        value_schema = type_to_json_schema(value_type, strict_schema)
        RETURN {
            "type": "object",
            "additionalProperties": value_schema
        }

    // Handle dataclass/struct/record
    IF is_dataclass(type_hint):
        properties = {}
        required = []

        FOR field IN get_fields(type_hint):
            field_schema = type_to_json_schema(field.type, strict_schema)
            properties[field.name] = field_schema

            IF field has no default:
                required.append(field.name)

        RETURN {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": not strict_schema  // Recursive!
        }

    // Handle basic types
    IF type is String: RETURN {"type": "string"}
    IF type is Int: RETURN {"type": "integer"}
    IF type is Float: RETURN {"type": "number"}
    IF type is Bool: RETURN {"type": "boolean"}
    IF type is Object/Dict: RETURN {"type": "object"}
    IF type is Array/List: RETURN {"type": "array"}

    // Unsupported type
    RETURN null

FUNCTION is_optional_type(type_hint: Type) → Bool:
    // Check if type is Union[T, None]
    IF is_union(type_hint):
        union_types = get_union_types(type_hint)
        RETURN NoneType IN union_types
    RETURN false
```

**Key Behaviors:**
- If any type can't be converted → Return null (graceful degradation)
- Unsupported types → No schema generated (worker still works)
- `strict_schema` applies recursively to ALL nested objects

---

## 9. Error Handling & Resilience

### 9.1 Error Handling Principles

1. **Never crash the worker** - All exceptions caught and logged
2. **Graceful degradation** - Continue with reduced functionality
3. **Retry on transient failures** - Exponential backoff
4. **Publish failure events** - Enable external monitoring
5. **Log at appropriate levels** - DEBUG for flow, WARNING for issues, CRITICAL for data loss

### 9.2 Auth Failure Backoff

```
GLOBAL auth_failures = 0
GLOBAL last_auth_failure = 0

FUNCTION handle_auth_failure():
    auth_failures += 1
    last_auth_failure = current_time()

    log_error("Authentication failed (failure count: {auth_failures})")

FUNCTION check_auth_backoff() → Bool:
    IF auth_failures == 0:
        RETURN false  // No backoff needed

    backoff_seconds = min(2 ^ auth_failures, 60)  // Cap at 60 seconds
    time_since_failure = current_time() - last_auth_failure

    IF time_since_failure < backoff_seconds:
        RETURN true  // In backoff period

    RETURN false

FUNCTION reset_auth_failures():
    auth_failures = 0
```

### 9.3 Adaptive Backoff for Empty Polls

```
GLOBAL consecutive_empty_polls = 0
GLOBAL last_poll_time = 0

FUNCTION handle_empty_poll():
    consecutive_empty_polls += 1

FUNCTION handle_successful_poll():
    consecutive_empty_polls = 0

FUNCTION should_backoff() → Bool:
    IF consecutive_empty_polls == 0:
        RETURN false

    now = current_time()
    time_since_last = now - last_poll_time

    // Exponential: 1ms, 2ms, 4ms, 8ms, ... up to poll_interval
    // Cap exponent at 10 to prevent overflow
    capped_empty_polls = min(consecutive_empty_polls, 10)
    min_delay = min(1ms * (2 ^ capped_empty_polls), poll_interval)

    IF time_since_last < min_delay:
        RETURN true  // Need to wait longer

    RETURN false
```

**Behavior:**
- Empty poll 1 → Wait 1ms
- Empty poll 2 → Wait 2ms
- Empty poll 3 → Wait 4ms
- Empty poll 4 → Wait 8ms
- ...
- Empty poll 10+ → Wait poll_interval

---

## 10. Performance Optimizations

### 10.1 HTTP/2 Support

**Requirement:** Use HTTP/2 for conductor API calls

**Benefits:**
- Request multiplexing (multiple requests on single connection)
- Header compression
- Higher throughput compared to HTTP/1.1

**Configuration:**
- Connection pool: 100 connections
- Keep-alive: 50 connections
- Timeout: Configurable

### 10.2 Connection Pooling

```
class HTTPClient {
    ConnectionPool pool

    CONSTRUCTOR():
        pool = create_pool(
            max_connections=100,
            max_keepalive=50,
            timeout=30 seconds,
            http2=true
        )
}
```

### 10.3 Batch Polling

**Always use batch poll** (even for 1 task) for consistency:

```
// Good: Batch poll
tasks = batch_poll(count=available_slots)

// Bad: Single poll in loop
FOR i IN 0 to available_slots:
    task = poll_single()  // ❌ Don't do this
```

**Benefits:**
- Fewer API calls compared to single polling
- Lower server load
- Better throughput

### 10.4 Immediate Cleanup

**Critical for low latency:**

```
FUNCTION run_once():
    // Clean up FIRST (before capacity check)
    cleanup_completed_tasks()  // Removes done tasks from tracking

    // NOW check capacity
    current_capacity = count(running_tasks)
    ...
```

**Why:** Completed tasks must be removed immediately to free capacity slots.

---

## 11. Testing Strategy

### 11.1 Unit Testing Approach

**Mock External Dependencies:**
- HTTP client (Conductor API calls)
- Metadata client
- Schema client

**Test Real Components:**
- Event system
- Configuration resolution
- Schema generation
- Serialization/deserialization

**Example Test Structure:**

```
TEST test_async_worker_end_to_end():
    // Setup mocks
    mock_http = create_mock_http_client()
    mock_http.batch_poll.returns([mock_task])
    mock_http.update_task.returns(success)

    // Create worker
    async_worker = create_async_worker()
    task_runner = AsyncTaskRunner(async_worker, mock_http)

    // Execute one iteration
    await task_runner.run_once()

    // Verify
    ASSERT mock_http.batch_poll.called_once
    ASSERT mock_http.update_task.called_once
    ASSERT task executed successfully
```

### 11.2 Test Categories

**Must Have:**

1. **Core Functionality Tests**
   - Poll → Execute → Update flow
   - Batch polling with dynamic capacity
   - Concurrent execution
   - Task result serialization

2. **Configuration Tests**
   - Environment variable override
   - Priority hierarchy (worker > global > code)
   - All property types (int, bool, string)

3. **Error Handling Tests**
   - Worker exceptions
   - HTTP errors (401, 404, 500)
   - Token refresh failures
   - Update retry logic

4. **Edge Case Tests**
   - Empty polls (backoff behavior)
   - Paused workers (stop polling)
   - Capacity limits (don't over-poll)
   - None/null returns
   - TaskInProgress returns

5. **Event System Tests**
   - All 7 events published
   - Multiple listeners receive events
   - Listener failures don't break worker
   - Event data accuracy

6. **Schema Generation Tests** (if implemented)
   - Basic types
   - Optional types
   - Collections
   - Nested structures
   - strict_schema flag

### 11.3 Integration Tests

**With Real Server:**
- End-to-end workflow execution
- Multiple workers concurrent
- Error scenarios
- Performance benchmarks

---

## 12. Implementation Checklist

### 12.1 Phase 1: Core Worker (MVP)

- [ ] TaskHandler - discovers and spawns workers
- [ ] Worker class - holds task metadata
- [ ] SyncTaskRunner - basic polling loop
- [ ] HTTP client - batch_poll and update_task
- [ ] Configuration - basic property resolution
- [ ] Logging - structured logging
- [ ] Tests - core functionality (poll, execute, update)

**Deliverable:** Workers can poll, execute, and update tasks

---

### 12.2 Phase 2: Concurrency & Performance

- [ ] Thread pool / coroutine execution
- [ ] Dynamic batch polling
- [ ] Capacity management
- [ ] Adaptive backoff for empty polls
- [ ] Auth failure backoff
- [ ] Immediate cleanup for low latency
- [ ] Tests - concurrency, capacity, backoff

**Deliverable:** High-performance concurrent execution

---

### 12.3 Phase 3: Configuration System

- [ ] Environment variable support (all formats)
- [ ] Hierarchical resolution (worker > global > code)
- [ ] Configuration logging on startup
- [ ] All 10+ properties supported
- [ ] Tests - env var override, priority, types

**Deliverable:** Production-ready configuration

---

### 12.4 Phase 4: Event System

- [ ] Event classes (7 events)
- [ ] EventDispatcher
- [ ] Event listener protocol
- [ ] Publish events at correct points
- [ ] MetricsCollector as event listener
- [ ] Tests - all events, multiple listeners, isolation

**Deliverable:** Decoupled observability

---

### 12.5 Phase 5: Advanced Features

- [ ] AsyncTaskRunner (if language supports async)
- [ ] Auto-detection (sync vs async)
- [ ] JSON Schema generation
- [ ] Task definition registration
- [ ] TaskUpdateFailure event
- [ ] Update retry logic (4 attempts, exponential backoff)
- [ ] Tests - async execution, schema generation, registration

**Deliverable:** Feature parity with reference implementation

---

### 12.6 Phase 6: Production Readiness

- [ ] TaskInProgress support (lease extension)
- [ ] Paused worker support
- [ ] Empty domain handling
- [ ] 404 graceful handling
- [ ] Comprehensive error messages
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Documentation

**Deliverable:** Production-ready SDK

---

## 13. Detailed Specifications

### 13.1 HTTP API Endpoints

**Batch Poll:**
```
POST /api/tasks/poll/batch/{taskType}
Query Params:
  - workerid: string (required)
  - count: int (required, 1-100)
  - timeout: int (optional, default 100ms)
  - domain: string (optional, only if not null/empty)

Response: List<Task>
```

**Update Task:**
```
POST /api/tasks
Body: TaskResult (JSON)

Response: string (task status)
```

**Register Task Definition:**
```
POST /api/metadata/taskdefs
Body: List<TaskDef>

Response: void
```

**Update Task Definition:**
```
PUT /api/metadata/taskdefs/{taskDefName}
Body: TaskDef

Response: void
```

**Register Schema:**
```
POST /api/schema
Body: SchemaDef {
  name: string
  version: int
  type: "JSON" | "AVRO" | "PROTOBUF"
  data: object (the schema itself)
}

Response: void
```

### 13.2 Data Structures

**Task:**
```json
{
  "taskId": "uuid",
  "taskDefName": "string",
  "workflowInstanceId": "uuid",
  "inputData": {},
  "status": "SCHEDULED | IN_PROGRESS | COMPLETED | FAILED",
  "pollCount": 0,
  "callbackAfterSeconds": 0,
  "responseTimeoutSeconds": 300
}
```

**TaskResult:**
```json
{
  "taskId": "uuid",
  "workflowInstanceId": "uuid",
  "workerId": "string",
  "status": "IN_PROGRESS | COMPLETED | FAILED | FAILED_WITH_TERMINAL_ERROR",
  "outputData": {},
  "reasonForIncompletion": "string",
  "callbackAfterSeconds": 0,
  "logs": [
    {"message": "string", "taskId": "uuid", "createdTime": 123456789}
  ]
}
```

**Status Values:**
- `IN_PROGRESS`: Task is executing or waiting for callback
- `COMPLETED`: Task succeeded
- `FAILED`: Task failed, will retry per retry_count (from regular Exception)
- `FAILED_WITH_TERMINAL_ERROR`: Task failed permanently, no retry (from NonRetryableException)

**TaskDef:**
```json
{
  "name": "string",
  "description": "string",
  "retryCount": 3,
  "retryLogic": "FIXED | LINEAR_BACKOFF | EXPONENTIAL_BACKOFF",
  "retryDelaySeconds": 10,
  "timeoutSeconds": 300,
  "timeoutPolicy": "RETRY | TIME_OUT_WF | ALERT_ONLY",
  "responseTimeoutSeconds": 60,
  "concurrentExecLimit": 10,
  "rateLimitPerFrequency": 100,
  "rateLimitFrequencyInSeconds": 60,
  "inputSchema": {"name": "string", "version": 1},
  "outputSchema": {"name": "string", "version": 1}
}
```

---

## 14. Language-Specific Considerations

### 14.1 Sync vs Async Support

**If Language Has Native Async:**
- Implement both SyncTaskRunner and AsyncTaskRunner
- Auto-detect based on function signature
- AsyncTaskRunner uses event loop/promises/futures
- Single event loop per worker process
- Semaphore for concurrency control

**If Language Doesn't Have Native Async:**
- Implement SyncTaskRunner only
- Use thread pool for concurrency
- May simulate async with callbacks/channels

### 14.2 Multiprocessing vs Multithreading

**Preferred:** One process per worker

**Alternative:** One thread per worker (if processes expensive)

**Why Process Isolation:**
- Fault tolerance
- True parallelism (no GIL equivalent)
- Independent resource management

### 14.3 HTTP Client Selection

**Requirements:**
- HTTP/2 support
- Connection pooling
- Async/await support (for AsyncTaskRunner)
- Timeout configuration
- Retry logic

**Examples:**
- Python: httpx (async), requests (sync)
- Java: OkHttp, Apache HttpClient
- Go: net/http with http2
- Rust: reqwest, hyper
- JavaScript: axios, node-fetch

### 14.4 JSON Serialization

**Must Handle:**
- Nested objects
- Arrays
- Null values
- Type conversion (string ↔ number)
- ISO 8601 timestamps

**Dataclass/Struct Support:**
- Convert dataclass to dict/JSON
- Convert dict/JSON to dataclass (with type hints)

---

## 15. Metrics & Monitoring

### 15.1 Required Metrics

**Via Event System (Recommended):**

Implement MetricsCollector as EventListener:

```
class MetricsCollector implements TaskRunnerEventsListener {
    on_poll_started(event):
        increment_counter("task_poll_total", labels={taskType: event.taskType})

    on_poll_completed(event):
        record_histogram("task_poll_time_seconds", event.durationMs / 1000)
        increment_counter("task_poll_total", labels={taskType: event.taskType})

    on_task_execution_completed(event):
        record_histogram("task_execute_time_seconds", event.durationMs / 1000)
        record_histogram("task_result_size_bytes", event.outputSizeBytes)

    on_task_execution_failure(event):
        increment_counter("task_execute_error_total",
            labels={taskType: event.taskType, exception: event.cause.type})

    on_task_update_failure(event):
        increment_counter("task_update_failed_total",
            labels={taskType: event.taskType})
        // CRITICAL: Alert operations team
}
```

**Metric Names (Prometheus format):**
- `task_poll_total{taskType}`
- `task_poll_time_seconds{taskType,quantile}`
- `task_execute_time_seconds{taskType,quantile}`
- `task_execute_error_total{taskType,exception}`
- `task_result_size_bytes{taskType,quantile}`
- `task_update_error_total{taskType,exception}`
- `task_update_failed_total{taskType}` ← CRITICAL metric

---

## 16. Special Features

### 16.1 Exception Handling - Terminal vs Retryable Failures

**Critical Design Decision:** Tasks can fail in two ways:

#### A. Retryable Failures (Regular Exception)

**Use Case:** Temporary/transient errors that may succeed on retry

```
class RegularException extends Exception {
    // Standard exception
}

// Examples of retryable failures:
- Network timeout
- Database connection lost
- Service temporarily unavailable
- Rate limit exceeded
- Temporary resource contention
```

**Behavior:**
- Task status: `FAILED`
- Conductor will retry based on `TaskDef.retry_count`
- Retry logic: FIXED, LINEAR_BACKOFF, or EXPONENTIAL_BACKOFF
- Each retry counts toward retryCount limit

**Implementation:**
```
CATCH Exception as error:
    task_result.status = "FAILED"
    task_result.reason_for_incompletion = error.message
    // Conductor will retry this task
```

#### B. Non-Retryable Failures (NonRetryableException)

**Use Case:** Permanent errors where retry would produce same result

```
class NonRetryableException extends Exception {
    // Marks task as terminally failed - no retries
}

// Examples of non-retryable failures:
- Business validation failure (invalid data format)
- Authorization failure (user lacks permission)
- Resource not found (entity doesn't exist)
- Configuration error (missing required config)
- Data integrity violation (constraint violation)
- Unsupported operation (feature not available)
```

**Behavior:**
- Task status: `FAILED_WITH_TERMINAL_ERROR`
- Conductor does **NOT** retry (even if `retry_count > 0`)
- Task immediately moves to terminal state
- Workflow can handle via failure workflow or switch task

**Implementation:**
```
CATCH NonRetryableException as error:
    task_result.status = "FAILED_WITH_TERMINAL_ERROR"
    task_result.reason_for_incompletion = error.message
    log_error("Task failed with terminal error (no retry): {error}")
    // Conductor will NOT retry this task
```

**Important:** NonRetryableException must be caught **BEFORE** general Exception handler

```
TRY:
    result = execute_worker()

CATCH NonRetryableException:  // ← Check FIRST
    status = "FAILED_WITH_TERMINAL_ERROR"

CATCH Exception:  // ← Check SECOND (catches everything else)
    status = "FAILED"
```

#### Decision Matrix: When to Use Each Exception

| Scenario | Exception Type | Reason |
|----------|---------------|--------|
| Network timeout | Exception | May work on retry |
| Database unavailable | Exception | Temporary issue |
| Invalid input format | NonRetryableException | Data won't change |
| User not authorized | NonRetryableException | Permission won't change |
| Order not found | NonRetryableException | Order still won't exist |
| API rate limit | Exception | Will succeed after cooldown |
| Missing config | NonRetryableException | Config won't appear |
| Null pointer | Exception | Could be transient |
| Validation failure | NonRetryableException | Data won't become valid |

#### Example Usage

```
FUNCTION validate_and_process_order(order_id: String) → Result:
    // Get order from database
    order = database.get_order(order_id)

    // Order doesn't exist - retry won't help
    IF order is null:
        THROW NonRetryableException("Order {order_id} not found")

    // Order cancelled - business rule, retry won't help
    IF order.status == "CANCELLED":
        THROW NonRetryableException("Cannot process cancelled order")

    // Invalid amount - data validation, retry won't help
    IF order.amount <= 0:
        THROW NonRetryableException("Invalid amount: {order.amount}")

    // User not authorized - permission issue, retry won't help
    IF not has_permission(current_user, order):
        THROW NonRetryableException("User not authorized for order {order_id}")

    // Database temporarily down - retry might help
    IF not database.is_healthy():
        THROW Exception("Database temporarily unavailable")

    // Network issue with payment gateway - retry might help
    TRY:
        payment_result = payment_gateway.process(order)
    CATCH NetworkException:
        THROW Exception("Payment gateway unreachable")

    RETURN payment_result
```

#### Benefits

1. **Faster Failure Recovery:** Terminal errors fail immediately without wasting retry attempts
2. **Resource Efficiency:** Don't retry operations that will always fail
3. **Clear Intent:** Code explicitly indicates permanent vs temporary failures
4. **Workflow Control:** Workflows can handle terminal failures differently
5. **Observability:** Metrics distinguish retryable vs non-retryable failures

---

### 16.2 Long-Running Tasks (TaskInProgress)

**Pattern:** Return TaskInProgress to extend lease

```
class TaskInProgress {
    Map<String, Any> output  // Intermediate output
    Int callbackAfterSeconds  // When to re-poll
}

FUNCTION execute_long_running_task(task: Task) → TaskResult | TaskInProgress:
    context = get_task_context()
    poll_count = context.poll_count

    // Do some work
    progress = process_chunk(task.input_data, poll_count)

    IF not complete:
        // Tell Conductor: "I'm not done yet, call me back"
        RETURN TaskInProgress(
            output={progress: progress.percentage},
            callbackAfterSeconds=60
        )
    ELSE:
        // Task complete
        RETURN TaskResult(status="COMPLETED", output={result: data})
```

**Task Result Conversion:**

```
IF output is TaskInProgress:
    task_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
        worker_id=worker.worker_id,
        status="IN_PROGRESS",
        output_data=output.output,
        callback_after_seconds=output.callbackAfterSeconds
    )
```

### 16.2 Task Context

**Provide to Worker Function:**

```
class TaskContext {
    String task_id
    String workflow_instance_id
    Int poll_count
    Int retry_count

    // Methods
    add_log(message: String)
    set_callback_after(seconds: Int)
}

// Thread-local or async-local storage
FUNCTION set_task_context(task: Task, initial_result: TaskResult):
    context = TaskContext(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
        poll_count=task.poll_count,
        retry_count=task.retry_count
    )
    store_in_thread_local(context)

FUNCTION get_task_context() → TaskContext:
    RETURN get_from_thread_local()

FUNCTION clear_task_context():
    remove_from_thread_local()
```

**Usage in Worker:**

```
FUNCTION my_worker(data: Input) → Output:
    ctx = get_task_context()

    ctx.add_log("Processing started")

    // Do work
    result = process(data)

    ctx.add_log("Processing completed")

    RETURN result
```

---

## 17. Best Practices

### 17.1 Worker Design

✅ **DO:**
- Keep workers stateless
- Make workers idempotent (handle retries)
- Use small, focused workers (single responsibility)
- Return structured data (not primitive types)
- Add logs for debugging
- Handle expected errors gracefully

❌ **DON'T:**
- Store workflow state in worker
- Implement workflow logic in workers
- Make external calls without timeouts
- Use blocking I/O in async workers
- Ignore errors silently

### 17.2 Configuration

✅ **DO:**
- Provide sensible defaults
- Support environment variable override
- Log resolved configuration on startup
- Validate configuration values
- Use hierarchical resolution

❌ **DON'T:**
- Hardcode configuration
- Ignore environment variables
- Use magic numbers
- Skip validation

### 17.3 Error Handling

✅ **DO:**
- Catch all exceptions
- Log with appropriate levels
- Retry on transient failures
- Publish failure events
- Continue execution (graceful degradation)

❌ **DON'T:**
- Let workers crash
- Swallow exceptions silently
- Retry infinitely
- Block on errors

---

## 18. Implementation Priorities

### Priority 1: CRITICAL (MVP)
- Polling loop
- Task execution
- Task update
- Configuration (basic)
- HTTP client

### Priority 2: HIGH (Production)
- Batch polling
- Concurrent execution
- Retry logic for updates
- Error handling
- Event system (basic)

### Priority 3: MEDIUM (Enhanced)
- Adaptive backoff
- Auth failure backoff
- Metrics collection
- Task definition registration
- Async support

### Priority 4: LOW (Optional)
- JSON Schema generation
- Complex type support
- Advanced events
- Performance optimizations

---

## 19. Verification & Validation

### 19.1 Correctness Checks

**Must Verify:**

1. **Dynamic Batch Polling:**
   - Batch size = thread_count - currently_running_tasks
   - Never polls when at capacity
   - Adapts as tasks complete

2. **Capacity Management:**
   - Semaphore/capacity held during execute AND update
   - Available slots = tasks fully handled (not just executing)
   - No over-polling

3. **Update Retries:**
   - Exactly 4 attempts
   - Backoff: 10s, 20s, 30s
   - TaskUpdateFailure event on final failure
   - Idempotent (safe to retry)

4. **Configuration Priority:**
   - Worker-specific env overrides global env
   - Global env overrides code
   - All formats work (dot, Unix, old)

5. **Event Publishing:**
   - All 7 events published at correct times
   - Event data accurate
   - Listener failures don't break worker

6. **Graceful Degradation:**
   - Worker continues on failures
   - Warnings logged appropriately
   - No crashes

### 19.2 Performance Targets

**Must Achieve:**
- Low polling latency (single-digit milliseconds)
- High throughput for sync workers
- Higher throughput for async workers (I/O-bound workloads)
- Reduced API calls via batch polling
- Efficient memory usage per worker process

### 19.3 Compatibility Matrix

| Feature | Sync Workers | Async Workers | Required |
|---------|-------------|---------------|----------|
| Polling loop | ✅ | ✅ | YES |
| Batch polling | ✅ | ✅ | YES |
| Dynamic capacity | ✅ | ✅ | YES |
| Adaptive backoff | ✅ | ✅ | YES |
| Update retries | ✅ | ✅ | YES |
| Event system | ✅ | ✅ | YES |
| Configuration | ✅ | ✅ | YES |
| Schema generation | ✅ | ✅ | NO |
| Task def registration | ✅ | ✅ | NO |

---

## 20. Reference Implementation

**Python SDK** serves as reference implementation:

**Files to Study:**
- `src/conductor/client/automator/task_runner.py` - Sync worker implementation
- `src/conductor/client/automator/async_task_runner.py` - Async worker implementation
- `src/conductor/client/automator/task_handler.py` - Orchestrator
- `src/conductor/client/worker/worker_config.py` - Configuration resolution
- `src/conductor/client/event/task_runner_events.py` - Event definitions
- `src/conductor/client/automator/json_schema_generator.py` - Schema generation

**Key Algorithms:**
- Polling loop: See run_once() in task_runner.py
- Batch polling: See __batch_poll_tasks()
- Update retries: See __update_task()
- Config resolution: See resolve_worker_config()
- Schema generation: See generate_json_schema_from_function()

---

## 21. Common Pitfalls & Solutions

### 21.1 Pitfall: Over-Polling

**Problem:** Polling for more tasks than can be handled

**Solution:** Dynamic batch sizing
```
available_slots = thread_count - currently_running_tasks
tasks = batch_poll(available_slots)
```

### 21.2 Pitfall: Update Without Retry

**Problem:** Task executed but update fails → Result lost

**Solution:** Retry with exponential backoff + TaskUpdateFailure event

### 21.3 Pitfall: Semaphore Released Before Update

**Problem:** New task polled before old task updated → Over capacity

**Solution:** Hold semaphore during execute AND update

### 21.4 Pitfall: Hardcoded additionalProperties

**Problem:** Can't control schema strictness

**Solution:** Use strict_schema flag, default to lenient (true)

### 21.5 Pitfall: Empty Domain String

**Problem:** Passing domain="" to API (invalid)

**Solution:** Only include domain if not null AND not empty

### 21.6 Pitfall: Optional[T] Required

**Problem:** Optional parameters marked as required in schema

**Solution:** Check if type is Optional, exclude from required array

---

## 22. Success Criteria

### 22.1 Functional Requirements

✅ Workers poll for and execute tasks
✅ Concurrent execution (configurable concurrency)
✅ Task results updated to Conductor
✅ Configuration via environment variables
✅ Both sync and async workers supported
✅ Graceful error handling (worker never crashes)
✅ Event system for observability

### 22.2 Non-Functional Requirements

✅ Low polling latency
✅ High throughput
✅ Memory efficient
✅ CPU efficient
✅ Network efficient (batch polling, connection pooling)
✅ Observable (metrics, events, logs)

### 22.3 Test Coverage

✅ Unit tests: Comprehensive coverage
✅ Integration tests: End-to-end workflows
✅ Edge cases: All critical paths tested
✅ Performance tests: Benchmark results documented

---

## 23. Summary

### 23.1 Must-Have Features

1. **Polling Loop** - Continuous, with batch polling and backoff
2. **Task Execution** - Concurrent, with capacity management
3. **Task Update** - With retries (4x, exponential backoff)
4. **Configuration** - Hierarchical, environment variable override
5. **Error Handling** - Graceful degradation, comprehensive logging
6. **Exception Handling** - NonRetryableException for terminal failures
7. **Event System** - 7 events, decoupled metrics
8. **Auto-Detection** - Sync vs async based on function signature

### 23.2 Should-Have Features

9. **Task Definition Registration** - Auto-register from code
10. **JSON Schema Generation** - From type hints/annotations
11. **TaskUpdateFailure Event** - Critical failure monitoring
12. **TaskInProgress Support** - Long-running task pattern
13. **Strict Schema Mode** - Control additionalProperties

### 23.3 Implementation Steps

1. Start with SyncTaskRunner (simpler)
2. Add configuration system
3. Add event system
4. Add AsyncTaskRunner (if supported)
5. Add schema generation
6. Add task registration
7. Optimize and tune

### 23.4 Testing Approach

1. Unit tests with mocked HTTP (fast, no server)
2. Integration tests with real server
3. Performance benchmarks
4. Load testing

---

## 24. AI Agent Instructions

If you are an AI agent implementing a Conductor worker SDK:

### 24.1 Read This Guide First

- Understand high-level architecture (Section 2)
- Understand core concepts (Section 3)
- Study component design (Section 4)

### 24.2 Implement In Order

1. Phase 1: Core Worker (MVP)
2. Phase 2: Concurrency
3. Phase 3: Configuration
4. Phase 4: Events
5. Phase 5: Advanced Features
6. Phase 6: Production Hardening

### 24.3 Reference Implementation

- Study Python SDK code (files listed in Section 20)
- Follow algorithms exactly (Sections 5, 6, 8, 9)
- Match behavior (use test cases as specification)

### 24.4 Validation

- Run thought experiments (Section 19.1)
- Write tests first (Section 11)
- Verify against checklist (Section 12)
- Meet success criteria (Section 22)

### 24.5 Key Behaviors to Match

- **Dynamic batch polling:** Batch size = capacity - running
- **Update retries:** 4 attempts, 10s/20s/30s backoff
- **Adaptive backoff:** Exponential on empty polls
- **Event publishing:** All 7 events at correct times
- **Graceful degradation:** Never crash worker
- **Configuration priority:** Worker > global > code

---

## 25. Appendix: Algorithms

### A. Cleanup Completed Tasks

```
FUNCTION cleanup_completed_tasks():
    running_tasks = filter(running_tasks, task => not task.done())
```

### B. Extract Function Parameters

```
FUNCTION extract_function_parameters(
    func: Function,
    input_data: Map
) → Map:

    signature = get_signature(func)
    params = {}

    FOR parameter IN signature.parameters:
        param_name = parameter.name
        param_type = parameter.type

        IF input_data contains param_name:
            value = input_data[param_name]

            // Convert if needed (dataclass, enum, etc.)
            IF param_type is dataclass:
                params[param_name] = convert_to_dataclass(value, param_type)
            ELSE:
                params[param_name] = value
        ELSE IF parameter has default:
            params[param_name] = parameter.default
        ELSE:
            params[param_name] = null

    RETURN params
```

### C. Merge Context Modifications

```
FUNCTION merge_context_modifications(
    task_result: TaskResult,
    context_result: TaskResult
):
    // Merge logs
    IF context_result.logs is not empty:
        task_result.logs.extend(context_result.logs)

    // Merge callback_after_seconds (context takes precedence)
    IF context_result.callback_after_seconds:
        task_result.callback_after_seconds = context_result.callback_after_seconds

    // Merge output_data if both are dicts
    IF both are dicts:
        task_result.output_data = merge_dicts(
            context_result.output_data,
            task_result.output_data  // Task result takes precedence
        )
```

---

## 26. Glossary

**AsyncTaskRunner:** Worker execution engine using event loop/coroutines for async workers
**Batch Polling:** Requesting multiple tasks in single API call
**Capacity:** Maximum concurrent tasks a worker can handle (thread_count)
**Domain:** Optional namespace for task isolation
**Event Dispatcher:** Component that publishes lifecycle events to listeners
**FAILED Status:** Task failed but will be retried per retry_count configuration
**FAILED_WITH_TERMINAL_ERROR:** Task failed permanently, no retries (from NonRetryableException)
**Graceful Degradation:** Continue operating with reduced functionality on errors
**Lease:** Time window worker has to complete task before timeout
**NonRetryableException:** Exception that marks task as terminally failed (no retries)
**Polling Loop:** Continuous loop that requests tasks from server
**Semaphore:** Concurrency control mechanism (limits concurrent executions)
**SyncTaskRunner:** Worker execution engine using thread pool for sync workers
**Task Context:** Thread-local storage providing task metadata to worker function
**TaskDef:** Task definition metadata (retry, timeout, rate limits)
**TaskInProgress:** Return type for long-running tasks (extends lease)
**TaskUpdateFailure:** Critical event when task result can't be sent to server after retries
**Thread Count:** Maximum concurrent tasks (threads for sync, coroutines for async)
**Worker:** Function or class implementing task execution logic

---

## 27. Version History

**v1.0 (2025-11-30):**
- Initial release
- Based on Python SDK v1.3.0+ implementation
- Includes all production features
- AI agent optimized

---

## 28. Contributing

This is a living document. If you implement a worker SDK in another language:

1. Validate against this specification
2. Report discrepancies or unclear areas
3. Suggest improvements
4. Share lessons learned

---

**Document Status:** Complete
**Implementation Difficulty:** Moderate
**Estimated Implementation Time:** 2-4 weeks (with testing)
**Prerequisites:** HTTP client library, JSON parser, concurrency primitives
**Reference Implementation:** Python SDK (v1.3.0+)

---

**END OF GUIDE**

For questions or clarifications, refer to:
- Python SDK source code: https://github.com/conductor-oss/conductor-python
- Conductor documentation: https://orkes.io/content
- This guide is self-contained and complete for AI agent consumption
