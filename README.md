# Python SDK for Conductor

[![CI](https://github.com/conductor-oss/python-sdk/actions/workflows/pull_request.yml/badge.svg)](https://github.com/conductor-oss/python-sdk/actions/workflows/pull_request.yml)
[![PyPI](https://img.shields.io/pypi/v/conductor-python.svg)](https://pypi.org/project/conductor-python/)
[![Python Versions](https://img.shields.io/pypi/pyversions/conductor-python.svg)](https://pypi.org/project/conductor-python/)
[![License](https://img.shields.io/pypi/l/conductor-python.svg)](LICENSE)

The Python SDK for [Conductor](https://www.conductor-oss.org/) lets you build durable Conductor agents, workflows, and workers. Conductor coordinates retries, state, and observability while your Python code runs wherever you deploy it.

**Get involved:** [⭐ Conductor OSS](https://github.com/conductor-oss/conductor) · [Choose a Conductor OSS contribution](https://github.com/conductor-oss/conductor/contribute) · [Contribution guide](https://github.com/conductor-oss/conductor/blob/main/CONTRIBUTING.md)

**Using an AI coding agent?** Load [Conductor Skills](https://github.com/conductor-oss/conductor-skills) so it can create, run, and operate Conductor workflows and Conductor agents:

```shell
npm install -g @conductor-oss/conductor-skills && conductor-skills --all
```

## Choose your path

| I want to… | Start here |
|---|---|
| Build a durable Conductor agent with tools and human approval | [Run an AI agent example](#ai-agent-quickstart) |
| Bring an existing Google ADK, LangChain, LangGraph, OpenAI Agents, or Claude Agent SDK agent | [Use framework bridges](#framework-bridges) |
| Build a durable workflow and Python worker | [Run the core hello-world example](#workflow-and-worker-quickstart) |
| Browse all examples | [AI agent guide](docs/agents/README.md) · [Core examples](docs/examples.md) |
| Navigate the SDK documentation | [Documentation hub](docs/README.md) |

## Choose your Conductor server

Connect to a server before following either quickstart. Use the hosted Developer Edition by default, or run Conductor locally when you need a self-managed development environment.

### Recommended: Orkes Developer Edition

[Orkes Developer Edition](https://developer.orkescloud.com/) is the default hosted option. Create an application and access key in the Developer Edition UI, then configure this SDK with its API endpoint. Keep the key and secret out of source control.

```shell
export CONDUCTOR_SERVER_URL=https://developer.orkescloud.com/api
export CONDUCTOR_AUTH_KEY=<your-key-id>
export CONDUCTOR_AUTH_SECRET=<your-key-secret>
```

For another hosted or self-managed remote cluster, use that cluster's `/api` URL and its application credentials instead. See [server setup](docs/server-setup.md) for details.

### Local alternative: Conductor CLI

The CLI is the preferred local-server path. Install the CLI, start the server, then point the SDK at its API endpoint.

```shell
npm install -g @conductor-oss/conductor-cli
conductor server start
conductor server status
export CONDUCTOR_SERVER_URL=http://localhost:8080/api
```

### Docker fallback

Use Docker when you need a containerized local server instead of the CLI:

```shell
docker run --rm -p 8080:8080 -p 1234:5000 conductoross/conductor:latest
export CONDUCTOR_SERVER_URL=http://localhost:8080/api
```

The Docker server UI is available at [http://localhost:1234](http://localhost:1234). See [server setup](docs/server-setup.md) for full local, remote, and authentication guidance.

## Why Conductor?

- **Survive process failures:** execution state is durable, so Conductor agents and workflows resume from completed work.
- **Build dynamic agent graphs:** define workflow graphs in Python or let an LLM plan them at runtime. Conductor executes plans as durable sub-workflows rather than transient in-process loops.
- **Run tools as distributed tasks:** scale Python workers independently while Conductor manages retries and delivery.
- **Orchestrate long-running work:** combine AI, schedules, events, and human approval without holding application threads open.
- **See every execution:** inspect inputs, outputs, tool calls, retries, and status through one execution model.

See the maintained [planner-context example](examples/agents/115_plan_execute_planner_context.py) for a durable plan-and-execute graph, or start with the [agent examples](examples/agents/README.md).

## Requirements and compatibility

- Python 3.10+
- A running OSS or Orkes Conductor server selected in [Choose your Conductor server](#choose-your-conductor-server)
- Docker when using the Docker local-server option
- Node.js/npm only when using the optional Conductor CLI

The CI workflows are the source of truth for the server versions exercised by this SDK. See the [agent E2E matrix](.github/workflows/agent-e2e.yml) for its pinned server version.

## Install the SDK

```shell
python3 -m venv conductor-env
source conductor-env/bin/activate  # Windows: conductor-env\Scripts\activate
pip install conductor-python
```

### AI agents

Install the complete Conductor agent surface, including supported framework bridges:

```shell
pip install 'conductor-python[agents]'
```

### Workflows and workers

The base package includes the workflow, task, worker, metadata, scheduler, and metrics clients:

```shell
pip install conductor-python
```

### Modules

| Package or extra | Use it for |
|---|---|
| `conductor-python` | Workflow, task, worker, metadata, scheduler, and metrics clients |
| `conductor-python[agents]` | Durable Conductor agents, tools, guardrails, handoffs, and all supported framework bridges |
| `conductor-python[adk]` | Google ADK bridge |
| `conductor-python[langchain]` | LangChain bridge |
| `conductor-python[langgraph]` | LangGraph bridge |
| `conductor-python[openai-agents]` | OpenAI Agents bridge |
| `conductor-python[claude]` | Claude Agent SDK bridge |

## AI agent quickstart

Use this path when your Conductor agent needs LLM reasoning, tools, guardrails, handoffs, or human approval. Select a server above first. For a local server, configure the LLM provider credential in the server environment before starting it. For Developer Edition, configure the provider integration in the hosted cluster. The [agent getting-started guide](docs/agents/getting-started.md) covers both paths.

```shell
export CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini
cd examples/agents
python 01_basic_agent.py
```

Expected outcome: the example prints an `AgentResult` containing the model response. Continue with the [AI agent guide](docs/agents/README.md), [tools guide](docs/agents/concepts/tools.md), and [agent examples](examples/agents/README.md).

### Framework bridges

Keep using the Python agent framework your team already knows. The SDK bridges native [Google ADK](docs/agents/frameworks/google-adk.md), [LangChain](docs/agents/frameworks/langchain.md), [LangGraph](docs/agents/frameworks/langgraph.md), [OpenAI Agents](docs/agents/frameworks/openai.md), and [Claude Agent SDK](docs/agents/frameworks/claude-agent-sdk.md) agents into durable Conductor agents.

## Workflow and worker quickstart

With a server selected above, this maintained example registers a workflow, starts a Python worker, executes the workflow, and prints its result.

```shell
cd examples/helloworld
python helloworld.py
```

Expected outcome: the workflow finishes with `COMPLETED` and prints its greeting output. For worker patterns, workflow definitions, and testing, continue with the [core examples catalog](docs/examples.md), [worker guide](docs/workers.md), and [workflow guide](docs/workflows.md).

## Common tasks

| Need | Start with |
|---|---|
| Build Python Conductor agents | [Agent concepts](docs/agents/concepts/agents.md) |
| Add tools and human approval | [Agent tools](docs/agents/concepts/tools.md) |
| Use another agent framework | [Google ADK](docs/agents/frameworks/google-adk.md) · [LangChain](docs/agents/frameworks/langchain.md) · [LangGraph](docs/agents/frameworks/langgraph.md) · [OpenAI Agents](docs/agents/frameworks/openai.md) |
| Deploy, serve, and run Conductor agents | [Agent runtime modes](docs/agents/concepts/deploy-serve-run.md) |
| Implement and scale Python workers | [Workers guide](docs/workers.md) · [reliability](docs/reliability.md) |
| Define and evolve workflows | [Workflows guide](docs/workflows.md) · [lifecycle/versioning](docs/workflow-lifecycle.md) |
| Upload/download workflow-scoped files | [Python compatibility](docs/compatibility.md#workflow-scoped-files) |
| Test workflows and workers | [Workflow testing](docs/workflow-testing.md) |
| Expose worker metrics | [Observability](docs/observability.md) |
| Host Python workers in an application | [FastAPI worker example](examples/fastapi_worker_service.py) · [deployment/scaling](docs/deployment-scaling.md) |
| Manage schedules and events | [Schedules/events guide](docs/schedules-events.md) |
| Find typed clients and API references | [Core API map](docs/api-map.md) |

## Troubleshooting

| Symptom | Check |
|---|---|
| Connection refused | The server is healthy at `http://localhost:8080/health`; `CONDUCTOR_SERVER_URL` ends in `/api`. |
| Task remains `SCHEDULED` | A worker is polling the exact task type and has enough worker capacity. |
| Authentication failure | `CONDUCTOR_AUTH_KEY` and `CONDUCTOR_AUTH_SECRET` are set for the target server. |
| Conductor agent cannot call a model | The server—not only the Python process—has a configured LLM provider and model. |

## Support and project policies

**Contribute upstream:** [Choose a Conductor OSS contribution](https://github.com/conductor-oss/conductor/contribute) · [Read the Conductor OSS contribution guide](https://github.com/conductor-oss/conductor/blob/main/CONTRIBUTING.md)

- [SDK issues](https://github.com/conductor-oss/python-sdk/issues) for Python SDK bugs and feature requests
- [Conductor server issues](https://github.com/conductor-oss/conductor/issues) for OSS server behavior
- [Conductor Code of Conduct](https://github.com/conductor-oss/conductor/blob/main/CODE_OF_CONDUCT.md) for community expectations and conduct reporting
- [Conductor security policy](https://github.com/conductor-oss/conductor/security/policy) for private vulnerability reporting
- [Conductor Slack](https://join.slack.com/t/orkes-conductor/shared_invite/zt-2vdbx239s-Eacdyqya9giNLHfrCavfaA) and the [Orkes Community Forum](https://community.orkes.io/) for questions

## License

Apache 2.0. See [LICENSE](LICENSE).
