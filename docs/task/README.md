# Task Management

## Task Client

### Initialization

```python
from conductor.client.configuration.configuration import Configuration
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_task_client import OrkesTaskClient

configuration = Configuration(
    server_api_url=SERVER_API_URL,
    debug=False,
    authentication_settings=AuthenticationSettings(key_id=KEY_ID, key_secret=KEY_SECRET)
)

task_client = OrkesTaskClient(configuration)
```

### Task Polling
#### Poll a single task

```python
polledTask = task_client.poll_task("TASK_TYPE")
```

#### Batch poll tasks

```python
batchPolledTasks = task_client.batch_poll_tasks("TASK_TYPE")
```

### Get Task

```python
task = task_client.get_task("task_id")
```

### Updating Task Status

#### Update task using TaskResult object

```python
task_result = TaskResult(
    workflow_instance_id="workflow_instance_id",
    task_id="task_id",
    status=TaskResultStatus.COMPLETED
)

task_client.update_task(task_result)
```

#### Update task using task reference name

```python
task_client.update_task_by_ref_name(
    "workflow_instance_id",
    "task_ref_name",
    "COMPLETED",
    "task 2 op 2nd wf"
)
```

#### Update task synchronously

```python
task_client.update_task_sync(
    "workflow_instance_id",
    "task_ref_name",
    "COMPLETED",
    "task 2 op 2nd wf"
)
```

### Task Log Management

#### Add Task logs

```python
task_client.add_task_log("task_id", "Test task log!")
```

#### Get Task logs

```python
taskLogs = task_client.get_task_logs("task_id")
```
