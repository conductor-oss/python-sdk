# Conductor Python SDK

[![CI Status](https://github.com/conductor-oss/python-sdk/actions/workflows/pull_request.yml/badge.svg)](https://github.com/conductor-oss/python-sdk/actions/workflows/pull_request.yml)

Python SDK for [Conductor](https://www.conductor-oss.org/) — the leading open-source orchestration platform for building distributed applications, AI agents, and workflow-driven microservices. Define workflows as code, run workers anywhere, and let Conductor handle retries, state management, and observability.

If you find [Conductor](https://github.com/conductor-oss/conductor) useful, please consider giving it a star on GitHub -- it helps the project grow.

[![GitHub stars](https://img.shields.io/github/stars/conductor-oss/conductor.svg?style=social&label=Star&maxAge=)](https://GitHub.com/conductor-oss/conductor/)

## 60-Second Quickstart

Install the SDK and create a single file `quickstart.py`:

```shell
pip install conductor-python
```

## Setting Up Conductor

If you don't already have a Conductor server running:

**macOS / Linux:**
```shell
curl -sSL https://raw.githubusercontent.com/conductor-oss/conductor/main/conductor_server.sh | sh
```

**Docker:**
```shell
docker run -p 8080:8080 conductoross/conductor:latest
```
The UI will be available at `http://localhost:8080`.

## Run your first workflow app
```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.worker.worker_task import worker_task


# Step 1: Define a worker — any Python function
@worker_task(task_definition_name='greet')
def greet(name: str) -> str:
    return f'Hello {name}'


def main():
    # Step 2: Configure the SDK (reads CONDUCTOR_SERVER_URL from env)
    config = Configuration()

    # Step 3: Build a workflow with the >> operator
    executor = WorkflowExecutor(configuration=config)
    workflow = ConductorWorkflow(name='greetings', version=1, executor=executor)
    workflow >> greet(task_ref_name='greet_ref', name=workflow.input('name'))
    workflow.register(True)

    # Step 4: Start polling for tasks
    task_handler = TaskHandler(configuration=config)
    task_handler.start_processes()

    # Step 5: Run the workflow and get the result
    result = executor.execute(name='greetings', version=1, workflow_input={'name': 'Conductor'})
    print(f'result: {result.output["result"]}')
    print(f'execution: {config.ui_host}/execution/{result.workflow_id}')

    task_handler.stop_processes()


if __name__ == '__main__':
    main()
```

Run it:

```shell
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
python quickstart.py
```

> **Using Orkes Conductor?** Export your authentication credentials as well:
> ```shell
> export CONDUCTOR_SERVER_URL="https://your-cluster.orkesconductor.io/api"
> export CONDUCTOR_AUTH_KEY="your-key"
> export CONDUCTOR_AUTH_SECRET="your-secret"
> ```
> See [Configuration](#configuration) for details.

That's it -- you just defined a worker, built a workflow, and executed it. Open [http://localhost:8080](http://localhost:8080) to see the execution in the Conductor UI.

### Comprehensive example with sync + async workers, metrics, and long-running tasks 

See [examples/workers_e2e.py](examples/workers_e2e.py)

### Configuration

The SDK reads configuration from environment variables:

```shell
# Required — Conductor server endpoint
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"

# Optional — Authentication (required for Orkes Conductor)
export CONDUCTOR_AUTH_KEY="your-key"
export CONDUCTOR_AUTH_SECRET="your-secret"
```
---

## Workers

Workers are Python functions that execute tasks. Decorate any function with `@worker_task` to make it a distributed worker:
Note: Workers can be used by LLMs for tool calling.

```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='greet')
def greet(name: str) -> str:
    return f'Hello {name}'
```

**Async workers** for I/O-bound tasks — the SDK automatically uses `AsyncTaskRunner` (event loop, no thread overhead):

```python
@worker_task(task_definition_name='fetch_data')
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()
```

**Start workers** with `TaskHandler`:

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration

api_config = Configuration()
task_handler = TaskHandler(
    workers=[],
    configuration=api_config,
    scan_for_annotated_workers=True,
)
task_handler.start_processes()
```

Workers support complex inputs (dataclasses), long-running tasks (`TaskInProgress`), and hierarchical configuration via environment variables.

**Learn more:**
- [Worker Design & Architecture](docs/design/WORKER_DESIGN.md) — AsyncTaskRunner vs TaskRunner, discovery, lifecycle
- [Worker Configuration](WORKER_CONFIGURATION.md) — Environment variable configuration system
- [Complete Worker Guide](docs/WORKER.md) — All worker patterns (function, class, annotation, async)

## Workflows

Define workflows in Python using the `>>` operator to chain tasks:

```python
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor

workflow_executor = WorkflowExecutor(configuration=api_config)
workflow = ConductorWorkflow(name='greetings', version=1, executor=workflow_executor)
workflow >> greet(task_ref_name='greet_ref', name=workflow.input('name'))
workflow.register(True)
```

**Execute workflows:**

```python
# Synchronous (waits for completion)
result = workflow_executor.execute(name='greetings', version=1, workflow_input={'name': 'Orkes'})
print(result.output)

# Asynchronous (returns workflow ID immediately)
from conductor.client.http.models import StartWorkflowRequest
request = StartWorkflowRequest(name='greetings', version=1, input={'name': 'Orkes'})
workflow_id = workflow_client.start_workflow(request)
```

**Manage running workflows:**

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

## Hello World

The complete Hello World example lives in [`examples/helloworld/`](examples/helloworld/):

```shell
python examples/helloworld/helloworld.py
```

It creates a `greetings` workflow with one worker task, runs the worker, executes the workflow, and prints the result. See the [Hello World source](examples/helloworld/helloworld.py) for the full code.

## AI & LLM Workflows

Conductor supports AI-native workflows including agentic tool calling, RAG pipelines, and multi-agent orchestration.

### Agentic Workflows

Build AI agents where LLMs dynamically select and call Python workers as tools. See [examples/agentic_workflows/](examples/agentic_workflows/) for all examples.

| Example | Description |
|---------|-------------|
| [llm_chat.py](examples/agentic_workflows/llm_chat.py) | Automated multi-turn science Q&A between two LLMs |
| [llm_chat_human_in_loop.py](examples/agentic_workflows/llm_chat_human_in_loop.py) | Interactive chat with WAIT task pauses for user input |
| [multiagent_chat.py](examples/agentic_workflows/multiagent_chat.py) | Multi-agent debate with moderator routing between panelists |
| [function_calling_example.py](examples/agentic_workflows/function_calling_example.py) | LLM picks which Python function to call based on user queries |
| [mcp_weather_agent.py](examples/agentic_workflows/mcp_weather_agent.py) | AI agent using MCP tools for weather queries |

### LLM and RAG Workflows

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

### Worker Configuration

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

### Monitoring

Enable Prometheus metrics:

```python
from conductor.client.configuration.settings.metrics_settings import MetricsSettings

metrics_settings = MetricsSettings(directory='/tmp/conductor-metrics', http_port=8000)
task_handler = TaskHandler(configuration=api_config, metrics_settings=metrics_settings, scan_for_annotated_workers=True)
# Metrics at http://localhost:8000/metrics
```

See [METRICS.md](METRICS.md) for details.

## Examples

See the [Examples Guide](examples/README.md) for the full catalog. Key examples:

| Example | Description | Run |
|---------|-------------|-----|
| [workers_e2e.py](examples/workers_e2e.py) | End-to-end: sync + async workers, metrics | `python examples/workers_e2e.py` |
| [helloworld.py](examples/helloworld/helloworld.py) | Minimal hello world | `python examples/helloworld/helloworld.py` |
| [dynamic_workflow.py](examples/dynamic_workflow.py) | Build workflows programmatically | `python examples/dynamic_workflow.py` |
| [llm_chat.py](examples/agentic_workflows/llm_chat.py) | AI multi-turn chat | `python examples/agentic_workflows/llm_chat.py` |
| [rag_workflow.py](examples/rag_workflow.py) | RAG pipeline (PDF → pgvector → answer) | `python examples/rag_workflow.py file.pdf "question"` |
| [task_context_example.py](examples/task_context_example.py) | Long-running tasks with TaskInProgress | `python examples/task_context_example.py` |
| [workflow_ops.py](examples/workflow_ops.py) | Pause, resume, terminate workflows | `python examples/workflow_ops.py` |
| [test_workflows.py](examples/test_workflows.py) | Unit testing workflows | `python -m unittest examples.test_workflows` |
| [kitchensink.py](examples/kitchensink.py) | All task types (HTTP, JS, JQ, Switch) | `python examples/kitchensink.py` |

### API Journey Examples

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

- [Open an issue](https://github.com/conductor-oss/conductor/issues) for bugs, questions, and feature requests
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
