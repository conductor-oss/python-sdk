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

Decision: [decision_router.py](decision_router.py) uses a decision `ToolDef` as a
router selector, with normal chat agents as executable children. Deployment
compiles it into one decision-backed `SWITCH`; the tool is not deployed as a
standalone agent. It compiles by default; pass `--run` for inference.

`decision_tool.py` shows the other agent pattern: a normal chat agent calls
Decision inference as a server-side tool. The server maps the tool call to a
branchless decision-backed `SWITCH`; no tool worker is needed.

For direct use in a traditional workflow, see
[`ai_decision_routing.py`](../agentic_workflows/ai_decision_routing.py).
