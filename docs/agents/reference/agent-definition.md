# Agent definition fields

`Agent` accepts a name, `provider/model`, instructions, tools, sub-agents, and
runtime policy. Important fields include `strategy`, `max_turns`, `max_tokens`,
`temperature`, `timeout_seconds`, `output_type`, `guardrails`, `termination`,
`handoffs`, `credentials`, `stateful`, `enable_planning`, `callbacks`, and
`fallback`.

Names must match `^[a-zA-Z_][a-zA-Z0-9_-]*$`. Empty models represent inherited or
external-agent behavior. The complete constructor and serialization semantics are
maintained in [api-reference.md](../api-reference.md) and
`AgentConfigSerializer`; use those sources when adding a newly supported field.
