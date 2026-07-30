# Google ADK

**Prerequisites:** install the `adk` extra and configure the selected provider on
the Conductor server.

Install the optional dependency:

```shell
pip install 'conductor-python[adk]'
```

Pass a standard Google ADK `Agent` to `AgentRuntime.run()`. The runtime detects
the framework object, serializes its instructions, tools, and sub-agent graph,
and starts a durable Conductor-agent execution.

```python
from conductor.ai.agents import AgentRuntime
from google.adk.agents import Agent

agent = Agent(name="adk_greeter", model="gemini-2.0-flash",
              instruction="Be concise.")
with AgentRuntime() as runtime:
    print(runtime.run(agent, "Say hello.").output)
```

See [runnable ADK examples](../../../examples/agents/adk/README.md). Provider
credentials must be configured on the Conductor server.

**Expected result:** the native ADK agent runs as a durable Conductor-agent
execution. **Next:** review [tools](../concepts/tools.md) and [runtime modes](../concepts/deploy-serve-run.md).
