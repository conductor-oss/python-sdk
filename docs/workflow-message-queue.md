# Workflow Message Queue (WMQ)

Send messages to a running workflow and process them inside the workflow using the
`PULL_WORKFLOW_MESSAGES` system task.

## Server requirement

WMQ must be enabled on the Conductor server:

```properties
conductor.workflow-message-queue.enabled=true
```

---

## Sending a message

After starting (or executing) a workflow you can push any JSON-serialisable dict
to it using `executor.send_message` or `workflow_client.send_message`.

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor

config = Configuration()  # reads CONDUCTOR_SERVER_URL / CONDUCTOR_AUTH_TOKEN from env
executor = WorkflowExecutor(config)

# --- start a workflow that has a PULL_WORKFLOW_MESSAGES task in it ---
workflow_id = executor.start_workflow(
    StartWorkflowRequest(name="order_processing", input={"orderId": "ORD-42"})
)

# --- send a message to the running workflow ---
message_id = executor.send_message(
    workflow_id,
    {"event": "payment_confirmed", "amount": 99.99, "currency": "USD"},
)
print(f"Message enqueued: {message_id}")
```

You can call `send_message` multiple times; each call returns a unique UUID.

```python
# Send a batch of status updates
for status in ["PICKED", "SHIPPED", "OUT_FOR_DELIVERY"]:
    executor.send_message(workflow_id, {"status": status})
```

---

## Defining a workflow that receives messages

Use `PullWorkflowMessagesTask` inside your workflow definition to consume the queue.

```python
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.pull_workflow_messages_task import PullWorkflowMessagesTask
from conductor.client.workflow.task.simple_task import SimpleTask

# Pull up to 5 messages at a time
pull = PullWorkflowMessagesTask(task_ref_name="pull_messages", batch_size=5)

process = SimpleTask(
    task_def_name="process_message_worker",
    task_reference_name="process_message",
)
# Pass pulled messages to the next task via input parameter references
process.input_parameters["messages"] = "${pull_messages.output.messages}"

wf = (
    ConductorWorkflow(executor=executor, name="order_processing", version=1)
    .add(pull)
    .add(process)
)

wf.register(overwrite=True)
```

### Task output shape

When messages are available the `PULL_WORKFLOW_MESSAGES` task output looks like:

```json
{
  "messages": [
    {
      "id": "f3c2a1b0-...",
      "workflowId": "<workflow-instance-id>",
      "payload": { "event": "payment_confirmed", "amount": 99.99 },
      "receivedAt": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

Reference individual fields in subsequent tasks:

```python
next_task.input_parameters["firstMessage"] = "${pull_messages.output.messages[0].payload}"
```

---

## Using the low-level client directly

If you prefer the `WorkflowClient` directly:

```python
from conductor.client.orkes_clients import OrkesClients

clients = OrkesClients(config)
workflow_client = clients.get_workflow_client()

message_id = workflow_client.send_message(
    workflow_id,
    {"type": "notification", "text": "Hello from outside the workflow"},
)
```

---

## Error handling

| HTTP status | Reason | What to do |
|-------------|--------|------------|
| `404 Not Found` | Workflow ID does not exist | Verify the workflow was started successfully |
| `409 Conflict` | Workflow is not `RUNNING` | Check workflow status before sending |
| `429 Too Many Requests` | Queue is at capacity (default 1 000 messages) | Back off and retry, or increase `conductor.workflow-message-queue.maxQueueSize` |

```python
from conductor.client.http.rest import ApiException

try:
    executor.send_message(workflow_id, {"ping": True})
except ApiException as e:
    if e.status == 404:
        print("Workflow not found")
    elif e.status == 409:
        print("Workflow is not running")
    elif e.status == 429:
        print("Queue full — back off and retry")
    else:
        raise
```
