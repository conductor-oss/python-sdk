# AgentClient control-plane reference

**Audience:** applications that need direct control-plane access without managing
local Python tool workers.

## Prerequisites

Use a configured SDK client and ensure tools are server-native or already served
by a deployed worker process.

`AgentClient` is the typed transport interface for `/agent/*` endpoints. Its
`OrkesAgentClient` implementation shares the SDK transport, token refresh, and
authentication behavior.

| Operation | Method |
|---|---|
| Compile, deploy, start | `compile_agent`, `deploy_agent`, `start_agent` |
| Inspect | `get_status`, `get_execution`, `list_executions` |
| Human/control actions | `respond`, `stop`, `signal` |
| Stream events | `stream_sse` / `stream_sse_async` |

Every operation has an async counterpart. `SSEUnavailableError` lets callers
choose a status-polling fallback. Use `AgentRuntime` unless an application needs
direct control-plane integration.

## Expected result and next steps

`stop`, `signal`, and `respond` change a durable execution; authorize callers and
make externally triggered requests idempotent. See [streaming and approval](../concepts/streaming-hitl.md) and [runtime](runtime.md).
