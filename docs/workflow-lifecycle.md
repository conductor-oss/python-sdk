# Workflow lifecycle and versioning

Register a versioned workflow, start it through `WorkflowExecutor`, and inspect
its execution before changing behavior. Additive output changes are normally
safe; renamed inputs, removed outputs, and changed task references are breaking
and require a new workflow version.

Use pause/resume for controlled maintenance, retry only transient failures, and
terminate executions with an explicit reason. Inspect failed tasks before retrying
to avoid replaying unsafe side effects. See [WORKFLOW.md](WORKFLOW.md) for the
complete lifecycle API.
