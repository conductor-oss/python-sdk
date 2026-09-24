# Decision tools

`DecisionModelTool` calls the server's `DECISION_MODEL` task. Configure the
provider credential on Conductor; no Python worker is needed.

```python
from conductor.ai.agents import Agent, AgentRuntime, DecisionModelTool, agent

class Support:
    @agent(model="openai/gpt-4o-mini", tools=[DecisionModelTool(
        "choose_team", "Choose the responsible support team.",
        provider="jev", model="jev-1.13",
        questions={"team": {
            "type": "choice", "instructions": "Which team should handle this?",
            "choices": {"billing": "Payment issues", "technical": "Software issues"},
        }},
    )])
    def assistant(self):
        """Call choose_team and report its decision."""

with AgentRuntime() as runtime:
    result = runtime.run(Agent.from_instance(Support(), "assistant"),
                         "My invoice was charged twice.", timeout=120)
```

Provider, model, and supplied questions are fixed configuration. Omitting
`questions` lets the agent supply them. Types: `choice` with named `choices`,
`score` with an ordered `scale`, and `boolean` returning a probability.

Requires a server with [decision-model support](https://github.com/conductor-oss/conductor/pull/1664).
The chat model handles orchestration; Jev evaluates state. Both incur inference
costs. Read the decision task's output for exact answers and usage.
