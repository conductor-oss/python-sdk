# Conductor agents

**Audience:** Python developers authoring durable, LLM-backed Conductor agents.

## Prerequisites

Install `conductor-python[agents]`, configure a reachable Conductor server, and
configure the selected provider on that server. Keep provider credentials out of
Python source and workflow input.

## Define an agent

Create an `Agent` with a stable name, `provider/model` identifier, instructions,
and optional tools or sub-agents. `@agent` turns a function docstring or return
value into instructions; `Agent.from_instance()` discovers decorated methods on
an object.

```python
from conductor.ai.agents import Agent, AgentRuntime, tool

@tool
def get_weather(city: str) -> str:
    return f"Weather for {city}"

agent = Agent(name="weather", model="openai/gpt-4o-mini",
              instructions="Answer concisely.", tools=[get_weather])
with AgentRuntime() as runtime:
    print(runtime.run(agent, "Weather in Seattle?").output)
```

## Instructions and runtime overrides

`instructions` may be a string, a callable evaluated during compilation, or a
`PromptTemplate` stored on the server. Use `RunSettings` for one execution's
model, temperature, token, or reasoning override; do not mutate a shared agent
definition per request. An omitted model is valid only for inherited-model or
external-agent designs.

## Expected result

`runtime.run()` compiles the agent, starts required local tool workers, and
returns an `AgentResult`. The Conductor UI shows the durable execution and its
tool calls.

## Common failures

- A model error normally means the provider credential or model is missing on
  the **server**, not merely in the Python process.
- A name that does not match `^[a-zA-Z_][a-zA-Z0-9_-]*$` is rejected.
- A closure or non-importable tool cannot be recovered by a worker process.

## Next steps

Use [tools](tools.md) for capabilities, [multi-agent](multi-agent.md) for
composition, and [runtime modes](deploy-serve-run.md) for deployment.
