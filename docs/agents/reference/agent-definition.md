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

## Jev agents

Use `JevAgent(name, model="jev-1.13", questions=questions)` or
`AgentDef(name=name, kind="jev", model="jev-1.13", questions=questions)`.
Questions are dictionaries with `instructions` and a `type`:
`choice` uses a `choices` map, `score` uses an ordered `scale`, and `boolean`
returns a probability. Omit questions to supply `context={"questions": questions}`.

Use `runtime.plan(agent, prompt)` to compile or `runtime.start(agent, prompt)`
to run. Call `handle.join()` and check `result.is_success` or `result.error`.
`result.output["result"]` preserves `model`, `answers`, `usage`, `latencyMs`
and optional `requestId`. Credentials and inference stay on Conductor.
No chat model or Python worker is needed.

[Example](../../../examples/agents/jev_agent.py)

For server-side Jev routing, use `Agent(strategy="router", router=selector,
agents=children)`. The Jev selector must have one fixed choice question whose
choice keys match the child agent names. No parent chat model is needed.
Routing runs one child and preserves its structured result.
