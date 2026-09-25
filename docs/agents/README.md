# Conductor Agent Python SDK

Build durable Python AI agents on Conductor. Agents can use local Python tools,
wait for people, execute dynamic plans, and recover after process restarts because
Conductor persists execution state.

## Install

```shell
pip install 'conductor-python[agents]'
```

Requirements: Python 3.10+ and a Conductor server with an LLM provider configured
server-side. Replace example model names with a model enabled on that server.

## Start here

- [Getting started](getting-started.md) — configure a server and run a basic agent.
- [Deploy · Serve · Run · Plan](concepts/deploy-serve-run.md) — choose a runtime mode.
- [Scheduling](concepts/scheduling.md) — manage deployed-agent schedules.

## Build agents

- [Agents](concepts/agents.md), [tools](concepts/tools.md), and [multi-agent](concepts/multi-agent.md)
- [Guardrails](concepts/guardrails.md), [termination](concepts/termination.md), [callbacks](concepts/callbacks.md)
- [Stateful agents](concepts/stateful.md), [streaming and HITL](concepts/streaming-hitl.md), and [structured output](concepts/structured-output.md)

## Framework bridges

- [Google ADK](frameworks/google-adk.md), [LangChain](frameworks/langchain.md), and [LangGraph](frameworks/langgraph.md)
- [OpenAI Agents SDK](frameworks/openai.md) and [Claude Agent SDK](frameworks/claude-agent-sdk.md)

## Operate and inspect

- [Runtime reference](reference/runtime.md), [control-plane reference](reference/client.md), and [API map](reference/api.md)
- [Agent-definition fields](reference/agent-definition.md) and [configuration contract](reference/agent-schema.md)

## What Conductor adds

| Capability | Conductor agent runtime |
|---|---|
| Process recovery | Durable workflow state resumes from completed work. |
| Python tools | Tools run as independently scalable Conductor worker tasks. |
| Long-running work | Human approval, schedules, and events do not occupy application threads. |
| Dynamic execution | Plans become durable, inspectable sub-workflows. |
| Observability | Inputs, outputs, tool calls, retries, and status share one execution record. |
