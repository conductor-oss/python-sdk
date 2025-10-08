# Workflow Helper Methods Usage Examples

This document provides comprehensive usage examples for the helper methods available in the `Workflow` class.

## Overview

The `Workflow` class provides several helper methods to make it easier to work with workflow instances:

- **Status checking methods**: `is_completed()`, `is_successful()`, `is_running()`, `is_failed()`
- **Task retrieval methods**: `current_task`, `get_in_progress_tasks()`, `get_task_by_reference_name()`

## Status Checking Methods

### `is_completed()`

Checks if the workflow has completed (regardless of success or failure).

```python
from conductor.client.http.models.workflow import Workflow

# Example workflow instances
workflow_completed = Workflow(status="COMPLETED")
workflow_failed = Workflow(status="FAILED")
workflow_terminated = Workflow(status="TERMINATED")
workflow_running = Workflow(status="RUNNING")

# Check completion status
print(workflow_completed.is_completed())  # True
print(workflow_failed.is_completed())     # True
print(workflow_terminated.is_completed()) # True
print(workflow_running.is_completed())   # False
```

### `is_successful()`

Checks if the workflow completed successfully.

```python
# Check success status
print(workflow_completed.is_successful())  # True
print(workflow_failed.is_successful())     # False
print(workflow_terminated.is_successful()) # False
print(workflow_running.is_successful())    # False
```

### `is_running()`

Checks if the workflow is currently running.

```python
workflow_paused = Workflow(status="PAUSED")

# Check running status
print(workflow_running.is_running())  # True
print(workflow_paused.is_running())   # True
print(workflow_completed.is_running()) # False
```

### `is_failed()`

Checks if the workflow has failed.

```python
workflow_timed_out = Workflow(status="TIMED_OUT")

# Check failure status
print(workflow_failed.is_failed())     # True
print(workflow_terminated.is_failed()) # True
print(workflow_timed_out.is_failed())  # True
print(workflow_completed.is_failed())  # False
```

## Task Retrieval Methods

### `current_task` Property

Gets the currently in-progress task (SCHEDULED or IN_PROGRESS).

```python
from conductor.client.http.models.task import Task
from conductor.client.http.models.workflow_task import WorkflowTask

# Create mock tasks
task_completed = TaskA(status="COMPLETED", task_def_name="task1")
task_in_progress = Task(status="IN_PROGRESS", task_def_name="task2")
task_scheduled = Task(status="SCHEDULED", task_def_name="task3")

# Set up workflow with tasks
workflow = Workflow(
    status="RUNNING",
    tasks=[task_completed, task_in_progress, task_scheduled]
)

# Get current task
current = workflow.current_task
print(current.task_def_name)  # "task2" (first IN_PROGRESS task)

# If no in-progress tasks
workflow_no_progress = Workflow(
    status="RUNNING",
    tasks=[task_completed]
)
print(workflow_no_progress.current_task)  # None
```

### `get_in_progress_tasks()`

Gets all currently in-progress tasks.

```python
# Get all in-progress tasks
in_progress_tasks = workflow.get_in_progress_tasks()
print(len(in_progress_tasks))  # 2 (task_in_progress and task_scheduled)

# Check specific tasks
for task in in_progress_tasks:
    print(f"Task: {task.task_def_name}, Status: {task.status}")
```

### `get_task_by_reference_name()`

Gets a task by its reference name.

```python
# Create tasks with workflow task references
workflow_task1 = WorkflowTaskAdapter(task_reference_name="ref_task_1")
workflow_task2 = WorkflowTaskAdapter(task_reference_name="ref_task_2")

task1 = TaskAdapter(
    status="COMPLETED",
    task_def_name="task1",
    workflow_task=workflow_task1
)
task2 = TaskAdapter(
    status="IN_PROGRESS",
    task_def_name="task2",
    workflow_task=workflow_task2
)

workflow_with_refs = Workflow(
    status="RUNNING",
    tasks=[task1, task2]
)

# Get task by reference name
found_task = workflow_with_refs.get_task_by_reference_name("ref_task_2")
if found_task:
    print(f"Found task: {found_task.task_def_name}")  # "task2"

# Task not found
not_found = workflow_with_refs.get_task_by_reference_name("nonexistent_ref")
print(not_found)  # None
```

## Real-World Usage Examples

### Example 1: Workflow Status Monitoring

```python
def monitor_workflow_status(workflow: Workflow):
    """Monitor and report workflow status"""
    
    if workflow.is_completed():
        if workflow.is_successful():
            print("Workflow completed successfully!")
            return "SUCCESS"
        else:
            print("Workflow failed or was terminated")
            return "FAILED"
    elif workflow.is_running():
        print("Workflow is still running...")
        
        # Check current task
        current = workflow.current_task
        if current:
            print(f"Current task: {current.task_def_name} ({current.status})")
        
        # Get all in-progress tasks
        in_progress = workflow.get_in_progress_tasks()
        print(f"Total in-progress tasks: {len(in_progress)}")
        
        return "RUNNING"
    else:
        print("Unknown workflow status")
        return "UNKNOWN"

# Usage
workflow = Workflow(status="RUNNING", tasks=[...])
status = monitor_workflow_status(workflow)
```

### Example 2: Task Progress Tracking

```python
def track_task_progress(workflow: Workflow):
    """Track progress of specific tasks in a workflow"""
    
    # Get all in-progress tasks
    in_progress_tasks = workflow.get_in_progress_tasks()
    
    print(f"Workflow Status: {workflow.status}")
    print(f"Total in-progress tasks: {len(in_progress_tasks)}")
    
    for task in in_progress_tasks:
        print(f"- {task.task_def_name}: {task.status}")
        
        # If task has a reference name, show it
        if hasattr(task, 'workflow_task') and task.workflow_task:
            ref_name = getattr(task.workflow_task, 'task_reference_name', 'N/A')
            print(f"  Reference: {ref_name}")

# Usage
workflow = Workflow(status="RUNNING", tasks=[...])
track_task_progress(workflow)
```

### Example 3: Workflow Result Processing

```python
def process_workflow_result(workflow: Workflow):
    """Process workflow results based on completion status"""
    
    if not workflow.is_completed():
        print("Workflow is not yet completed")
        return None
    
    if workflow.is_successful():
        print("Processing successful workflow result...")
        
        # Get workflow output
        if workflow.output:
            print(f"Workflow output: {workflow.output}")
        
        # Find specific tasks by reference name
        result_task = workflow.get_task_by_reference_name("process_result")
        if result_task:
            print(f"Result task status: {result_task.status}")
            if hasattr(result_task, 'output_data') and result_task.output_data:
                print(f"Task output: {result_task.output_data}")
        
        return workflow.output
    
    else:
        print("Processing failed workflow...")
        
        # Get failed tasks
        failed_tasks = [task for task in workflow.tasks if task.status == "FAILED"]
        print(f"Number of failed tasks: {len(failed_tasks)}")
        
        for task in failed_tasks:
            print(f"Failed task: {task.task_def_name}")
            if hasattr(task, 'reason_for_incompletion'):
                print(f"Reason: {task.reason_for_incompletion}")
        
        return None

# Usage
workflow = Workflow(status="COMPLETED", output={"result": "success"})
result = process_workflow_result(workflow)
```

### Example 4: Workflow Health Check

```python
def health_check_workflow(workflow: Workflow) -> dict:
    """Perform a comprehensive health check on a workflow"""
    
    health_status = {
        "workflow_id": getattr(workflow, 'workflow_id', 'unknown'),
        "status": workflow.status,
        "is_completed": workflow.is_completed(),
        "is_successful": workflow.is_successful(),
        "is_running": workflow.is_running(),
        "is_failed": workflow.is_failed(),
        "current_task": None,
        "in_progress_count": 0,
        "total_tasks": 0
    }
    
    # Task information
    if workflow.tasks:
        health_status["total_tasks"] = len(workflow.tasks)
        health_status["in_progress_count"] = len(workflow.get_in_progress_tasks())
        
        current = workflow.current_task
        if current:
            health_status["current_task"] = {
                "name": current.task_def_name,
                "status": current.status
            }
    
    # Overall health assessment
    if workflow.is_successful():
        health_status["health"] = "HEALTHY"
    elif workflow.is_failed():
        health_status["health"] = "UNHEALTHY"
    elif workflow.is_running():
        health_status["health"] = "IN_PROGRESS"
    else:
        health_status["health"] = "UNKNOWN"
    
    return health_status

# Usage
workflow = Workflow(status="RUNNING", tasks=[...])
health = health_check_workflow(workflow)
print(f"Workflow health: {health['health']}")
```

## Async Client Usage

The async client (`conductor.asyncio_client.adapters.models.workflow_adapter.WorkflowAdapter`) provides the same helper methods:

```python
from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter

# All the same methods are available
workflow = WorkflowAdapter(status="RUNNING")
print(workflow.is_running())  # True
print(workflow.current_task)  # None or current task
```

## Best Practices

1. **Always check for None**: When using `current_task` or `get_task_by_reference_name()`, always check if the result is None.

2. **Use appropriate status methods**: Use `is_completed()` for general completion, `is_successful()` for success checking, and `is_failed()` for failure detection.

3. **Handle missing tasks gracefully**: Always check if `workflow.tasks` is not None before calling task-related methods.

4. **Use reference names for task identification**: When possible, use `get_task_by_reference_name()` instead of iterating through tasks manually.

5. **Combine methods for comprehensive checks**: Use multiple helper methods together to get a complete picture of workflow state.

```python
def comprehensive_workflow_check(workflow: WorkflowAdapter):
    """Comprehensive workflow state checking"""
    
    if workflow.is_completed():
        if workflow.is_successful():
            return "SUCCESS"
        elif workflow.is_failed():
            return "FAILED"
        else:
            return "COMPLETED_UNKNOWN"
    elif workflow.is_running():
        current = workflow.current_task
        if current:
            return f"RUNNING_CURRENT_TASK_{current.task_def_name}"
        else:
            return "RUNNING_NO_CURRENT_TASK"
    else:
        return "UNKNOWN_STATUS"
```
