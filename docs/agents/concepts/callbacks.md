# Callbacks

**Audience:** applications that need local observation or lightweight reactions to
Conductor-agent lifecycle events.

## Prerequisites

Register callback handlers before starting the runtime. Treat callback payloads as
potentially sensitive execution data.

`CallbackHandler` observes agent lifecycle events and supports hooks for messages,
tool calls, results, and failures. Keep callback work fast and non-blocking; move
durable business effects into a tool or workflow task. Use structured logging and
redact credentials and sensitive user data.

## Expected result and failures

Callbacks receive lifecycle notifications without changing the durable workflow
unless they explicitly fail the local process. Do not use them as the only record
of an audit, notification, or external write: process restarts can interrupt local
observers.

## Next steps

Use [streaming](streaming-hitl.md) for caller-visible events and [tools](tools.md)
for durable side effects.
