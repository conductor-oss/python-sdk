# Streaming and human-in-the-loop

**Audience:** interactive applications that display progress or require a human
decision before a tool executes.

## Prerequisites

Keep the execution ID returned by the runtime or handle. Define who may approve,
reject, or respond and validate every human-supplied value.

`runtime.stream()` yields `AgentEvent` values while an execution runs; when SSE is
unavailable, the runtime can fall back to status polling. Use `human_tool` or a
wait tool to pause work, then approve, reject, or respond through `AgentHandle`.

Do not treat streamed content as a final result until the terminal event arrives.
Use event execution IDs when approving nested or sub-agent work.

## Approval pattern

Use `human_tool` or a wait-for-message tool for an explicit durable pause. Resume
through the handle/client control plane rather than relying on an in-memory web
request. Make approval actions idempotent because callers may retry a network
request.

## Expected result and cleanup

The stream yields progress followed by a terminal event, while an approval task
remains visible as waiting work in Conductor. Close stream consumers and stop
short-lived runtimes after the terminal event.

## Next steps

See [tools](tools.md), [agent client](../reference/client.md), and
[callbacks](callbacks.md).
