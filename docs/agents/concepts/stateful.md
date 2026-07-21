# Stateful agents

**Audience:** applications that need durable, session-scoped conversation state.

## Prerequisites

Choose a stable `session_id`, define retention/deletion policy, and classify which
user data may be persisted before enabling state.

Set `stateful=True` when a session needs durable conversation state and worker
isolation. Pass a stable session identifier when resuming a conversation, use
`ConversationMemory` or `SemanticMemory` only for data appropriate to persist,
and define retention rules for user data.

Stateful runs use liveness monitoring by default. Configure it with
`CONDUCTOR_AGENT_LIVENESS_*` and use `resume()` after a process restart.

## Expected result and failures

Runs with the same session identifier can resume the intended durable state.
Unexpected context growth should be handled with retention, memory limits, or
context condensation—not by placing unbounded history in prompts.

## Next steps

Read [streaming and approval](streaming-hitl.md), [security](../../security.md),
and [runtime modes](deploy-serve-run.md).
