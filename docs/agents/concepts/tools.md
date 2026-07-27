# Tools

**Audience:** authors exposing Python or server-native capabilities to a
Conductor agent.

## Prerequisites

Install `conductor-python[agents]`. Tool functions must be importable by worker
processes and safe to receive more than once.

## Define a Python tool

`@tool` converts Python type hints and docstrings into a tool schema. Each call is
a durable, retryable Conductor task.

```python
from conductor.ai.agents import ToolContext, tool

@tool(credentials=["GITHUB_TOKEN"])
def create_issue(title: str, context: ToolContext) -> str:
    token = context.get_credential("GITHUB_TOKEN")
    return f"created: {title}"
```

## Choose the right tool

| Need | Factory or pattern |
|---|---|
| Python business logic | `@tool` |
| HTTP endpoint | `http_tool` |
| OpenAPI/Postman discovery | `api_tool` |
| MCP server | `mcp_tool` |
| Human decision | `human_tool` |
| PDF, media, or vector retrieval | built-in PDF/media/index/search factories |
| Another Conductor agent | `agent_tool` |

The built-in factories compile to Conductor system tasks where possible; prefer
them to hand-written wrapper workers. Declare credentials on the tool or agent so
the server resolves them into task runtime metadata. Do not read credentials from
ambient environment variables or store them in workflow input.

Use command/code tools only with an allowlist. See [security](../../security.md)
and the complete Python signatures in [API reference](../reference/api.md).

## Reliability and approval

Use `retry_count`, `retry_delay_seconds`, `timeout_seconds`, and an idempotency
key appropriate to the external system. Mark destructive operations with
`approval_required=True` or model them with `human_tool`. A tool may accept
`ToolContext` for execution ID, session state, and resolved credentials.

## Expected result and failures

A successful tool appears as a named task in the agent execution. A task that
remains `SCHEDULED` has no compatible worker polling; a failed credential lookup
must be fixed in the server credential store rather than by adding a secret to
the prompt.

## Next steps

Continue with [guardrails](guardrails.md), [streaming and approval](streaming-hitl.md),
or [security](../../security.md).
