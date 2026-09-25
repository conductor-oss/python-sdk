# Conductor-agent examples

Runnable Python examples for durable Conductor agents. Start a server, configure
the provider integration on that server, then use the canonical environment names:

```shell
export CONDUCTOR_SERVER_URL=http://localhost:8080/api
export CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini
```

## Start here

| Example | Demonstrates |
|---|---|
| `01_basic_agent.py` | A minimal agent and `runtime.run()`. |
| `02a_simple_tools.py` | Python worker tools. |
| `05_handoffs.py` | Agent handoffs. |
| `09_human_in_the_loop.py` | Approval and resume. |
| `57_plan_dry_run.py` | Compile without running. |
| `63b_serve.py` | Deploy and serve workers. |

Run an example from this directory: `python 01_basic_agent.py`. For production,
deploy with `AgentRuntime.deploy()` and run workers with `AgentRuntime.serve()`;
the Conductor CLI manages the server with `conductor server start`.

Framework-specific examples are in [ADK](adk/README.md),
[LangGraph](langgraph/README.md), and [OpenAI Agents SDK](openai/README.md).
Review tool side effects before using real credentials.

## Jev agents

`python examples/agents/jev_agent.py` (from the repository root) compiles the
`jev_support_agent` definition without inference. Pass `--run` to explicitly start
it and poll for completion. The example uses `JevAgent` and `AgentRuntime`, requires
no chat model or Python worker, and prints structured `output.result` data:
`model`, `answers`, `usage`, `latencyMs`, and optional `requestId`.
Configure Jev credentials only on Conductor; the SDK calls the agent APIs.

The equivalent generic definition is
`AgentDef(name="jev_support_agent", kind="jev", model="jev-1.13", questions=questions)`.
Both forms support `runtime.plan()`, `runtime.start()`, and deployment. Questions
require `instructions`: `ChoiceQuestion` uses a choices map, `ScoreQuestion` uses
an ordered scale, and `BooleanQuestion` returns a probability. If questions are
omitted from the definition, pass `context={"questions": questions}` to `plan()`
or `start()`. There is no public Jev tool or standalone decision-model API.
