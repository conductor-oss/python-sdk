# Conductor Python SDK

[![CI](https://github.com/conductor-sdk/conductor-python/actions/workflows/pull_request.yml/badge.svg)](https://github.com/conductor-sdk/conductor-python/actions/workflows/pull_request.yml)
[![PyPI](https://img.shields.io/pypi/v/conductor-python.svg)](https://pypi.org/project/conductor-python/)
[![Python Versions](https://img.shields.io/pypi/pyversions/conductor-python.svg)](https://pypi.org/project/conductor-python/)
[![License](https://img.shields.io/pypi/l/conductor-python.svg)](LICENSE)

Python SDK for [Conductor](https://www.conductor-oss.org/) (OSS and Orkes Conductor) — an orchestration platform for building distributed applications, AI agents, and workflow-driven microservices. Define workflows as code, run workers anywhere, and let Conductor handle retries, state management, and observability.

If you find [Conductor](https://github.com/conductor-oss/conductor) useful, please consider giving it a star on GitHub -- it helps the project grow.

[![GitHub stars](https://img.shields.io/github/stars/conductor-oss/conductor.svg?style=social&label=Star&maxAge=)](https://GitHub.com/conductor-oss/conductor/)

## Quick Links

<!-- TOC -->
* [Start  Conductor server](#start--conductor-server)
* [Install the SDK](#install-the-sdk)
* [60-Second Quickstart](#60-second-quickstart)
* [Comprehensive example with sync + async workers, metrics, and long-running tasks](#comprehensive-example-with-sync--async-workers-metrics-and-long-running-tasks)
* [Workers](#workers)
* [Monitoring Workers](#monitoring-workers)
* [Workflows](#workflows)
* [Troubleshooting](#troubleshooting)
* [AI & LLM Workflows](#ai--llm-workflows)
* [Examples](#examples)
* [API Journey Examples](#api-journey-examples)
* [Documentation](#documentation)
* [Support](#support)
* [Frequently Asked Questions](#frequently-asked-questions)
* [License](#license)
<!-- TOC -->


## Start  Conductor server

If you don't already have a Conductor server running, pick one:

**Docker Compose (recommended, includes UI):**

```shell
docker run -p 8080:8080 conductoross/conductor:latest
```
The UI will be available at `http://localhost:8080` and the API at `http://localhost:8080/api`

**MacOS / Linux (one-liner):** (If you don't want to use docker, you can install and run the binary directly)
```shell
curl -sSL https://raw.githubusercontent.com/conductor-oss/conductor/main/conductor_server.sh | sh
```

**Conductor CLI**
```shell
# Installs conductor cli
npm install -g @conductor-oss/conductor-cli

# Start the open source conductor server
conductor server start
# see conductor server --help for all the available commands
```

## Install the SDK

```shell
pip install conductor-python
```

## 60-Second Quickstart

**Step 1: Create a workflow**

Workflows are definitions that reference task types (e.g. a SIMPLE task called `greet`). We'll build a workflow called
`greetings` that runs one task and returns its output.

Assuming you have a `WorkflowExecutor` (`executor`) and a worker task (`greet`):

```python
from conductor.client.workflow.conductor_workflow import ConductorWorkflow

workflow = ConductorWorkflow(name='greetings', version=1, executor=executor)
greet_task = greet(task_ref_name='greet_ref', name=workflow.input('name'))
workflow >> greet_task
workflow.output_parameters({'result': greet_task.output('result')})
workflow.register(overwrite=True)
```

**Step 2: Write worker**

Workers are just Python functions decorated with `@worker_task` that poll Conductor for tasks and execute them.

```python
from conductor.client.worker.worker_task import worker_task

# register_task_def=True is convenient for local dev quickstarts; in production, manage task definitions separately.
@worker_task(task_definition_name='greet', register_task_def=True)
def greet(name: str) -> str:
    return f'Hello {name}'
```

**Step 3: Run your first workflow app**

Create a `quickstart.py` with the following:

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.worker.worker_task import worker_task


# A worker is any Python function.
@worker_task(task_definition_name='greet', register_task_def=True)
def greet(name: str) -> str:
    return f'Hello {name}'


def main():
    # Configure the SDK (reads CONDUCTOR_SERVER_URL / CONDUCTOR_AUTH_* from env).
    config = Configuration()

    clients = OrkesClients(configuration=config)
    executor = clients.get_workflow_executor()

    # Build a workflow with the >> operator.
    workflow = ConductorWorkflow(name='greetings', version=1, executor=executor)
    greet_task = greet(task_ref_name='greet_ref', name=workflow.input('name'))
    workflow >> greet_task
    workflow.output_parameters({'result': greet_task.output('result')})
    workflow.register(overwrite=True)

    # Start polling for tasks (one worker subprocess per worker function).
    with TaskHandler(configuration=config, scan_for_annotated_workers=True) as task_handler:
        task_handler.start_processes()

        # Run the workflow and get the result.
        run = executor.execute(name='greetings', version=1, workflow_input={'name': 'Conductor'})
        print(f'result: {run.output["result"]}')
        print(f'execution: {config.ui_host}/execution/{run.workflow_id}')


if __name__ == '__main__':
    main()
```

Run it:

```shell
python quickstart.py
```

> ### Using Orkes Conductor / Remote Server? 
> Export your authentication credentials as well:
> 
> ```shell
> export CONDUCTOR_SERVER_URL="https://your-cluster.orkesconductor.io/api"
> 
> # If using Orkes Conductor that requires auth key/secret
> export CONDUCTOR_AUTH_KEY="your-key"
> export CONDUCTOR_AUTH_SECRET="your-secret"
> 
> # Optional — set to false to force HTTP/1.1 if your network environment has unstable long-lived HTTP/2 connections (default: true)
> # export CONDUCTOR_HTTP2_ENABLED=false
> ```
> See [Configuration](#configuration) for details.

That's it -- you just defined a worker, built a workflow, and executed it. Open the Conductor UI (default:
[http://localhost:8127](http://localhost:8127)) to see the execution.

## Comprehensive example with sync + async workers, metrics, and long-running tasks

See [examples/workers_e2e.py](examples/workers_e2e.py)

---

## Workers

Workers are Python functions that execute Conductor tasks. Decorate any function with `@worker_task` to:

- register it as a worker (auto-discovered by `TaskHandler`)
- use it as a workflow task (call it with `task_ref_name=...`)

Note: Workers can also be used by LLMs for tool calling (see [AI & LLM Workflows](#ai--llm-workflows)).

```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='greet')
def greet(name: str) -> str:
    return f'Hello {name}'
```

**Async workers** for I/O-bound tasks — the SDK automatically uses `AsyncTaskRunner` (event loop, no thread overhead):

```python
import httpx

@worker_task(task_definition_name='fetch_data')
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()
```

**Start workers** with `TaskHandler`:

Note: `@worker_task` functions are discovered only after their modules are imported. Either import your worker modules
explicitly, or pass `import_modules=[...]` when constructing `TaskHandler`.

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration

api_config = Configuration()
task_handler = TaskHandler(
    workers=[],
    configuration=api_config,
    scan_for_annotated_workers=True,  # auto-discover @worker_task functions
    # monitor_processes=True and restart_on_failure=True by default
)
task_handler.start_processes()
try:
    task_handler.join_processes()  # blocks (workers poll forever)
finally:
    task_handler.stop_processes()
```

Workers support complex inputs (dataclasses), long-running tasks (`TaskInProgress`), and hierarchical configuration via environment variables.

**Resilience: auto-restart and health checks**


Workers are typically long-lived services. By default, `TaskHandler` monitors worker subprocesses and restarts them if
they exit unexpectedly.

For a `/healthcheck` endpoint, you can use:

```python
task_handler.is_healthy()
task_handler.get_worker_process_status()
```

To disable monitoring/restarts (e.g., local debugging):

```python
TaskHandler(..., monitor_processes=False, restart_on_failure=False)
```

**Worker Configuration**

Workers support hierarchical environment variable configuration — global settings that can be overridden per worker:

```shell
# Global (all workers)
export CONDUCTOR_WORKER_ALL_POLL_INTERVAL_MILLIS=250
export CONDUCTOR_WORKER_ALL_THREAD_COUNT=20
export CONDUCTOR_WORKER_ALL_DOMAIN=production

# Per-worker override
export CONDUCTOR_WORKER_GREETINGS_THREAD_COUNT=50
```

See [WORKER_CONFIGURATION.md](WORKER_CONFIGURATION.md) for all options.

## Monitoring Workers

Enable Prometheus metrics:

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings

api_config = Configuration()
metrics_settings = MetricsSettings(directory='/tmp/conductor-metrics', http_port=8000)

task_handler = TaskHandler(configuration=api_config, metrics_settings=metrics_settings, scan_for_annotated_workers=True)
task_handler.start_processes()
# Metrics at http://localhost:8000/metrics
try:
    task_handler.join_processes()  # blocks (workers poll forever)
finally:
    task_handler.stop_processes()
```

See [METRICS.md](METRICS.md) for details.

**Learn more:**
- [Worker Design & Architecture](docs/design/WORKER_DESIGN.md) — AsyncTaskRunner vs TaskRunner, discovery, lifecycle
- [Worker Configuration](WORKER_CONFIGURATION.md) — Environment variable configuration system
- [Complete Worker Guide](docs/WORKER.md) — All worker patterns (function, class, annotation, async)

## Workflows

Define workflows in Python using the `>>` operator to chain tasks:

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow

api_config = Configuration()
clients = OrkesClients(configuration=api_config)
workflow_executor = clients.get_workflow_executor()

workflow = ConductorWorkflow(name='greetings', version=1, executor=workflow_executor)
# Assuming greet is defined (see Workers section above).
workflow >> greet(task_ref_name='greet_ref', name=workflow.input('name'))
# Registering is required if you want to start/execute by name+version; optional if you only execute inline.
workflow.register(overwrite=True)
```

**Execute workflows:**

```python
# Synchronous (waits for completion)
result = workflow_executor.execute(name='greetings', version=1, workflow_input={'name': 'Orkes'})
print(result.output)

# Asynchronous (returns workflow ID immediately)
from conductor.client.http.models import StartWorkflowRequest
request = StartWorkflowRequest(name='greetings', version=1, input={'name': 'Orkes'})
workflow_id = workflow_executor.start_workflow(request)

# Inline (sends the workflow definition with the request; no prior register required)
run = workflow.execute(workflow_input={'name': 'Orkes'}, wait_for_seconds=10)
print(run.output)
```

**Manage running workflows and send signals:**

```python
from conductor.client.orkes_clients import OrkesClients

clients = OrkesClients(configuration=api_config)
workflow_client = clients.get_workflow_client()

workflow_client.pause_workflow(workflow_id)
workflow_client.resume_workflow(workflow_id)
workflow_client.terminate_workflow(workflow_id, reason='no longer needed')
workflow_client.retry_workflow(workflow_id)
workflow_client.restart_workflow(workflow_id)
```

**Learn more:**
- [Workflow Management](docs/WORKFLOW.md) — Start, pause, resume, terminate, retry, search
- [Workflow Testing](docs/WORKFLOW_TESTING.md) — Unit testing with mock task outputs
- [Metadata Management](docs/METADATA.md) — Task & workflow definitions

## Troubleshooting

- Worker stops polling or crashes: `TaskHandler` monitors and restarts worker subprocesses by default. Consider exposing
  a `/healthcheck` endpoint using `task_handler.is_healthy()` + `task_handler.get_worker_process_status()`. If you
  enable metrics, alert on `worker_restart_total`.
- `httpcore.RemoteProtocolError: <ConnectionTerminated ...>`: the SDK recreates the underlying HTTP client and retries
  once for idempotent requests. If your environment is still unstable with HTTP/2, set
  `CONDUCTOR_HTTP2_ENABLED=false` (forces HTTP/1.1) — see `docs/WORKER.md`.
- FastAPI/Uvicorn: avoid running `uvicorn` with multiple web workers unless you explicitly want multiple independent
  `TaskHandler`s polling Conductor (see `examples/fastapi_worker_service.py`).
---
## AI & LLM Workflows

Conductor supports AI-native workflows including agentic tool calling, RAG pipelines, and multi-agent orchestration.

**Agentic Workflows**

Build AI agents where LLMs dynamically select and call Python workers as tools. See [examples/agentic_workflows/](examples/agentic_workflows/) for all examples.

| Example | Description |
|---------|-------------|
| [llm_chat.py](examples/agentic_workflows/llm_chat.py) | Automated multi-turn science Q&A between two LLMs |
| [llm_chat_human_in_loop.py](examples/agentic_workflows/llm_chat_human_in_loop.py) | Interactive chat with WAIT task pauses for user input |
| [multiagent_chat.py](examples/agentic_workflows/multiagent_chat.py) | Multi-agent debate with moderator routing between panelists |
| [function_calling_example.py](examples/agentic_workflows/function_calling_example.py) | LLM picks which Python function to call based on user queries |
| [mcp_weather_agent.py](examples/agentic_workflows/mcp_weather_agent.py) | AI agent using MCP tools for weather queries |

**LLM and RAG Workflows**

| Example | Description |
|---------|-------------|
| [rag_workflow.py](examples/rag_workflow.py) | End-to-end RAG: document conversion (PDF/Word/Excel), pgvector indexing, semantic search, answer generation |
| [vector_db_helloworld.py](examples/orkes/vector_db_helloworld.py) | Vector database operations: text indexing, embedding generation, and semantic search with Pinecone |

```shell
# Automated multi-turn chat
python examples/agentic_workflows/llm_chat.py

# Multi-agent debate
python examples/agentic_workflows/multiagent_chat.py --topic "renewable energy"

# RAG pipeline
pip install "markitdown[pdf]"
python examples/rag_workflow.py document.pdf "What are the key findings?"
```

## Examples

See the [Examples Guide](examples/README.md) for the full catalog. Key examples:

| Example | Description | Run |
|---------|-------------|-----|
| [workers_e2e.py](examples/workers_e2e.py) | End-to-end: sync + async workers, metrics | `python examples/workers_e2e.py` |
| [fastapi_worker_service.py](examples/fastapi_worker_service.py) | FastAPI: expose a workflow as an API (+ workers) (deps: fastapi, uvicorn) | `uvicorn examples.fastapi_worker_service:app --port 8081 --workers 1` |
| [helloworld.py](examples/helloworld/helloworld.py) | Minimal hello world | `python examples/helloworld/helloworld.py` |
| [dynamic_workflow.py](examples/dynamic_workflow.py) | Build workflows programmatically | `python examples/dynamic_workflow.py` |
| [llm_chat.py](examples/agentic_workflows/llm_chat.py) | AI multi-turn chat | `python examples/agentic_workflows/llm_chat.py` |
| [rag_workflow.py](examples/rag_workflow.py) | RAG pipeline (PDF → pgvector → answer) | `python examples/rag_workflow.py file.pdf "question"` |
| [task_context_example.py](examples/task_context_example.py) | Long-running tasks with TaskInProgress | `python examples/task_context_example.py` |
| [workflow_ops.py](examples/workflow_ops.py) | Pause, resume, terminate workflows | `python examples/workflow_ops.py` |
| [test_workflows.py](examples/test_workflows.py) | Unit testing workflows | `python -m unittest examples.test_workflows` |
| [kitchensink.py](examples/kitchensink.py) | All task types (HTTP, JS, JQ, Switch) | `python examples/kitchensink.py` |

## API Journey Examples

End-to-end examples covering all APIs for each domain:

| Example | APIs | Run |
|---------|------|-----|
| [authorization_journey.py](examples/authorization_journey.py) | Authorization APIs | `python examples/authorization_journey.py` |
| [metadata_journey.py](examples/metadata_journey.py) | Metadata APIs | `python examples/metadata_journey.py` |
| [schedule_journey.py](examples/schedule_journey.py) | Schedule APIs | `python examples/schedule_journey.py` |
| [prompt_journey.py](examples/prompt_journey.py) | Prompt APIs | `python examples/prompt_journey.py` |

## Documentation

| Document | Description |
|----------|-------------|
| [Worker Design](docs/design/WORKER_DESIGN.md) | Architecture: AsyncTaskRunner vs TaskRunner, discovery, lifecycle |
| [Worker Guide](docs/WORKER.md) | All worker patterns (function, class, annotation, async) |
| [Worker Configuration](WORKER_CONFIGURATION.md) | Hierarchical environment variable configuration |
| [Workflow Management](docs/WORKFLOW.md) | Start, pause, resume, terminate, retry, search |
| [Workflow Testing](docs/WORKFLOW_TESTING.md) | Unit testing with mock outputs |
| [Task Management](docs/TASK_MANAGEMENT.md) | Task operations |
| [Metadata](docs/METADATA.md) | Task & workflow definitions |
| [Authorization](docs/AUTHORIZATION.md) | Users, groups, applications, permissions |
| [Schedules](docs/SCHEDULE.md) | Workflow scheduling |
| [Secrets](docs/SECRET_MANAGEMENT.md) | Secret storage |
| [Prompts](docs/PROMPT.md) | AI/LLM prompt templates |
| [Integrations](docs/INTEGRATION.md) | AI/LLM provider integrations |
| [Metrics](METRICS.md) | Prometheus metrics collection |
| [Examples](examples/README.md) | Complete examples catalog |

## Support

- [Open an issue (SDK)](https://github.com/conductor-sdk/conductor-python/issues) for SDK bugs, questions, and feature requests
- [Open an issue (Conductor server)](https://github.com/conductor-oss/conductor/issues) for Conductor OSS server issues
- [Join the Conductor Slack](https://join.slack.com/t/orkes-conductor/shared_invite/zt-2vdbx239s-Eacdyqya9giNLHfrCavfaA) for community discussion and help
- [Orkes Community Forum](https://community.orkes.io/) for Q&A

## Frequently Asked Questions

**Is this the same as Netflix Conductor?**

Yes. Conductor OSS is the continuation of the original [Netflix Conductor](https://github.com/Netflix/conductor) repository after Netflix contributed the project to the open-source foundation.

**Is this project actively maintained?**

Yes. [Orkes](https://orkes.io) is the primary maintainer and offers an enterprise SaaS platform for Conductor across all major cloud providers.

**Can Conductor scale to handle my workload?**

Conductor was built at Netflix to handle massive scale and has been battle-tested in production environments processing millions of workflows. It scales horizontally to meet virtually any demand.

**Does Conductor support durable code execution?**

Yes. Conductor ensures workflows complete reliably even in the face of infrastructure failures, process crashes, or network issues.

**Are workflows always asynchronous?**

No. While Conductor excels at asynchronous orchestration, it also supports synchronous workflow execution when immediate results are required.

**Do I need to use a Conductor-specific framework?**

No. Conductor is language and framework agnostic. Use your preferred language and framework -- the [SDKs](https://github.com/conductor-oss/conductor#conductor-sdks) provide native integration for Python, Java, JavaScript, Go, C#, and more.

**Can I mix workers written in different languages?**

Yes. A single workflow can have workers written in Python, Java, Go, or any other supported language. Workers communicate through the Conductor server, not directly with each other.

**What Python versions are supported?**

Python 3.9 and above.

**Should I use `def` or `async def` for my workers?**

Use `async def` for I/O-bound tasks (API calls, database queries) -- the SDK uses `AsyncTaskRunner` with a single event loop for high concurrency with low overhead. Use regular `def` for CPU-bound or blocking work -- the SDK uses `TaskRunner` with a thread pool. The SDK selects the right runner automatically based on your function signature.

**How do I run workers in production?**

Workers are standard Python processes. Deploy them as you would any Python application -- in containers, VMs, or bare metal. Workers poll the Conductor server for tasks, so no inbound ports need to be opened. See [Worker Design](docs/design/WORKER_DESIGN.md) for architecture details.

**How do I test workflows without running a full Conductor server?**

The SDK provides a test framework that uses Conductor's `POST /api/workflow/test` endpoint to evaluate workflows with mock task outputs. See [Workflow Testing](docs/WORKFLOW_TESTING.md) for details.

## License

Apache 2.0
