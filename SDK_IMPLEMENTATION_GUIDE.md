# Conductor SDK Architecture & Implementation Guide

A comprehensive guide for implementing Conductor SDKs across all languages (Java, Go, C#, JavaScript/TypeScript, Clojure) based on the Python SDK reference architecture.

## Executive Summary

This guide provides a complete blueprint for creating or refactoring Conductor SDKs to match the architecture, API design, and documentation standards established in the Python SDK. Each language should maintain its idiomatic patterns while following the core architectural principles.

---

## 🏗️ SDK Architecture Blueprint

### Core Architecture Layers

```
┌─────────────────────────────────────────────────┐
│              Application Layer                   │
│         (User's Application Code)                │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│            High-Level Clients                    │
│   (OrkesClients, WorkflowExecutor, Workers)      │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│         Domain-Specific Clients                  │
│  (TaskClient, WorkflowClient, SecretClient...)   │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│             Orkes Implementations                │
│     (OrkesTaskClient, OrkesWorkflowClient...)    │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│              Resource API Layer                  │
│    (TaskResourceApi, WorkflowResourceApi...)     │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│              HTTP/API Client                     │
│         (ApiClient, HTTP Transport)              │
└─────────────────────────────────────────────────┘
```

### Client Hierarchy Pattern

```
AbstractClient (Interface/ABC)
    ↑
OrkesBaseClient (Shared Implementation)
    ↑
OrkesSpecificClient (Concrete Implementation)
```

---

## 📦 Package Structure

### Standard Package Organization

```
conductor-{language}/
├── src/
│   └── conductor/
│       ├── client/
│       │   ├── {domain}_client.{ext}      # Abstract interfaces
│       │   ├── orkes/
│       │   │   ├── orkes_base_client.{ext}
│       │   │   ├── orkes_{domain}_client.{ext}
│       │   │   └── models/
│       │   ├── http/
│       │   │   ├── api/                   # Generated from OpenAPI
│       │   │   │   └── *_resource_api.{ext}
│       │   │   ├── models/                # Generated models
│       │   │   └── api_client.{ext}
│       │   ├── automator/
│       │   │   ├── task_runner.{ext}
│       │   │   └── async_task_runner.{ext}
│       │   ├── configuration/
│       │   │   ├── configuration.{ext}
│       │   │   └── settings/
│       │   ├── worker/
│       │   │   ├── worker_task.{ext}
│       │   │   └── worker_discovery.{ext}
│       │   └── workflow/
│       │       ├── conductor_workflow.{ext}
│       │       └── task/
├── examples/
│   ├── workers_e2e.{ext}                  # End-to-end example
│   ├── {feature}_journey.{ext}            # 100% API coverage demos
│   └── README.md                          # Examples catalog
├── docs/
│   ├── AUTHORIZATION.md                   # 49 APIs
│   ├── METADATA.md                        # 21 APIs
│   ├── INTEGRATION.md                     # 28+ providers
│   ├── TASK_MANAGEMENT.md                 # 11 APIs
│   ├── SECRET_MANAGEMENT.md               # 9 APIs
│   ├── WORKFLOW_TESTING.md
│   └── ...
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 🎯 Implementation Checklist

### Phase 1: Core Infrastructure

#### 1.1 Configuration System

- [ ] Create Configuration class with builder pattern
- [ ] Support environment variables
- [ ] Implement hierarchical configuration (all → domain → task)
- [ ] Add authentication settings (key/secret, token)
- [ ] Include retry configuration
- [ ] Add connection pooling settings

#### 1.2 HTTP/API Layer

- [ ] Generate models from OpenAPI specification
- [ ] Generate resource API classes
- [ ] Implement ApiClient with:
  - [ ] Connection pooling
  - [ ] Retry logic with exponential backoff
  - [ ] Request/response interceptors
  - [ ] Error handling and mapping
  - [ ] Metrics collection hooks

#### 1.3 Base Client Architecture

- [ ] Create abstract base clients (interfaces)
- [ ] Implement OrkesBaseClient aggregating all APIs
- [ ] Add proper dependency injection
- [ ] Implement client factory pattern

### Phase 2: Domain Clients

For each domain, implement:

#### 2.1 Task Client

```
Abstract Interface (11 methods):
- poll_task(task_type, worker_id?, domain?)
- batch_poll_tasks(task_type, worker_id?, count?, timeout?, domain?)
- get_task(task_id)
- update_task(task_result)
- update_task_by_ref_name(workflow_id, ref_name, status, output, worker_id?)
- update_task_sync(workflow_id, ref_name, status, output, worker_id?)
- get_queue_size_for_task(task_type)
- add_task_log(task_id, message)
- get_task_logs(task_id)
- get_task_poll_data(task_type)
- signal_task(workflow_id, ref_name, data)
```

#### 2.2 Workflow Client

```
Abstract Interface (20+ methods):
- start_workflow(start_request)
- get_workflow(workflow_id, include_tasks?)
- get_workflow_status(workflow_id, include_output?, include_variables?)
- delete_workflow(workflow_id, archive?)
- terminate_workflow(workflow_id, reason?, trigger_failure?)
- pause_workflow(workflow_id)
- resume_workflow(workflow_id)
- restart_workflow(workflow_id, use_latest_def?)
- retry_workflow(workflow_id, resume_subworkflow?)
- rerun_workflow(workflow_id, rerun_request)
- skip_task_from_workflow(workflow_id, task_ref, skip_request)
- test_workflow(test_request)
- search(start?, size?, free_text?, query?)
- execute_workflow(start_request, request_id?, wait_until?, wait_seconds?)
[... additional methods]
```

#### 2.3 Metadata Client (21 APIs)

#### 2.4 Authorization Client (49 APIs)

#### 2.5 Secret Client (9 APIs)

#### 2.6 Integration Client (28+ providers)

#### 2.7 Prompt Client (8 APIs)

#### 2.8 Schedule Client (15 APIs)

### Phase 3: Worker Framework

#### 3.1 Worker Task Decorator/Annotation

- [ ] Create worker registration system
- [ ] Implement task discovery
- [ ] Add worker lifecycle management
- [ ] Support both sync and async workers

#### 3.2 Task Runner

- [ ] Implement TaskRunner with thread pool
- [ ] Implement AsyncTaskRunner with event loop
- [ ] Add metrics collection
- [ ] Implement graceful shutdown
- [ ] Add health checks

#### 3.3 Worker Features

- [ ] Task context injection
- [ ] Automatic retries
- [ ] TaskInProgress support for long-running tasks
- [ ] Error handling (retryable vs terminal)
- [ ] Worker discovery from packages

### Phase 4: Workflow DSL

- [ ] Implement ConductorWorkflow builder
- [ ] Add all task types (Simple, HTTP, Switch, Fork, DoWhile, etc.)
- [ ] Support method chaining
- [ ] Add workflow validation
- [ ] Implement workflow testing utilities

### Phase 5: Examples

#### 5.1 Core Examples

- [ ] `workers_e2e` - Complete end-to-end example
- [ ] `worker_example` - Worker patterns
- [ ] `task_context_example` - Long-running tasks
- [ ] `workflow_example` - Workflow creation
- [ ] `test_workflows` - Testing patterns

#### 5.2 Journey Examples (100% API Coverage)

- [ ] `authorization_journey` - All 49 authorization APIs
- [ ] `metadata_journey` - All 21 metadata APIs
- [ ] `integration_journey` - All integration providers
- [ ] `schedule_journey` - All 15 schedule APIs
- [ ] `prompt_journey` - All 8 prompt APIs
- [ ] `secret_journey` - All 9 secret APIs

### Phase 6: Documentation

- [ ] Create all API reference documents (see Documentation section)
- [ ] Add Quick Start for each module
- [ ] Include complete working examples
- [ ] Document all models
- [ ] Add error handling guides
- [ ] Include best practices

---

## 🌐 Language-Specific Implementation

### Java Implementation

```java
// Package Structure
com.conductor.sdk/
├── client/
│   ├── TaskClient.java                    // Interface
│   ├── orkes/
│   │   ├── OrkesBaseClient.java
│   │   └── OrkesTaskClient.java          // Implementation
│   └── http/
│       ├── api/                          // Generated
│       └── models/                       // Generated

// Client Pattern
public interface TaskClient {
    Optional<Task> pollTask(String taskType, String workerId, String domain);
    List<Task> batchPollTasks(String taskType, BatchPollRequest request);
    // ... other methods
}

public class OrkesTaskClient extends OrkesBaseClient implements TaskClient {
    @Override
    public Optional<Task> pollTask(String taskType, String workerId, String domain) {
        return Optional.ofNullable(
            taskResourceApi.poll(taskType, workerId, domain)
        );
    }
}

// Configuration
Configuration config = Configuration.builder()
    .serverUrl("http://localhost:8080/api")
    .authentication(keyId, keySecret)
    .connectionPool(10, 30, TimeUnit.SECONDS)
    .retryPolicy(3, 1000)
    .build();

// Worker Pattern
@WorkerTask("process_order")
public class OrderProcessor implements Worker {
    @Override
    public TaskResult execute(Task task) {
        OrderInput input = task.getInputData(OrderInput.class);
        // Process
        return TaskResult.complete(output);
    }
}

// Task Runner
TaskRunnerConfigurer configurer = TaskRunnerConfigurer.builder()
    .configuration(config)
    .workers(new OrderProcessor(), new PaymentProcessor())
    .threadCount(10)
    .build();

configurer.start();
```

### Go Implementation

```go
// Package Structure
github.com/conductor-oss/conductor-go/
├── client/
│   ├── task_client.go                    // Interface
│   ├── orkes/
│   │   ├── base_client.go
│   │   └── task_client.go               // Implementation
│   └── http/
│       ├── api/                         // Generated
│       └── models/                      // Generated

// Client Pattern
type TaskClient interface {
    PollTask(ctx context.Context, taskType string, opts ...PollOption) (*Task, error)
    BatchPollTasks(ctx context.Context, taskType string, opts ...PollOption) ([]*Task, error)
    // ... other methods
}

type orkesTaskClient struct {
    *BaseClient
    api *TaskResourceAPI
}

func (c *orkesTaskClient) PollTask(ctx context.Context, taskType string, opts ...PollOption) (*Task, error) {
    options := &pollOptions{}
    for _, opt := range opts {
        opt(options)
    }
    return c.api.Poll(ctx, taskType, options.WorkerID, options.Domain)
}

// Configuration
config := client.NewConfig(
    client.WithServerURL("http://localhost:8080/api"),
    client.WithAuthentication(keyID, keySecret),
    client.WithConnectionPool(10, 30*time.Second),
    client.WithRetryPolicy(3, time.Second),
)

// Worker Pattern
type OrderProcessor struct{}

func (p *OrderProcessor) TaskType() string {
    return "process_order"
}

func (p *OrderProcessor) Execute(ctx context.Context, task *Task) (*TaskResult, error) {
    var input OrderInput
    if err := task.GetInputData(&input); err != nil {
        return nil, err
    }
    // Process
    return NewTaskResultComplete(output), nil
}

// Task Runner
runner := worker.NewTaskRunner(
    worker.WithConfig(config),
    worker.WithWorkers(&OrderProcessor{}, &PaymentProcessor{}),
    worker.WithThreadCount(10),
)

runner.Start(ctx)
```

### TypeScript/JavaScript Implementation

```typescript
// Package Structure
@conductor-oss/conductor-sdk/
├── src/
│   ├── client/
│   │   ├── TaskClient.ts                 // Interface
│   │   ├── orkes/
│   │   │   ├── OrkesBaseClient.ts
│   │   │   └── OrkesTaskClient.ts       // Implementation
│   │   └── http/
│   │       ├── api/                     // Generated
│   │       └── models/                  // Generated

// Client Pattern
export interface TaskClient {
    pollTask(taskType: string, workerId?: string, domain?: string): Promise<Task | null>;
    batchPollTasks(taskType: string, options?: BatchPollOptions): Promise<Task[]>;
    // ... other methods
}

export class OrkesTaskClient extends OrkesBaseClient implements TaskClient {
    async pollTask(taskType: string, workerId?: string, domain?: string): Promise<Task | null> {
        return await this.taskApi.poll(taskType, { workerId, domain });
    }
}

// Configuration
const config = new Configuration({
    serverUrl: 'http://localhost:8080/api',
    authentication: {
        keyId: 'your-key',
        keySecret: 'your-secret'
    },
    connectionPool: {
        maxConnections: 10,
        keepAliveTimeout: 30000
    },
    retry: {
        maxAttempts: 3,
        backoffMs: 1000
    }
});

// Worker Pattern (Decorators)
@WorkerTask('process_order')
export class OrderProcessor implements Worker {
    async execute(task: Task): Promise<TaskResult> {
        const input = task.inputData as OrderInput;
        // Process
        return TaskResult.complete(output);
    }
}

// Worker Pattern (Functional)
export const processOrder = workerTask('process_order', async (task: Task) => {
    const input = task.inputData as OrderInput;
    // Process
    return output;
});

// Task Runner
const runner = new TaskRunner({
    config,
    workers: [OrderProcessor, PaymentProcessor],
    // or functional: workers: [processOrder, processPayment],
    options: {
        threadCount: 10,
        pollInterval: 100
    }
});

await runner.start();
```

### C# Implementation

```csharp
// Package Structure
Conductor.Client/
├── Client/
│   ├── ITaskClient.cs                    // Interface
│   ├── Orkes/
│   │   ├── OrkesBaseClient.cs
│   │   └── OrkesTaskClient.cs           // Implementation
│   └── Http/
│       ├── Api/                         // Generated
│       └── Models/                      // Generated

// Client Pattern
public interface ITaskClient
{
    Task<ConductorTask?> PollTaskAsync(string taskType, string? workerId = null, string? domain = null);
    Task<List<ConductorTask>> BatchPollTasksAsync(string taskType, BatchPollOptions? options = null);
    // ... other methods
}

public class OrkesTaskClient : OrkesBaseClient, ITaskClient
{
    public async Task<ConductorTask?> PollTaskAsync(string taskType, string? workerId = null, string? domain = null)
    {
        return await TaskApi.PollAsync(taskType, workerId, domain);
    }
}

// Configuration
var config = new Configuration
{
    ServerUrl = "http://localhost:8080/api",
    Authentication = new AuthenticationSettings
    {
        KeyId = "your-key",
        KeySecret = "your-secret"
    },
    ConnectionPool = new PoolSettings
    {
        MaxConnections = 10,
        KeepAliveTimeout = TimeSpan.FromSeconds(30)
    },
    Retry = new RetryPolicy
    {
        MaxAttempts = 3,
        BackoffMs = 1000
    }
};

// Worker Pattern (Attributes)
[WorkerTask("process_order")]
public class OrderProcessor : IWorker
{
    public async Task<TaskResult> ExecuteAsync(ConductorTask task)
    {
        var input = task.GetInputData<OrderInput>();
        // Process
        return TaskResult.Complete(output);
    }
}

// Task Runner
var runner = new TaskRunner(config)
    .AddWorker<OrderProcessor>()
    .AddWorker<PaymentProcessor>()
    .WithOptions(new RunnerOptions
    {
        ThreadCount = 10,
        PollInterval = TimeSpan.FromMilliseconds(100)
    });

await runner.StartAsync();
```

---

## 📋 API Method Naming Conventions

### Consistent Naming Across All Clients

| Operation | Method Pattern | Example |
|-----------|---------------|---------|
| Create | `create{Resource}` / `save{Resource}` | `createWorkflow`, `saveSchedule` |
| Read (single) | `get{Resource}` | `getTask`, `getWorkflow` |
| Read (list) | `list{Resources}` / `getAll{Resources}` | `listTasks`, `getAllSchedules` |
| Update | `update{Resource}` | `updateTask`, `updateWorkflow` |
| Delete | `delete{Resource}` | `deleteWorkflow`, `deleteSecret` |
| Search | `search{Resources}` | `searchWorkflows`, `searchTasks` |
| Execute | `{action}{Resource}` | `pauseWorkflow`, `resumeSchedule` |
| Test | `test{Resource}` | `testWorkflow` |

### Parameter Patterns

```
Required parameters: Direct method parameters
Optional parameters: Options object or builder pattern

Example:
- pollTask(taskType: string, options?: PollOptions)
- updateTask(taskId: string, result: TaskResult)
```

---

## 📚 Documentation Structure

### Required Documentation Files

```
docs/
├── AUTHORIZATION.md         # 49 APIs - User, Group, Application, Permissions
├── METADATA.md             # 21 APIs - Task & Workflow definitions
├── INTEGRATION.md          # 28+ providers - AI/LLM integrations
├── PROMPT.md               # 8 APIs - Prompt template management
├── SCHEDULE.md             # 15 APIs - Workflow scheduling
├── SECRET_MANAGEMENT.md    # 9 APIs - Secret storage
├── TASK_MANAGEMENT.md      # 11 APIs - Task operations
├── WORKFLOW.md             # Workflow operations
├── WORKFLOW_TESTING.md     # Testing guide
├── WORKER.md               # Worker implementation
└── README.md               # SDK overview
```

### Documentation Template for Each Module

```markdown
# [Module] API Reference

Complete API reference for [module] operations in Conductor [Language] SDK.

> 📚 **Complete Working Example**: See [example.ext] for comprehensive implementation.

## Quick Start

```language
// 10-15 line minimal example
```

## Quick Links
- [API Category 1](#api-category-1)
- [API Category 2](#api-category-2)
- [API Details](#api-details)
- [Model Reference](#model-reference)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## API Category Tables

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `methodName()` | `HTTP_VERB /path` | Description | [Link](#anchor) |

## API Details

[Detailed examples for each API method]

## Model Reference

[Model/class definitions]

## Error Handling

[Common errors and handling patterns]

## Best Practices

[Good vs bad examples with ✅ and ❌]

## Complete Working Example

[50-150 line runnable example]
```

---

## 🧪 Testing Requirements

### Test Coverage Goals

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|------------|-------------------|-----------|
| Clients | 90% | 80% | - |
| Workers | 95% | 85% | 70% |
| Workflow DSL | 90% | 80% | - |
| Examples | - | 100% | 100% |
```

### Test Structure
```
tests/
├── unit/
│   ├── client/
│   │   ├── test_task_client.{ext}
│   │   └── test_workflow_client.{ext}
│   ├── worker/
│   │   └── test_worker_discovery.{ext}
│   └── workflow/
│       └── test_workflow_builder.{ext}
├── integration/
│   ├── test_worker_execution.{ext}
│   ├── test_workflow_execution.{ext}
│   └── test_error_handling.{ext}
└── e2e/
    ├── test_authorization_journey.{ext}
    └── test_complete_flow.{ext}
```

---

## 🎯 Success Criteria

### Architecture
- [ ] Follows layered architecture pattern
- [ ] Maintains separation of concerns
- [ ] Uses dependency injection
- [ ] Implements proper abstractions

### API Design
- [ ] Consistent method naming
- [ ] Predictable parameter patterns
- [ ] Strong typing with models
- [ ] Comprehensive error handling

### Documentation
- [ ] 100% API coverage
- [ ] Quick start for each module
- [ ] Complete working examples
- [ ] Best practices documented

### Testing
- [ ] >90% unit test coverage
- [ ] Integration tests for all APIs
- [ ] Journey tests demonstrate 100% API usage
- [ ] Examples are executable tests

### Developer Experience
- [ ] Intuitive API design
- [ ] Excellent IDE support
- [ ] Clear error messages
- [ ] Comprehensive logging

---

## 📊 Validation Checklist

Before considering an SDK complete:

### Code Quality
- [ ] Follows language idioms
- [ ] Consistent code style
- [ ] No code duplication
- [ ] Proper error handling
- [ ] Comprehensive logging

### API Completeness
- [ ] All 49 Authorization APIs
- [ ] All 21 Metadata APIs
- [ ] All 15 Schedule APIs
- [ ] All 11 Task APIs
- [ ] All 9 Secret APIs
- [ ] All 8 Prompt APIs
- [ ] All Integration providers

### Documentation
- [ ] All API docs created
- [ ] Quick starts work
- [ ] Examples run successfully
- [ ] Cross-references valid
- [ ] No broken links

### Testing
- [ ] Unit test coverage >90%
- [ ] Integration tests pass
- [ ] Journey examples complete
- [ ] CI/CD configured

### Package
- [ ] Published to package registry
- [ ] Versioning follows semver
- [ ] CHANGELOG maintained
- [ ] LICENSE included

---

## 🔧 Tooling Requirements

### Code Generation
- OpenAPI Generator for API/models
- Custom generators for boilerplate

### Build System
- Language-appropriate build tool
- Dependency management
- Version management
- Package publishing

### CI/CD Pipeline
- Unit tests on every commit
- Integration tests on PR
- Documentation generation
- Package publishing on release

---

## 📞 Support & Questions

For SDK implementation questions:

1. Reference Python SDK for patterns
2. Check this guide for architecture
3. Maintain consistency across SDKs
4. Prioritize developer experience

Remember: The goal is to make Conductor easy to use in every language while maintaining consistency and completeness.

---

