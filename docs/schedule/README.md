# Schedule Management

## Scheduler Client

### Initialization

```python
from conductor.client.configuration.configuration import Configuration
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient

configuration = Configuration(
    server_api_url=SERVER_API_URL,
    debug=False,
    authentication_settings=AuthenticationSettings(key_id=KEY_ID, key_secret=KEY_SECRET)
)

scheduler_client = OrkesSchedulerClient(configuration)
```

### Saving Schedule

```python
from conductor.client.adapters.models import SaveScheduleRequest, StartWorkflowRequest

startWorkflowRequest = StartWorkflowRequest(
    name="WORKFLOW_NAME", workflow_def=workflowDef
)
saveScheduleRequest = SaveScheduleRequest(
    name="SCHEDULE_NAME",
    start_workflow_request=startWorkflowRequest,
    cron_expression="0 */5 * ? * *"
)

scheduler_client.save_schedule(saveScheduleRequest)
```

### Get Schedule

#### Get a specific schedule

```python
scheduler_client.get_schedule("SCHEDULE_NAME")
```

#### Get all schedules

```python
scheduler_client.get_all_schedules()
```

#### Get all schedules for a workflow

```python
scheduler_client.get_all_schedules("WORKFLOW_NAME")
```

### Delete Schedule

```python
scheduler_client.delete_schedule("SCHEDULE_NAME")
```

### Pause and Resume Schedules

#### Pause a schedule

```python
scheduler_client.pause_schedule("SCHEDULE_NAME")
```

#### Pause all schedules

```python
scheduler_client.pause_all_schedules()
```

#### Resume a scheduler

```python
scheduler_client.resume_schedule("SCHEDULE_NAME")
```

#### Resume all schedules

```python
scheduler_client.resume_all_schedules()
```

### Scheduler Tag Management

#### Set scheduler tags

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("sch_tag", "val"), MetadataTag("sch_tag_2", "val2")
]
scheduler_client.set_scheduler_tags(tags, "SCHEDULE_NAME")
```

#### Get scheduler tags

```python
tags = scheduler_client.get_scheduler_tags("SCHEDULE_NAME")
```

#### Delete scheduler tags

```python
tags = [
    MetadataTag("sch_tag", "val"), MetadataTag("sch_tag_2", "val2")
]
scheduler_client.delete_scheduler_tags(tags, "SCHEDULE_NAME")
```
