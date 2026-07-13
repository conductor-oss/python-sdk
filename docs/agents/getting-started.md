# Getting started

## Under 30 seconds

The agents API ships as an extra of `conductor-python` (see `pyproject.toml`).

```bash
pip install 'conductor-python[agents]'
```

Or, per framework, install just what you need — e.g. `conductor-python[langchain]`,
`conductor-python[adk]`, `conductor-python[claude]`.

Point the SDK at a running Conductor Agent server (defaults to `http://localhost:8080/api`):

```bash
export CONDUCTOR_SERVER_URL=http://localhost:8080/api
export OPENAI_API_KEY=<YOUR-KEY>
export AGENTSPAN_LLM_MODEL=openai/gpt-4o-mini
```

Write `hello.py`:

```python
from conductor.ai.agents import Agent, AgentRuntime

agent = Agent(
    name="greeter",
    model="anthropic/claude-sonnet-4-6",
    instructions="You are a friendly assistant. Keep responses brief.",
)

with AgentRuntime() as runtime:
    result = runtime.run(agent, "Say hello and tell me a fun fact about Python.")
    print(result.output)
```

Run it:

```bash
uv run python hello.py
```

That is the whole loop: define an `Agent`, open an `AgentRuntime`, call `run`. The
runtime compiles the agent to a workflow, starts it, and blocks until it returns an
[`AgentResult`](api-reference.md#agentresult). `result.print_result()` pretty-prints
the output if you prefer.

## Environment variables

Connection, auth, and log level come from the standard `Configuration()` — used by
`AgentRuntime()` with no arguments — not from `AgentConfig`:

| Variable | Default | Purpose |
|---|---|---|
| `CONDUCTOR_SERVER_URL` (falls back to `AGENTSPAN_SERVER_URL`) | `http://localhost:8080/api` | Server base URL |
| `CONDUCTOR_AUTH_KEY` | — | Key/secret auth — key |
| `CONDUCTOR_AUTH_SECRET` | — | Key/secret auth — secret |
| `CONDUCTOR_LOG_LEVEL` (falls back to `AGENTSPAN_LOG_LEVEL`) | `INFO` | Log level |

`AgentConfig.from_env()` reads the agent-runtime *behaviour* knobs (all optional —
defaults shown):

| Variable | Default | Purpose |
|---|---|---|
| `AGENTSPAN_WORKER_POLL_INTERVAL` | `100` | Worker poll interval (ms) |
| `AGENTSPAN_WORKER_THREADS` | `1` | Worker thread count |
| `AGENTSPAN_AUTO_START_WORKERS` | `true` | Auto-start local tool workers |
| `AGENTSPAN_DAEMON_WORKERS` | `true` | Run workers as daemon threads |
| `AGENTSPAN_INTEGRATIONS_AUTO_REGISTER` | `false` | Auto-register provider integrations |
| `AGENTSPAN_STREAMING_ENABLED` | `true` | Enable SSE streaming |
| `AGENTSPAN_LIVENESS_ENABLED` | `true` | Enable the stateful-run liveness monitor |
| `AGENTSPAN_LIVENESS_STALL_SECONDS` | `30.0` | Idle window before a run is considered stalled |
| `AGENTSPAN_LIVENESS_CHECK_INTERVAL_SECONDS` | `10.0` | Liveness poll interval |

The model string is `"provider/model"`, e.g. `anthropic/claude-sonnet-4-6`,
`anthropic/claude-sonnet-4-20250514`, `google_gemini/gemini-2.0-flash`. Set the
matching provider API key in the environment of whoever runs the agent's workers.

## What `model` looks like

```python
Agent(name="a", model="openai/gpt-4o")              # OpenAI
Agent(name="b", model="anthropic/claude-sonnet-4-20250514")
Agent(name="c", model="google_gemini/gemini-2.0-flash")
```

## Next

- Add tools, sub-agents, and human-in-the-loop: [Writing agents](writing-agents.md).
- Deploy once and serve workers separately for production: [Advanced](advanced.md).
