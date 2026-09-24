# Server decision tools

`DecisionModelTool` exposes Conductor's `DECISION_MODEL` task to an agent. The
server owns provider credentials, inference, response validation, and usage
reporting. The SDK sends tool configuration and starts no Python tool worker.
This requires a server that supports the `decision_model` tool type.

```python
from conductor.ai.agents import Agent, AgentRuntime, DecisionModelTool, agent

class Support:
    @agent(
        model="openai/gpt-4o-mini",
        tools=[DecisionModelTool(
            name="choose_team",
            description="Choose the team responsible for a support issue.",
            provider="jev",
            model="jev-1.13",
            questions={"team": {
                "type": "choice",
                "instructions": "Which team should handle the issue?",
                "choices": {"billing": "Payment issues", "technical": "Software issues"},
            }},
            max_calls=1,
        )],
    )
    def assistant(self):
        """Call choose_team with the supplied state and report its decision."""

with AgentRuntime() as runtime:
    result = runtime.run(Agent.from_instance(Support(), "assistant"),
                         "My invoice was charged twice.", timeout=120)
```

Select an orchestration model configured on your server. It handles conversation
and tool calling; the decision model evaluates state. Both can incur inference
costs. The Jev provider and its API key must be configured on the server, not in
the agent's environment, prompt, or tool arguments.

Provider and model are fixed tool configuration. With fixed `questions`, only
`state` is exposed as a tool argument. Omitting `questions` exposes a typed
questions schema too. Generated arguments cannot override the configured provider,
model, or fixed questions.

Questions have `type` and `instructions`:

| Type | Additional fields | Answer |
| --- | --- | --- |
| `choice` | `choices`: 2–255 named options with descriptions | `choice`: one of the option names |
| `score` | `scale`: 2–10 ordered descriptions | `score`: number from 0 to scale length minus one |
| `boolean` | None | `probability`: number from 0 to 1 |

The server returns `model`, `answers`, `usage`, `latencyMs`, and optional
`requestId`. Usage fields are `inputTokens`, `outputTokens`, and optional `cost`
and `currency`. Unknown costs are omitted, not reported as zero. Confidence is
optional per answer. Read the decision task's output for exact values; the agent's
final conversational summary is model-generated.

The compiled tool task has zero retries by default. A caller explicitly rerunning
a workflow can still trigger another inference request. No Jev-specific HTTP or
authentication code belongs in the SDK.
