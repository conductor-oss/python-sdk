# Schedule API Reference

Complete API reference for schedule management operations in Conductor Python SDK.

> 📚 **Complete Working Example**: See [schedule_journey.py](../../examples/schedule_journey.py) for a comprehensive implementation covering all schedule management APIs.

## Quick Links

- [Schedule APIs](#schedule-apis)
- [Schedule Execution APIs](#schedule-execution-apis)
- [Schedule Tag Management APIs](#schedule-tag-management-apis)
- [API Details](#api-details)
- [Model Reference](#model-reference)
- [Error Handling](#error-handling)

## Schedule APIs

Core CRUD operations for managing workflow schedules.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `save_schedule()` | `POST /api/scheduler/schedules` | Create or update a schedule | [Example](#save-schedule) |
| `get_schedule()` | `GET /api/scheduler/schedules/{name}` | Get a specific schedule | [Example](#get-schedule) |
| `get_all_schedules()` | `GET /api/scheduler/schedules` | Get all schedules (optionally by workflow) | [Example](#get-all-schedules) |
| `delete_schedule()` | `DELETE /api/scheduler/schedules/{name}` | Delete a schedule | [Example](#delete-schedule) |

## Schedule Control APIs

Operations for controlling schedule execution state.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `pause_schedule()` | `PUT /api/scheduler/schedules/{name}/pause` | Pause a specific schedule | [Example](#pause-schedule) |
| `pause_all_schedules()` | `PUT /api/scheduler/schedules/pause` | Pause all schedules | [Example](#pause-all-schedules) |
| `resume_schedule()` | `PUT /api/scheduler/schedules/{name}/resume` | Resume a specific schedule | [Example](#resume-schedule) |
| `resume_all_schedules()` | `PUT /api/scheduler/schedules/resume` | Resume all schedules | [Example](#resume-all-schedules) |

## Schedule Execution APIs

APIs for managing and querying schedule executions.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `get_next_few_schedule_execution_times()` | `GET /api/scheduler/nextFewRuns` | Get next execution times for cron expression | [Example](#get-next-execution-times) |
| `search_schedule_executions()` | `GET /api/scheduler/search/executions` | Search schedule execution history | [Example](#search-executions) |
| `requeue_all_execution_records()` | `POST /api/scheduler/requeue` | Requeue all execution records | [Example](#requeue-executions) |

## Schedule Tag Management APIs

Operations for managing tags associated with schedules.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `set_scheduler_tags()` | `POST /api/scheduler/schedules/{name}/tags` | Set/overwrite tags on a schedule | [Example](#set-scheduler-tags) |
| `get_scheduler_tags()` | `GET /api/scheduler/schedules/{name}/tags` | Get tags for a schedule | [Example](#get-scheduler-tags) |
| `delete_scheduler_tags()` | `DELETE /api/scheduler/schedules/{name}/tags` | Delete specific tags from a schedule | [Example](#delete-scheduler-tags) |

---

## API Details

### Schedule Management

#### Save Schedule

Create or update a workflow schedule.

```python
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

# Create workflow start request
start_workflow_request = StartWorkflowRequest(
    name="order_processing",
    version=1,
    input={
        "source": "scheduled",
        "batch_size": 100
    },
    correlation_id="SCHEDULE_ORDER_BATCH"
)

# Create schedule request
# Note: Conductor uses Spring cron format (6 fields: second minute hour day month weekday)
schedule_request = SaveScheduleRequest(
    name="daily_order_processing",
    description="Process pending orders daily at midnight",
    cron_expression="0 0 0 * * ?",  # Daily at midnight (Spring cron format)
    zone_id="America/New_York",
    start_workflow_request=start_workflow_request,
    paused=False  # Schedule starts active
)

# Save the schedule
scheduler_client.save_schedule(schedule_request)
```

**Parameters:**
- `name` (str, required): Unique schedule name
- `description` (str, optional): Schedule description
- `cron_expression` (str, required): Spring cron expression (6 fields: second minute hour day month weekday)
- `zone_id` (str, optional): Time zone ID (default: UTC)
- `start_workflow_request` (StartWorkflowRequest, required): Workflow to execute
- `paused` (bool, optional): Start schedule paused (default: False)
- `schedule_start_time` (int, optional): Schedule start time (epoch millis)
- `schedule_end_time` (int, optional): Schedule end time (epoch millis)

**Spring Cron Format:**
- Format: `second minute hour day month weekday`
- Examples:
  - `0 0 0 * * ?` - Daily at midnight
  - `0 0 * * * ?` - Every hour
  - `0 0 9 ? * MON` - Every Monday at 9 AM
  - `0 0 */2 * * ?` - Every 2 hours
  - `0 0 0,12 * * ?` - Midnight and noon

#### Get Schedule

Retrieve a specific schedule by name.

```python
schedule = scheduler_client.get_schedule("daily_order_processing")
if schedule:
    print(f"Schedule: {schedule.name}")
    print(f"Cron: {schedule.cron_expression}")
    print(f"Paused: {schedule.paused}")
    print(f"Next Run: {schedule.next_execution_time}")
```

**Returns:** `WorkflowSchedule` object or None if not found

#### Get All Schedules

Retrieve all schedules, optionally filtered by workflow name.

```python
# Get all schedules
all_schedules = scheduler_client.get_all_schedules()

# Get schedules for specific workflow
workflow_schedules = scheduler_client.get_all_schedules("order_processing")

for schedule in workflow_schedules:
    print(f"{schedule.name}: {schedule.cron_expression}")
```

**Parameters:**
- `workflow_name` (str, optional): Filter by workflow name

**Returns:** List of `WorkflowSchedule` objects

#### Delete Schedule

Delete a schedule by name.

```python
scheduler_client.delete_schedule("daily_order_processing")
print("Schedule deleted successfully")
```

---

### Schedule Control

#### Pause Schedule

Pause a specific schedule to stop executions.

```python
scheduler_client.pause_schedule("daily_order_processing")
print("Schedule paused")
```

#### Pause All Schedules

Pause all schedules in the system.

```python
scheduler_client.pause_all_schedules()
print("All schedules paused")
```

#### Resume Schedule

Resume a paused schedule.

```python
scheduler_client.resume_schedule("daily_order_processing")
print("Schedule resumed")
```

#### Resume All Schedules

Resume all paused schedules.

```python
scheduler_client.resume_all_schedules()
print("All schedules resumed")
```

---

### Schedule Execution

#### Get Next Execution Times

Calculate next execution times for a cron expression.

```python
import time

# Get next 5 execution times
next_times = scheduler_client.get_next_few_schedule_execution_times(
    cron_expression="0 0 0 * * ?",  # Daily at midnight (Spring cron)
    schedule_start_time=int(time.time() * 1000),
    schedule_end_time=None,
    limit=5
)

for timestamp in next_times:
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp / 1000)
    print(f"Next execution: {dt}")
```

**Parameters:**
- `cron_expression` (str, required): Cron expression to evaluate
- `schedule_start_time` (int, optional): Start time in epoch millis
- `schedule_end_time` (int, optional): End time in epoch millis
- `limit` (int, optional): Number of times to return (default: 3)

#### Search Executions

Search schedule execution history with filtering and pagination.

```python
# Search recent executions
results = scheduler_client.search_schedule_executions(
    start=0,
    size=20,
    sort="startTime:DESC",
    free_text="order",
    query="scheduleName='daily_order_processing' AND status='COMPLETED'"
)

print(f"Total executions: {results.total_hits}")
for execution in results.results:
    print(f"Execution: {execution.workflow_id} - {execution.status}")
```

**Parameters:**
- `start` (int, optional): Start index for pagination (default: 0)
- `size` (int, optional): Number of results (default: 100)
- `sort` (str, optional): Sort field and order (e.g., "startTime:DESC")
- `free_text` (str, optional): Free text search
- `query` (str, optional): Query DSL for filtering

**Returns:** `SearchResultWorkflowScheduleExecutionModel` with results and metadata

#### Requeue Executions

Requeue all execution records for retry.

```python
scheduler_client.requeue_all_execution_records()
print("All execution records requeued")
```

---

### Schedule Tagging

#### Set Scheduler Tags

Set or overwrite all tags on a schedule.

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("environment", "production"),
    MetadataTag("priority", "high"),
    MetadataTag("team", "backend")
]

scheduler_client.set_scheduler_tags(tags, "daily_order_processing")
print("Tags set successfully")
```

**Note:** This overwrites all existing tags

#### Get Scheduler Tags

Retrieve all tags for a schedule.

```python
tags = scheduler_client.get_scheduler_tags("daily_order_processing")
for tag in tags:
    print(f"{tag.key}: {tag.value}")
```

**Returns:** List of `MetadataTag` objects

#### Delete Scheduler Tags

Delete specific tags from a schedule.

```python
tags_to_delete = [
    MetadataTag("priority", "high"),
    MetadataTag("team", "backend")
]

remaining_tags = scheduler_client.delete_scheduler_tags(
    tags_to_delete,
    "daily_order_processing"
)

print(f"Remaining tags: {len(remaining_tags)}")
```

**Returns:** List of remaining `MetadataTag` objects

---

## Model Reference

### Core Models

#### SaveScheduleRequest

Request model for creating/updating schedules.

```python
class SaveScheduleRequest:
    name: str                                    # Unique schedule name
    description: Optional[str]                   # Schedule description
    cron_expression: str                         # Spring cron expression (6 fields)
    zone_id: Optional[str] = "UTC"              # Time zone
    start_workflow_request: StartWorkflowRequest # Workflow to execute
    paused: Optional[bool] = False               # Start paused
    schedule_start_time: Optional[int]           # Start time (epoch millis)
    schedule_end_time: Optional[int]             # End time (epoch millis)
```

#### WorkflowSchedule

Schedule configuration and status.

```python
class WorkflowSchedule:
    name: str                          # Schedule name
    cron_expression: str               # Spring cron expression
    zone_id: str                       # Time zone
    paused: bool                       # Pause status
    enabled: bool                      # Enable status
    start_workflow_request: dict       # Workflow configuration
    created_time: int                  # Creation time (epoch millis)
    updated_time: int                  # Last update time
    next_execution_time: Optional[int] # Next run time
    schedule_start_time: Optional[int] # Schedule start
    schedule_end_time: Optional[int]   # Schedule end
```

#### StartWorkflowRequest

Workflow execution request.

```python
class StartWorkflowRequest:
    name: str                          # Workflow name
    version: Optional[int]             # Workflow version
    input: Optional[dict]              # Input parameters
    correlation_id: Optional[str]      # Correlation ID
    task_to_domain: Optional[dict]     # Task domain mapping
    workflow_def: Optional[WorkflowDef] # Inline workflow definition
    priority: Optional[int] = 0        # Execution priority
```

#### SearchResultWorkflowScheduleExecutionModel

Search results for schedule executions.

```python
class SearchResultWorkflowScheduleExecutionModel:
    results: List[WorkflowScheduleExecution] # Execution records
    total_hits: int                          # Total matching records
```

---

## Error Handling

### Common Errors

```python
try:
    schedule = scheduler_client.get_schedule("non_existent")
except Exception as e:
    if "404" in str(e):
        print("Schedule not found")
    else:
        print(f"Error: {e}")

# Validation errors
try:
    schedule_request = SaveScheduleRequest(
        name="invalid",
        cron_expression="invalid_cron",  # Invalid cron
        start_workflow_request=start_request
    )
    scheduler_client.save_schedule(schedule_request)
except ValueError as e:
    print(f"Validation error: {e}")

# Permission errors
try:
    scheduler_client.delete_schedule("system_schedule")
except PermissionError as e:
    print(f"Permission denied: {e}")
```

### Best Practices

1. **Schedule Naming**:
   - Use descriptive, unique names
   - Include frequency/purpose in name
   - Follow naming conventions

2. **Cron Expressions**:
   - Test expressions before deployment
   - Use `get_next_few_schedule_execution_times()` to verify
   - Consider time zones carefully

3. **Error Recovery**:
   - Monitor execution history regularly
   - Use `search_schedule_executions()` for debugging
   - Implement workflow error handling

4. **Tagging Strategy**:
   - Tag by environment (dev/staging/prod)
   - Tag by team/owner
   - Tag by priority/criticality

---

## Complete Working Example

For a comprehensive example covering all schedule management APIs with proper error handling and best practices, see [schedule_journey.py](../../examples/schedule_journey.py).

```python
# Quick example
from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient
from conductor.client.configuration.configuration import Configuration

config = Configuration(server_api_url="http://localhost:8080/api")
scheduler = OrkesSchedulerClient(config)

# Create, manage, and monitor schedules
# Full implementation in examples/schedule_journey.py
```

---

## See Also

- [Workflow Management](./WORKFLOW.md) - Creating workflows to schedule
- [Metadata Management](./METADATA.md) - Task and workflow definitions
- [Authorization](./AUTHORIZATION.md) - Permission management for schedules
- [Examples](../../examples/) - Complete working examples