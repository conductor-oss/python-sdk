# Authoring Workflows

## Workflow Definition Management

### Register Workflow Definition

In order to define a workflow, you must provide a `MetadataClient` and a `WorkflowExecutor`, which requires a `Configuration` object with the Conductor Server info. Here's an example on how to do that:

```python
from conductor.client.configuration.configuration import Configuration
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClie
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor

configuration = Configuration(
    server_api_url=SERVER_API_URL,
    debug=False,
    authentication_settings=AuthenticationSettings(key_id=KEY_ID, key_secret=KEY_SECRET)
)

metadata_client = OrkesMetadataClient(configuration)

workflow_executor = WorkflowExecutor(configuration)
workflow = ConductorWorkflow(
    executor=workflow_executor,
    name='python_workflow_example_from_code',
    description='Python workflow example from code'
)
```

After creating an instance of a `ConductorWorkflow`, you can start adding tasks to it. There are two possible ways to do that:
* method: `add`
* operator: `>>`

```python
from conductor.client.workflow.task.simple_task import SimpleTask

simple_task_1 = SimpleTask(
    task_def_name='python_simple_task_from_code_1',
    task_reference_name='python_simple_task_from_code_1'
)
workflow.add(simple_task_1)

simple_task_2 = SimpleTask(
    task_def_name='python_simple_task_from_code_2',
    task_reference_name='python_simple_task_from_code_2'
)
workflow >> simple_task_2
```
You can add input parameters to your workflow:

```python
workflow.input_parameters(["a", "b"])
```

You should be able to register your workflow at the Conductor Server:

```python
from conductor.client.http.models.workflow_def import WorkflowDef

workflowDef = workflow.to_workflow_def()
metadata_client.register_workflow_def(workflowDef, True)
```

### Get Workflow Definition

You should be able to get your workflow definiton that you added previously:

```python
wfDef = metadata_client.get_workflow_def('python_workflow_example_from_code')
```

In case there is an error in fetching the definition, errorStr will be populated.

### Update Workflow Definition

You should be able to update your workflow after adding new tasks:

```python
workflow >> SimpleTask("simple_task", "simple_task_ref_2")
updatedWorkflowDef = workflow.to_workflow_def()
metadata_client.update_workflow_def(updatedWorkflowDef, True)
```

### Unregister Workflow Definition

You should be able to unregister your workflow by passing name and version:

```python
metadata_client.unregister_workflow_def('python_workflow_example_from_code', 1)
```

## Task Definition Management

### Register Task Definition

You should be able to register your task at the Conductor Server:

```python
from conductor.client.http.models.task_def import TaskDef

taskDef = TaskDef(
    name="PYTHON_TASK",
    description="Python Task Example",
    input_keys=["a", "b"]
)
metadata_client.register_task_def(taskDef)
```

### Get Task Definition

You should be able to get your task definiton that you added previously:

```python
taskDef = metadata_client.get_task_def('PYTHON_TASK')
```

### Update Task Definition

You should be able to update your task definition by modifying field values:

```python
taskDef.description = "Python Task Example New Description"
taskDef.input_keys = ["a", "b", "c"]
metadata_client.update_task_def(taskDef)
```

### Unregister Task Definition

You should be able to unregister your task at the Conductor Server:

```python
metadata_client.unregister_task_def('python_task_example_from_code')
```

## Tag Management

### Set tags on your workflow

You should be able to set tags on your workflow:

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("wftag1", "val1"),
    MetadataTag("wftag2", "val2")
]

metadata_client.set_workflow_tags(tags, 'python_workflow_example_from_code')
```

### Add single tag to your workflow

You should be able to add a single tag to your workflow:

```python
tag = MetadataTag("wftag", "val")
metadata_client.add_workflow_tag(tag, 'python_workflow_example_from_code')
```

### Fetch tags added to your workflow

You should be able to fetch tags added to your workflow:

```python
tags = metadata_client.get_workflow_tags('python_workflow_example_from_code')
```

### Delete tag from your workflow

You should be able to delete a tag on your workflow:

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tag = MetadataTag("wftag2", "val2")
metadata_client.delete_workflow_tag(tag, 'python_workflow_example_from_code')
```

### Add tags to your task

You should be able to set tags for your task:

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("tag2", "val2"),
    MetadataTag("tag3", "val3")
]

metadata_client.setTaskTags(tags, 'PYTHON_TASK')
```
setTaskTags will override any previously added tags.

### Add single tag to your task

You should be able to add a tag to your task:

```python
metadata_client.addTaskTag(MetadataTag("tag1", "val1"), 'PYTHON_TASK')
```

### Get tags added to your task

You should be able to fetch tags added to your workflow:

```python
tags = metadata_client.getTaskTags('PYTHON_TASK')
```

### Delete tag from your task

You should be able to delete a tag on your task:

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tag = MetadataTag("tag1", "val1"),
metadata_client.deleteTaskTag(tag, 'PYTHON_TASK')
```

## Rate Limit Management

### Set rate limit for your workflow

You should be able to add a rate limit to your workflow:

```python
metadata_client.setWorkflowRateLimit(5, 'python_workflow_example_from_code')
```

Here the execution limit is set as 5, which means that no more than 5 workflows will be allowed to execute at any given time.

### Get rate limit added to your workflow

You should be able to retrieve the rate limit that was set for your workflow previously:

```python
rate_limit = metadata_client.getWorkflowRateLimit('python_workflow_example_from_code')
```

### Remove the rate limit on your workflow

You should be able to remove the rate limit on your workflow:

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

metadata_client.removeWorkflowRateLimit('python_workflow_example_from_code')
