# Workers

Workers poll a named task queue, execute idempotent business logic, and return a
result. Define a function worker with `@worker_task`, then run it with
`TaskHandler` or `AsyncTaskRunner`.

```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name="greet")
def greet(name: str) -> dict:
    return {"result": f"Hello {name}"}
```

Use explicit retries, task timeouts, and domains for production isolation. Stop
task handlers during application shutdown. See the detailed [worker guide](WORKER.md),
[reliability](reliability.md), and [workflow testing](workflow-testing.md).
