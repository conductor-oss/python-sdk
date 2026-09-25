# Workflow testing

Use the SDK workflow-test utilities to validate definitions with controlled task
outputs before deploying. Cover successful paths, retryable and terminal failures,
branching, timeouts, and workflow outputs.

```shell
python -m pytest tests/unit
```

The maintained examples and detailed API are in [WORKFLOW_TESTING.md](WORKFLOW_TESTING.md).
Do not run examples with production credentials unless their external side effects
have been reviewed.
