# Conductor Workflows

Workflow can be defined as the collection of tasks and operators that specify the order and execution of the defined tasks. This orchestration occurs in a hybrid ecosystem that encircles serverless functions, microservices, and monolithic applications.

## Table of Contents

- [Creating Workflows](#creating-workflows)
- [Executing Workflows](#executing-workflows)
- [Managing Workflow Executions](#managing-workflow-executions)
- [Handling Failures, Retries and Rate Limits](#handling-failures-retries-and-rate-limits)
- [Using Conductor in Your Application](#using-conductor-in-your-application)

## Creating Workflows

Conductor lets you create the workflows using either Python or JSON as the configuration.

Using Python as code to define and execute workflows lets you build extremely powerful, dynamic workflows and run them on Conductor.

When the workflows are relatively static, they can be designed using the Orkes UI (available when using Orkes Conductor) and APIs or SDKs to register and run the workflows.

Both the code and configuration approaches are equally powerful and similar in nature to how you treat Infrastructure as Code.

### Execute Dynamic Workflows Using Code

For cases where the workflows cannot be created statically ahead of time, Conductor is a powerful dynamic workflow execution platform that lets you create very complex workflows in code and execute them. It is useful when the workflow is unique for each execution.

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow

#@worker_task annotation denotes that this is a worker
@worker_task(task_definition_name='get_user_email')
def get_user_email(userid: str) -> str:
    return f'{userid}@example.com'

#@worker_task annotation denotes that this is a worker
@worker_task(task_definition_name='send_email')
def send_email(email: str, subject: str, body: str):
    print(f'sending email to {email} with subject {subject} and body {body}')


def main():

    # defaults to reading the configuration using following env variables
    # CONDUCTOR_SERVER_URL : conductor server e.g. https://play.orkes.io/api
    # CONDUCTOR_AUTH_KEY : API Authentication Key
    # CONDUCTOR_AUTH_SECRET: API Auth Secret
    api_config = Configuration()

    task_handler = TaskHandler(configuration=api_config)  
    #Start Polling
    task_handler.start_processes()

    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow = ConductorWorkflow(name='dynamic_workflow', version=1, executor=workflow_executor)
    get_email = get_user_email(task_ref_name='get_user_email_ref', userid=workflow.input('userid'))
    sendmail = send_email(task_ref_name='send_email_ref', email=get_email.output('result'), subject='Hello from Orkes',
                          body='Test Email')
    #Order of task execution
    workflow >> get_email >> sendmail

    # Configure the output of the workflow
    workflow.output_parameters(output_parameters={
        'email': get_email.output('result')
    })
    #Run the workflow
    result = workflow.execute(workflow_input={'userid': 'user_a'})
    print(f'\nworkflow output:  {result.output}\n')
    #Stop Polling
    task_handler.stop_processes()


if __name__ == '__main__':
    main()
```

See [dynamic_workflow.py](../../examples/dynamic_workflow.py) for a fully functional example.

### Kitchen-Sink Workflow 

For a more complex workflow example with all the supported features, see [kitchensink.py](../../examples/kitchensink.py).

## Executing Workflows

The [WorkflowClient](../../src/conductor/client/workflow_client.py) interface provides all the APIs required to work with workflow executions.

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients

api_config = Configuration()
clients = OrkesClients(configuration=api_config)
workflow_client = clients.get_workflow_client() 
```

### Execute Workflow Asynchronously

Useful when workflows are long-running.

```python
from conductor.client.http.models import StartWorkflowRequest

request = StartWorkflowRequest()
request.name = 'hello'
request.version = 1
request.input = {'name': 'Orkes'}
# workflow id is the unique execution id associated with this execution
workflow_id = workflow_client.start_workflow(request)
```

### Execute Workflow Synchronously

Applicable when workflows complete very quickly - usually under 20-30 seconds.

```python
from conductor.client.http.models import StartWorkflowRequest

request = StartWorkflowRequest()
request.name = 'hello'
request.version = 1
request.input = {'name': 'Orkes'}

workflow_run = workflow_client.execute_workflow(
        start_workflow_request=request, 
        wait_for_seconds=12)
```

## Managing Workflow Executions

> [!note] 
> See [workflow_ops.py](../../examples/workflow_ops.py)  for a fully working application that demonstrates working with the workflow executions and sending signals to the workflow to manage its state.

Workflows represent the application state. With Conductor, you can query the workflow execution state anytime during its lifecycle. You can also send signals to the workflow that determines the outcome of the workflow state.

[WorkflowClient](../../src/conductor/client/workflow_client.py) is the client interface used to manage workflow executions.

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients

api_config = Configuration()
clients = OrkesClients(configuration=api_config)
workflow_client = clients.get_workflow_client()
```

### Get Execution Status

The following method lets you query the status of the workflow execution given the id. When the `include_tasks` is set, the response also includes all the completed and in-progress tasks.

```python
get_workflow(workflow_id: str, include_tasks: Optional[bool] = True) -> Workflow
```

### Update Workflow State Variables

Variables inside a workflow are the equivalent of global variables in a program.

```python
update_variables(self, workflow_id: str, variables: Dict[str, object] = {})
```

### Terminate Running Workflows

Used to terminate a running workflow. Any pending tasks are canceled, and no further work is scheduled for this workflow upon termination. A failure workflow will be triggered but can be avoided if `trigger_failure_workflow` is set to False.

```python
terminate_workflow(self, workflow_id: str, reason: Optional[str] = None, trigger_failure_workflow: bool = False)
```

### Retry Failed Workflows

If the workflow has failed due to one of the task failures after exhausting the retries for the task, the workflow can still be resumed by calling the retry.

```python
retry_workflow(self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = False)
```

When a sub-workflow inside a workflow has failed, there are two options:

1. Re-trigger the sub-workflow from the start (Default behavior).
2. Resume the sub-workflow from the failed task (set  `resume_subworkflow_tasks` to True).

### Restart Workflows

A workflow in the terminal state (COMPLETED, TERMINATED, FAILED) can be restarted from the beginning. Useful when retrying from the last failed task is insufficient, and the whole workflow must be started again.

```python
restart_workflow(self, workflow_id: str, use_latest_def: Optional[bool] = False)
```

### Rerun Workflow from a Specific Task

In the cases where a workflow needs to be restarted from a specific task rather than from the beginning, rerun provides that option. When issuing the rerun command to the workflow, you can specify the task ID from where the workflow should be restarted (as opposed to from the beginning), and optionally, the workflow's input can also be changed.

```python
rerun_workflow(self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequest)
```

> [!tip]
> Rerun is one of the most powerful features Conductor has, giving you unparalleled control over the workflow restart.

### Pause Running Workflow

A running workflow can be put to a PAUSED status. A paused workflow lets the currently running tasks complete but does not schedule any new tasks until resumed.

```python
pause_workflow(self, workflow_id: str)
```

### Resume Paused Workflow

Resume operation resumes the currently paused workflow, immediately evaluating its state and scheduling the next set of tasks.

```python
resume_workflow(self, workflow_id: str)
```

### Searching for Workflows

Workflow executions are retained until removed from the Conductor. This gives complete visibility into all the executions an application has - regardless of the number of executions. Conductor has a powerful search API that allows you to search for workflow executions.

```python
search(self, start, size, free_text: str = '*', query: str = None) -> ScrollableSearchResultWorkflowSummary
```

* **free_text**: Free text search to look for specific words in the workflow and task input/output.
* **query** SQL-like query to search against specific fields in the workflow.

Here are the supported fields for **query**:

| Field       | Description     |
|-------------|-----------------|
| status      |The status of the workflow. |
| correlationId |The ID to correlate the workflow execution to other executions.   |
| workflowType |The name of the workflow. |
 | version     |The version of the workflow. |
|startTime|The start time of the workflow is in milliseconds.|

## Handling Failures, Retries and Rate Limits

Conductor lets you embrace failures rather than worry about the complexities introduced in the system to handle failures.

All the aspects of handling failures, retries, rate limits, etc., are driven by the configuration that can be updated in real time without re-deploying your application.

### Retries

Each task in the Conductor workflow can be configured to handle failures with retries, along with the retry policy (linear, fixed, exponential backoff) and maximum number of retry attempts allowed.

See [Error Handling](https://orkes.io/content/error-handling) for more details.

### Rate Limits

What happens when a task is operating on a critical resource that can only handle a few requests at a time? Tasks can be configured to have a fixed concurrency (X request at a time) or a rate (Y tasks/time window).

### Task Registration

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import TaskDef
from conductor.client.orkes_clients import OrkesClients


def main():
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    metadata_client = clients.get_metadata_client()

    task_def = TaskDef()
    task_def.name = 'task_with_retries'
    task_def.retry_count = 3
    task_def.retry_logic = 'LINEAR_BACKOFF'
    task_def.retry_delay_seconds = 1

    # only allow 3 tasks at a time to be in the IN_PROGRESS status
    task_def.concurrent_exec_limit = 3

    # timeout the task if not polled within 60 seconds of scheduling
    task_def.poll_timeout_seconds = 60

    # timeout the task if the task does not COMPLETE in 2 minutes
    task_def.timeout_seconds = 120

    # for the long running tasks, timeout if the task does not get updated in COMPLETED or IN_PROGRESS status in
    # 60 seconds after the last update
    task_def.response_timeout_seconds = 60

    # only allow 100 executions in a 10-second window! -- Note, this is complementary to concurrent_exec_limit
    task_def.rate_limit_per_frequency = 100
    task_def.rate_limit_frequency_in_seconds = 10

    metadata_client.register_task_def(task_def=task_def)
```

```json
{
  "name": "task_with_retries",
  
  "retryCount": 3,
  "retryLogic": "LINEAR_BACKOFF",
  "retryDelaySeconds": 1,
  "backoffScaleFactor": 1,
  
  "timeoutSeconds": 120,
  "responseTimeoutSeconds": 60,
  "pollTimeoutSeconds": 60,
  "timeoutPolicy": "TIME_OUT_WF",
  
  "concurrentExecLimit": 3,
  
  "rateLimitPerFrequency": 0,
  "rateLimitFrequencyInSeconds": 1
}
```

#### Update Task Definition:

```shell
POST /api/metadata/taskdef -d @task_def.json
```

See [task_configure.py](../../examples/task_configure.py) for a detailed working app.

## Using Conductor in Your Application

Conductor SDKs are lightweight and can easily be added to your existing or new Python app. This section will dive deeper into integrating Conductor in your application.

### Adding Conductor SDK to Your Application

Conductor Python SDKs are published on PyPi @ https://pypi.org/project/conductor-python/:

```shell
pip3 install conductor-python
```

### Testing Workflows

Conductor SDK for Python provides a complete feature testing framework for your workflow-based applications. The framework works well with any testing framework you prefer without imposing any specific framework.

The Conductor server provides a test endpoint `POST /api/workflow/test` that allows you to post a workflow along with the test execution data to evaluate the workflow.

The goal of the test framework is as follows:

1. Ability to test the various branches of the workflow.
2. Confirm the workflow execution and tasks given a fixed set of inputs and outputs.
3. Validate that the workflow completes or fails given specific inputs.

Here are example assertions from the test:

```python

...
test_request = WorkflowTestRequest(name=wf.name, version=wf.version,
                                       task_ref_to_mock_output=task_ref_to_mock_output,
                                       workflow_def=wf.to_workflow_def())
run = workflow_client.test_workflow(test_request=test_request)

print(f'completed the test run')
print(f'status: {run.status}')
self.assertEqual(run.status, 'COMPLETED')

...

```

> [!note]
> Workflow workers are your regular Python functions and can be tested with any available testing framework.

#### Example Unit Testing Application

See [test_workflows.py](../../examples/test_workflows.py) for a fully functional example of how to test a moderately complex workflow with branches.

### Workflow Deployments Using CI/CD

> [!tip]
> Treat your workflow definitions just like your code. Suppose you are defining the workflows using UI. In that case, we recommend checking the JSON configuration into the version control and using your development workflow for CI/CD to promote the workflow definitions across various environments such as Dev, Test, and Prod.

Here is a recommended approach when defining workflows using JSON:

* Treat your workflow metadata as code.
* Check in the workflow and task definitions along with the application code.
* Use `POST /api/metadata/*` endpoints or MetadataClient (`from conductor.client.metadata_client import MetadataClient`) to register/update workflows as part of the deployment process.
* Version your workflows. If there is a significant change, change the version field of the workflow. See versioning workflows below for more details.

### Versioning Workflows

A powerful feature of Conductor is the ability to version workflows. You should increment the version of the workflow when there is a significant change to the definition. You can run multiple versions of the workflow at the same time. When starting a new workflow execution, use the `version` field to specify which version to use. When omitted, the latest (highest-numbered) version is used.

* Versioning allows safely testing changes by doing canary testing in production or A/B testing across multiple versions before rolling out.
* A version can also be deleted, effectively allowing for "rollback" if required.