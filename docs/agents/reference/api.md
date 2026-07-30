# Agent API map

| Need | Python API | Guide |
|---|---|---|
| Define an agent | `Agent`, `@agent`, `Agent.from_instance` | [Agents](../concepts/agents.md) |
| Define tools | `@tool`, `ToolDef`, built-in tool factories | [Tools](../concepts/tools.md) |
| Run lifecycle operations | `AgentRuntime`, module-level helpers | [Runtime](runtime.md) |
| Control an execution | `AgentClient`, `AgentHandle` | [Control plane](client.md) |
| Add safety controls | guardrails and termination classes | [Guardrails](../concepts/guardrails.md) |
| Compose agents | `Strategy`, handoffs, `plan_execute` | [Multi-agent](../concepts/multi-agent.md) |
| Bridge frameworks | framework extras | [Framework bridges](../README.md) |

All public agent imports are available from `conductor.ai.agents`; detailed legacy
API lists remain available through [api-reference.md](../api-reference.md).
