# Run your first durable Conductor agent

**Prerequisites:** Python 3.10+, a reachable Conductor server, and an LLM provider
credential configured on that server.

## 1. Configure the client

```shell
pip install 'conductor-python[agents]'
export CONDUCTOR_SERVER_URL=http://localhost:8080/api
export CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini
```

For authenticated servers, also set `CONDUCTOR_AUTH_KEY` and
`CONDUCTOR_AUTH_SECRET`. Do not export provider secrets into application source;
configure the provider integration on the server.

## 2. Run the maintained example

```shell
cd examples/agents
python 01_basic_agent.py
```

Expected result: an `AgentResult` with the model response. If the request cannot
reach the server, check [server setup](../server-setup.md). If the agent cannot
call a model, check the server-side provider integration.

## 3. Create the same agent

```python
from conductor.ai.agents import Agent, AgentRuntime

agent = Agent(name="greeter", model="openai/gpt-4o-mini",
              instructions="You are a friendly assistant.")
with AgentRuntime() as runtime:
    result = runtime.run(agent, "Say hello.")
    print(result.output)
```

Next: [tools](concepts/tools.md), [runtime modes](concepts/deploy-serve-run.md),
or [framework bridges](README.md#framework-bridges).
