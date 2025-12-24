# Metadata API Reference

This document provides a comprehensive reference for all Metadata Management APIs available in the Conductor Python SDK, covering workflow and task definition management.

> 📚 **Complete Working Example**: See [metadata_journey.py](../examples/metadata_journey.py) for a comprehensive implementation.

## Table of Contents
- [Quick Start](#quick-start)
- [Workflow Definitions](#workflow-definitions)
- [Task Definitions](#task-definitions)
- [Workflow Tags](#workflow-tags)
- [Task Tags](#task-tags)
- [Rate Limiting](#rate-limiting)
- [Models Reference](#models-reference)
- [API Coverage Summary](#api-coverage-summary)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)

---

## Quick Start

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.simple_task import SimpleTask

# Initialize client
configuration = Configuration(
    server_api_url="http://localhost:8080/api",
    debug=False
)
metadata_client = OrkesMetadataClient(configuration)
workflow_executor = WorkflowExecutor(configuration)

# Create workflow
workflow = ConductorWorkflow(
    executor=workflow_executor,
    name='order_workflow',
    version=1,
    description='Process orders'
)

# Add tasks
workflow >> SimpleTask('validate_order', 'validate_ref')
workflow >> SimpleTask('process_payment', 'payment_ref')

# Register workflow
workflow_def = workflow.to_workflow_def()
metadata_client.register_workflow_def(workflow_def, overwrite=True)
```

---

## Workflow Definitions

Manage workflow definitions in your Conductor instance.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `register_workflow_def()` | `POST /api/metadata/workflow` | Create new workflow | [Example](#register-workflow-definition) |
| `update_workflow_def()` | `PUT /api/metadata/workflow` | Update existing workflow | [Example](#update-workflow-definition) |
| `get_workflow_def()` | `GET /api/metadata/workflow/{name}` | Get workflow by name | [Example](#get-workflow-definition) |
| `get_all_workflow_defs()` | `GET /api/metadata/workflow` | List all workflows | [Example](#get-all-workflow-definitions) |
| `unregister_workflow_def()` | `DELETE /api/metadata/workflow/{name}/{version}` | Delete workflow | [Example](#unregister-workflow-definition) |

### Register Workflow Definition

```python
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.simple_task import SimpleTask

# Method 1: Using ConductorWorkflow builder (recommended)
workflow = ConductorWorkflow(
    executor=workflow_executor,
    name='order_processing_workflow',
    version=1,
    description='Process customer orders',
    timeout_seconds=3600
)

# Add input parameters
workflow.input_parameters(['orderId', 'customerId', 'items'])

# Add tasks using >> operator
workflow >> SimpleTask('validate_order', 'validate_order_ref')
workflow >> SimpleTask('process_payment', 'process_payment_ref')
workflow >> SimpleTask('ship_order', 'ship_order_ref')

# Register workflow
workflow_def = workflow.to_workflow_def()
metadata_client.register_workflow_def(workflow_def, overwrite=True)

# Method 2: Using WorkflowDef directly
workflow_def = WorkflowDef(
    name='simple_workflow',
    version=1,
    description='A simple workflow',
    tasks=[
        {
            'name': 'simple_task',
            'taskReferenceName': 'simple_task_ref',
            'type': 'SIMPLE'
        }
    ],
    inputParameters=['param1', 'param2'],
    outputParameters={'output': '${simple_task_ref.output}'}
)
metadata_client.register_workflow_def(workflow_def, overwrite=False)
```

### Update Workflow Definition

```python
# Get existing workflow
workflow_def = metadata_client.get_workflow_def('order_processing_workflow')

# Modify workflow
workflow_def.description = 'Updated order processing workflow'
workflow_def.timeout_seconds = 7200

# Update workflow
metadata_client.update_workflow_def(workflow_def, overwrite=True)

# Or update using ConductorWorkflow
workflow >> SimpleTask('send_notification', 'notify_ref')
updated_def = workflow.to_workflow_def()
metadata_client.update_workflow_def(updated_def, overwrite=True)
```

### Get Workflow Definition

```python
# Get specific version
workflow_def = metadata_client.get_workflow_def('order_processing_workflow', version=1)

# Get latest version
workflow_def = metadata_client.get_workflow_def('order_processing_workflow')

if workflow_def:
    print(f"Name: {workflow_def.name}")
    print(f"Version: {workflow_def.version}")
    print(f"Tasks: {len(workflow_def.tasks)}")
```

### Get All Workflow Definitions

```python
# Get all workflows
workflows = metadata_client.get_all_workflow_defs()

for wf in workflows:
    print(f"Workflow: {wf.name} v{wf.version}")
    print(f"  Description: {wf.description}")
    print(f"  Tasks: {len(wf.tasks)}")
    print(f"  Active: {wf.active}")
```

### Unregister Workflow Definition

```python
# Delete specific version
metadata_client.unregister_workflow_def('order_processing_workflow', version=1)

# Delete latest version
metadata_client.unregister_workflow_def('order_processing_workflow')
```

---

## Task Definitions

Manage task definitions that can be used in workflows.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `register_task_def()` | `POST /api/metadata/taskdefs` | Create new task | [Example](#register-task-definition) |
| `update_task_def()` | `PUT /api/metadata/taskdefs` | Update existing task | [Example](#update-task-definition) |
| `get_task_def()` | `GET /api/metadata/taskdefs/{name}` | Get task by name | [Example](#get-task-definition) |
| `get_all_task_defs()` | `GET /api/metadata/taskdefs` | List all tasks | [Example](#get-all-task-definitions) |
| `unregister_task_def()` | `DELETE /api/metadata/taskdefs/{name}` | Delete task | [Example](#unregister-task-definition) |

### Register Task Definition

```python
from conductor.client.http.models.task_def import TaskDef

# Create task definition
task_def = TaskDef(
    name='process_payment',
    description='Process payment for order',
    retry_count=3,
    retry_logic='EXPONENTIAL_BACKOFF',
    retry_delay_seconds=60,
    timeout_seconds=300,
    input_keys=['amount', 'currency', 'payment_method'],
    output_keys=['transaction_id', 'status'],
    response_timeout_seconds=180,
    concurrent_exec_limit=10,
    rate_limit_per_frequency=100,
    rate_limit_frequency_in_seconds=60
)

# Register task
metadata_client.register_task_def(task_def)

# Register multiple tasks
task_defs = [
    TaskDef(name='validate_order', input_keys=['order_id']),
    TaskDef(name='ship_order', input_keys=['order_id', 'address']),
    TaskDef(name='send_notification', input_keys=['email', 'message'])
]

for task_def in task_defs:
    metadata_client.register_task_def(task_def)
```

### Update Task Definition

```python
# Get existing task
task_def = metadata_client.get_task_def('process_payment')

# Update properties
task_def.description = 'Process payment with fraud detection'
task_def.retry_count = 5
task_def.timeout_seconds = 600
task_def.input_keys.append('fraud_check')

# Save updates
metadata_client.update_task_def(task_def)
```

### Get Task Definition

```python
# Get task definition
task_def = metadata_client.get_task_def('process_payment')

if task_def:
    print(f"Task: {task_def.name}")
    print(f"Description: {task_def.description}")
    print(f"Retry Count: {task_def.retry_count}")
    print(f"Timeout: {task_def.timeout_seconds}s")
    print(f"Input Keys: {task_def.input_keys}")
```

### Get All Task Definitions

```python
# List all tasks
tasks = metadata_client.get_all_task_defs()

for task in tasks:
    print(f"Task: {task.name}")
    print(f"  Type: {task.type if hasattr(task, 'type') else 'SIMPLE'}")
    print(f"  Retries: {task.retry_count}")
    print(f"  Rate Limit: {task.rate_limit_per_frequency}/s")
```

### Unregister Task Definition

```python
# Delete task definition
metadata_client.unregister_task_def('process_payment')
print("Task definition deleted")
```

---

## Workflow Tags

Organize workflows with metadata tags.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `set_workflow_tags()` | `PUT /api/metadata/workflow/{name}/tags` | Replace all tags | [Example](#set-workflow-tags) |
| `add_workflow_tag()` | `POST /api/metadata/workflow/{name}/tags` | Add single tag | [Example](#add-workflow-tag) |
| `get_workflow_tags()` | `GET /api/metadata/workflow/{name}/tags` | Get all tags | [Example](#get-workflow-tags) |
| `delete_workflow_tag()` | `DELETE /api/metadata/workflow/{name}/tags` | Delete specific tag | [Example](#delete-workflow-tag) |

### Set Workflow Tags

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Replace all tags (overwrites existing)
tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "platform"),
    MetadataTag("criticality", "high"),
    MetadataTag("cost_center", "engineering")
]

metadata_client.set_workflow_tags(tags, 'order_processing_workflow')
print("✅ Workflow tags set")
```

### Add Workflow Tag

```python
# Add a single tag (preserves existing)
tag = MetadataTag("version", "2.0")
metadata_client.add_workflow_tag(tag, 'order_processing_workflow')
print("✅ Tag added to workflow")
```

### Get Workflow Tags

```python
# Get all tags
tags = metadata_client.get_workflow_tags('order_processing_workflow')

for tag in tags:
    print(f"Tag: {tag.key} = {tag.value}")
```

### Delete Workflow Tag

```python
# Delete specific tag
tag = MetadataTag("environment", "production")
metadata_client.delete_workflow_tag(tag, 'order_processing_workflow')
print("✅ Tag deleted from workflow")
```

---

## Task Tags

Organize tasks with metadata tags.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `setTaskTags()` | `PUT /api/metadata/taskdefs/{name}/tags` | Replace all tags | [Example](#set-task-tags) |
| `addTaskTag()` | `POST /api/metadata/taskdefs/{name}/tags` | Add single tag | [Example](#add-task-tag) |
| `getTaskTags()` | `GET /api/metadata/taskdefs/{name}/tags` | Get all tags | [Example](#get-task-tags) |
| `deleteTaskTag()` | `DELETE /api/metadata/taskdefs/{name}/tags` | Delete specific tag | [Example](#delete-task-tag) |

### Set Task Tags

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Replace all tags (overwrites existing)
tags = [
    MetadataTag("type", "payment"),
    MetadataTag("integration", "stripe"),
    MetadataTag("async", "false"),
    MetadataTag("retryable", "true")
]

metadata_client.setTaskTags(tags, 'process_payment')
print("✅ Task tags set")
```

### Add Task Tag

```python
# Add a single tag (preserves existing)
tag = MetadataTag("sla", "critical")
metadata_client.addTaskTag(tag, 'process_payment')
print("✅ Tag added to task")
```

### Get Task Tags

```python
# Get all tags
tags = metadata_client.getTaskTags('process_payment')

for tag in tags:
    print(f"Tag: {tag.key} = {tag.value}")
```

### Delete Task Tag

```python
# Delete specific tag
tag = MetadataTag("type", "payment")
metadata_client.deleteTaskTag(tag, 'process_payment')
print("✅ Tag deleted from task")
```

---

## Rate Limiting

Control workflow execution rates to manage load.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `setWorkflowRateLimit()` | `POST /api/metadata/workflow/{name}/ratelimit` | Set rate limit | [Example](#set-workflow-rate-limit) |
| `getWorkflowRateLimit()` | `GET /api/metadata/workflow/{name}/ratelimit` | Get rate limit | [Example](#get-workflow-rate-limit) |
| `removeWorkflowRateLimit()` | `DELETE /api/metadata/workflow/{name}/ratelimit` | Remove rate limit | [Example](#remove-workflow-rate-limit) |

### Set Workflow Rate Limit

```python
# Set rate limit - max 10 concurrent executions
metadata_client.setWorkflowRateLimit(10, 'order_processing_workflow')
print("✅ Rate limit set to 10 concurrent executions")

# Different rate limits for different workflows
metadata_client.setWorkflowRateLimit(100, 'high_volume_workflow')
metadata_client.setWorkflowRateLimit(5, 'resource_intensive_workflow')
metadata_client.setWorkflowRateLimit(1, 'singleton_workflow')  # Only 1 at a time
```

### Get Workflow Rate Limit

```python
# Get current rate limit
rate_limit = metadata_client.getWorkflowRateLimit('order_processing_workflow')

if rate_limit:
    print(f"Rate limit: {rate_limit} concurrent executions")
else:
    print("No rate limit set (unlimited)")
```

### Remove Workflow Rate Limit

```python
# Remove rate limit (allow unlimited)
metadata_client.removeWorkflowRateLimit('order_processing_workflow')
print("✅ Rate limit removed - unlimited executions allowed")
```

---

## Models Reference

### Core Models

#### WorkflowDef

Represents a workflow definition.

**Module:** `conductor.client.http.models.workflow_def`

**Key Properties:**
- `name` (str, required): Unique workflow name
- `version` (int): Version number (default: 1)
- `description` (str): Workflow description
- `tasks` (list): List of workflow tasks
- `inputParameters` (list): Required input parameters
- `outputParameters` (dict): Output mapping
- `schemaVersion` (int): Schema version (default: 2)
- `restartable` (bool): Allow restart (default: true)
- `workflowStatusListenerEnabled` (bool): Enable status listener
- `ownerEmail` (str): Owner email address
- `timeoutSeconds` (int): Workflow timeout in seconds
- `timeoutPolicy` (str): ALERT_ONLY, TIME_OUT_WF
- `failureWorkflow` (str): Workflow to run on failure

**Example:**
```python
from conductor.client.http.models.workflow_def import WorkflowDef

workflow_def = WorkflowDef(
    name='order_workflow',
    version=1,
    description='Order processing workflow',
    tasks=[],
    inputParameters=['orderId', 'customerId'],
    outputParameters={'status': '${finalTask.output.status}'},
    timeoutSeconds=3600,
    restartable=True
)
```

#### TaskDef

Represents a task definition.

**Module:** `conductor.client.http.models.task_def`

**Key Properties:**
- `name` (str, required): Unique task name
- `description` (str): Task description
- `retryCount` (int): Number of retries (default: 3)
- `retryLogic` (str): FIXED, EXPONENTIAL_BACKOFF, LINEAR_BACKOFF
- `retryDelaySeconds` (int): Delay between retries
- `timeoutSeconds` (int): Task timeout
- `inputKeys` (list): Expected input parameters
- `outputKeys` (list): Expected output parameters
- `timeoutPolicy` (str): RETRY, TIME_OUT_WF, ALERT_ONLY
- `responseTimeoutSeconds` (int): Response timeout
- `concurrentExecLimit` (int): Max concurrent executions
- `rateLimitPerFrequency` (int): Rate limit count
- `rateLimitFrequencyInSeconds` (int): Rate limit window
- `isolationGroupId` (str): Isolation group for execution
- `executionNameSpace` (str): Execution namespace
- `ownerEmail` (str): Task owner email
- `pollTimeoutSeconds` (int): Poll timeout for system tasks

**Example:**
```python
from conductor.client.http.models.task_def import TaskDef

task_def = TaskDef(
    name='send_email',
    description='Send email notification',
    retryCount=3,
    retryLogic='EXPONENTIAL_BACKOFF',
    retryDelaySeconds=60,
    timeoutSeconds=300,
    inputKeys=['to', 'subject', 'body'],
    outputKeys=['messageId', 'status'],
    concurrentExecLimit=50,
    rateLimitPerFrequency=100,
    rateLimitFrequencyInSeconds=60
)
```

#### MetadataTag

Tag for organizing workflows and tasks.

**Module:** `conductor.client.orkes.models.metadata_tag`

**Properties:**
- `key` (str, required): Tag key
- `value` (str, required): Tag value

**Example:**
```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tag = MetadataTag("environment", "production")
```

#### ConductorWorkflow

Builder class for creating workflows programmatically.

**Module:** `conductor.client.workflow.conductor_workflow`

**Key Methods:**
- `add(task)`: Add a task to workflow
- `>>`: Operator to add tasks
- `input_parameters(params)`: Set input parameters
- `to_workflow_def()`: Convert to WorkflowDef

**Example:**
```python
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.simple_task import SimpleTask

workflow = ConductorWorkflow(
    executor=executor,
    name='my_workflow',
    version=1
)

# Add tasks
workflow >> SimpleTask('task1', 'ref1')
workflow >> SimpleTask('task2', 'ref2')

# Set inputs
workflow.input_parameters(['param1', 'param2'])

# Convert to definition
workflow_def = workflow.to_workflow_def()
```

---

## API Coverage Summary

### Metadata Management APIs (17 total)

| Category | API | Status |
|----------|-----|--------|
| **Workflow Definitions** | | |
| | `register_workflow_def()` | ✅ Implemented |
| | `update_workflow_def()` | ✅ Implemented |
| | `get_workflow_def()` | ✅ Implemented |
| | `get_all_workflow_defs()` | ✅ Implemented |
| | `unregister_workflow_def()` | ✅ Implemented |
| **Task Definitions** | | |
| | `register_task_def()` | ✅ Implemented |
| | `update_task_def()` | ✅ Implemented |
| | `get_task_def()` | ✅ Implemented |
| | `get_all_task_defs()` | ✅ Implemented |
| | `unregister_task_def()` | ✅ Implemented |
| **Workflow Tags** | | |
| | `set_workflow_tags()` | ✅ Implemented |
| | `add_workflow_tag()` | ✅ Implemented |
| | `get_workflow_tags()` | ✅ Implemented |
| | `delete_workflow_tag()` | ✅ Implemented |
| **Task Tags** | | |
| | `setTaskTags()` | ✅ Implemented |
| | `addTaskTag()` | ✅ Implemented |
| | `getTaskTags()` | ✅ Implemented |
| | `deleteTaskTag()` | ✅ Implemented |
| **Rate Limiting** | | |
| | `setWorkflowRateLimit()` | ✅ Implemented |
| | `getWorkflowRateLimit()` | ✅ Implemented |
| | `removeWorkflowRateLimit()` | ✅ Implemented |

**Coverage: 21/21 APIs (100%)**

---

## Best Practices

### 1. Workflow Design

```python
# Use meaningful names and descriptions
workflow = ConductorWorkflow(
    name='order_fulfillment_v2',  # Versioned naming
    description='Handles order fulfillment with inventory check',
    version=2,
    timeout_seconds=3600  # Set appropriate timeout
)

# Define clear input/output contracts
workflow.input_parameters(['orderId', 'customerId', 'items'])
```

### 2. Task Definition

```python
# Configure retry strategy appropriately
task_def = TaskDef(
    name='payment_processor',
    retryCount=3,
    retryLogic='EXPONENTIAL_BACKOFF',  # For transient failures
    retryDelaySeconds=60,
    timeoutSeconds=300,
    timeoutPolicy='RETRY'  # Retry on timeout
)

# Set rate limits for external services
task_def.rateLimitPerFrequency = 100
task_def.rateLimitFrequencyInSeconds = 60
```

### 3. Tag Strategy

```python
# Use consistent tagging
workflow_tags = [
    MetadataTag("env", "prod"),
    MetadataTag("team", "platform"),
    MetadataTag("criticality", "p1"),
    MetadataTag("domain", "orders"),
    MetadataTag("version", "2.0")
]

task_tags = [
    MetadataTag("type", "external"),
    MetadataTag("integration", "payment"),
    MetadataTag("async", "true"),
    MetadataTag("idempotent", "true")
]
```

### 4. Version Management

```python
# Always version workflows
workflow_v1 = ConductorWorkflow(name='process_order', version=1)
workflow_v2 = ConductorWorkflow(name='process_order', version=2)

# Keep old versions for rollback
metadata_client.register_workflow_def(workflow_v2.to_workflow_def(), overwrite=False)
```

### 5. Rate Limiting

```python
# Set appropriate limits based on resources
metadata_client.setWorkflowRateLimit(
    100,  # High throughput
    'data_processing_workflow'
)

metadata_client.setWorkflowRateLimit(
    5,  # Resource intensive
    'video_processing_workflow'
)

metadata_client.setWorkflowRateLimit(
    1,  # Singleton pattern
    'daily_report_workflow'
)
```

---

## Error Handling

```python
from conductor.client.http.rest import ApiException

try:
    # Register workflow
    workflow_def = workflow.to_workflow_def()
    metadata_client.register_workflow_def(workflow_def, overwrite=False)

except ApiException as e:
    if e.status == 409:
        print("Workflow already exists")
        # Update instead
        metadata_client.update_workflow_def(workflow_def, overwrite=True)
    elif e.status == 400:
        print(f"Invalid workflow definition: {e}")
    else:
        print(f"API error: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")

# Safe get with fallback
def get_workflow_safe(name, version=None):
    try:
        return metadata_client.get_workflow_def(name, version)
    except:
        return None

# Cleanup helper
def cleanup_workflow(name, version=None):
    try:
        # Remove rate limit
        metadata_client.removeWorkflowRateLimit(name)
        # Delete workflow
        metadata_client.unregister_workflow_def(name, version)
        print(f"✅ Cleaned up workflow: {name}")
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")
```

---

## Complete Example

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.http.models.task_def import TaskDef
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Initialize
configuration = Configuration()
metadata_client = OrkesMetadataClient(configuration)
workflow_executor = WorkflowExecutor(configuration)

# 1. Register Task Definitions
tasks = [
    TaskDef(name='validate_order', inputKeys=['orderId']),
    TaskDef(name='check_inventory', inputKeys=['items']),
    TaskDef(name='process_payment', inputKeys=['amount', 'method']),
    TaskDef(name='ship_order', inputKeys=['orderId', 'address'])
]

for task in tasks:
    metadata_client.register_task_def(task)

# 2. Create and Register Workflow
workflow = ConductorWorkflow(
    executor=workflow_executor,
    name='complete_order_workflow',
    version=1,
    description='End-to-end order processing'
)

workflow.input_parameters(['orderId', 'customerId', 'items', 'paymentMethod'])
workflow >> SimpleTask('validate_order', 'validate_ref')
workflow >> SimpleTask('check_inventory', 'inventory_ref')
workflow >> SimpleTask('process_payment', 'payment_ref')
workflow >> SimpleTask('ship_order', 'ship_ref')

workflow_def = workflow.to_workflow_def()
metadata_client.register_workflow_def(workflow_def, overwrite=True)

# 3. Add Tags
workflow_tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "fulfillment"),
    MetadataTag("sla", "24h")
]
metadata_client.set_workflow_tags(workflow_tags, 'complete_order_workflow')

# 4. Set Rate Limit
metadata_client.setWorkflowRateLimit(50, 'complete_order_workflow')

# 5. Verify Setup
workflow = metadata_client.get_workflow_def('complete_order_workflow')
tags = metadata_client.get_workflow_tags('complete_order_workflow')
rate_limit = metadata_client.getWorkflowRateLimit('complete_order_workflow')

print(f"✅ Workflow: {workflow.name} v{workflow.version}")
print(f"✅ Tags: {len(tags)} tags applied")
print(f"✅ Rate Limit: {rate_limit} concurrent executions")
```

---

## See Also

- [Workflow Management](./WORKFLOW.md) - Running workflows
- [Schedule Management](./SCHEDULE.md) - Scheduling workflows
- [Worker Implementation](./WORKER.md) - Implementing task workers
- [Authorization](./AUTHORIZATION.md) - Permission management
- [Examples](../examples/) - Complete working examples