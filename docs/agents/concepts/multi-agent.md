# Multi-agent systems

**Audience:** authors composing specialists into a durable Conductor-agent graph.

## Prerequisites

Each participating agent needs a unique stable name and bounded execution policy.
Start with a single agent and a tested tool before introducing delegation.

`Agent(agents=[...], strategy=...)` supports `SEQUENTIAL`, `PARALLEL`, `HANDOFF`,
`ROUTER`, `ROUND_ROBIN`, `RANDOM`, `SWARM`, `MANUAL`, and `PLAN_EXECUTE`.

- Sequential and parallel strategies compose deterministic work.
- Handoff, router, and swarm transfer control between agents; restrict transitions
  and define an empty-safe fallback.
- `PLAN_EXECUTE` compiles a typed `Plan` into a durable sub-workflow and can replan.
- `agent_tool(child)` calls a child agent as a tool instead of transferring control.

Set a termination condition and a turn/token limit for every open-ended design.
See [termination](termination.md), [plans](../reference/agent-definition.md), and
[writing examples](../../../examples/agents/README.md).

## Handoffs, routers, and plans

Use `HANDOFF` when the model should select a specialist, `ROUTER` when an explicit
router chooses one, and `agent_tool(child)` when a parent needs a child's result
without transferring control. `PLAN_EXECUTE` is for typed, inspectable plans that
must survive restarts; provide a planner and an optional fallback/replan policy.
Restrict allowed transitions so an unexpected model output cannot reach an unsafe
specialist.

## Expected result and failures

The compiled parent contains durable child/sub-workflow work and each child is
visible in execution history. If a graph loops, add `max_turns`, termination, and
a bounded planner/replan policy before retrying.

## Next steps

Read [termination](termination.md), [stateful agents](stateful.md), and the
[agent definition reference](../reference/agent-definition.md).
