# Workflows

Use `ConductorWorkflow` to build a workflow definition and `WorkflowExecutor`
to register, start, inspect, pause, resume, retry, or terminate executions.

```python
from conductor.client.workflow.conductor_workflow import ConductorWorkflow

workflow = ConductorWorkflow(name="greetings", version=1, executor=executor)
workflow >> greet(task_ref_name="greet", name=workflow.input("name"))
workflow.output_parameters({"result": "${greet.output.result}"})
workflow.register(overwrite=True)
```

Use system task classes for HTTP, wait, switch, fork/join, sub-workflow, and
other orchestration primitives. See the detailed [workflow API guide](WORKFLOW.md)
and [workflow lifecycle](workflow-lifecycle.md). Keep versioned definitions
compatible with callers; never place secrets in workflow input.
