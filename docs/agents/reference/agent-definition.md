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

Use `JevAgent(name="jev_support_agent", model="jev-1.13", questions=questions)`
or `AgentDef(name="jev_support_agent", kind="jev", model="jev-1.13", questions=questions)`.
Both serialize through `AgentConfigSerializer` with `kind: "jev"` and use the
standard agent runtime APIs. Jev credentials and provider HTTP calls stay on
Conductor. A chat model and Python worker are not required.

Each question requires `instructions`. Use `ChoiceQuestion(instructions, choices)`
for a choices map, `ScoreQuestion(instructions, scale)` for an ordered scale, or
`BooleanQuestion(instructions)` for a probability response. Plain dictionaries
with `type` and the corresponding fields are also accepted. Omit definition
questions to supply them in `context={"questions": questions}` for each run.

`runtime.plan(agent, prompt, context=context)` calls `/agent/compile` without
inference. `runtime.start(agent, prompt, context=context)` calls `/agent/start`;
`handle.join()` polls status until complete. Check `result.is_success` and report
`result.error` on failure. `result.output["result"]` retains the structured
`model`, `answers`, `usage`, `latencyMs`, and optional `requestId` fields.

See [the runnable Jev example](../../../examples/agents/jev_agent.py), which
compiles by default and requires `--run` to start inference. Jev is supported
only as an agent definition; there is no public Jev task or decision-model tool.
