# Conductor Python SDK Examples

Quick reference for example files demonstrating SDK features.

## 🚀 Quick Start

```bash
# Install
pip install conductor-python httpx

# Configure
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"

# Run end-to-end example
python examples/workers_e2e.py
```

---

## 📁 Examples by Category

### Core Workers

| File | Description | Run |
|------|-------------|-----|
| **workers_e2e.py** | ⭐ Start here - sync + async workers | `python examples/workers_e2e.py` |
| **worker_example.py** | Comprehensive patterns (None returns, TaskInProgress) | `python examples/worker_example.py` |
| **fastapi_worker_service.py** | FastAPI exposing a workflow as an API (+ workers) | `uvicorn examples.fastapi_worker_service:app --port 8081 --workers 1` |
| **worker_configuration_example.py** | Hierarchical configuration (env vars) | `python examples/worker_configuration_example.py` |
| **task_context_example.py** | Task context (logs, poll_count, task_id) | `python examples/task_context_example.py` |
| **task_workers.py** | Task worker patterns with dataclasses | `python examples/task_workers.py` |
| **pythonic_usage.py** | Pythonic API patterns and decorators | `python examples/pythonic_usage.py` |

**Key Concepts:**
- `def` → TaskRunner (ThreadPoolExecutor)
- `async def` → AsyncTaskRunner (pure async/await, single event loop)
- One process per worker (automatic selection)

### Long-Running Tasks

```python
from conductor.client.context.task_context import TaskInProgress
from typing import Union

@worker_task(task_definition_name='batch_job')
def process_batch(batch_id: str) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()

    if ctx.get_poll_count() < 5:
        # More work - extend lease
        return TaskInProgress(callback_after_seconds=30)

    return {'status': 'completed'}
```

See: `task_context_example.py`, `worker_example.py`

---

### Workflows

| File | Description | Run |
|------|-------------|-----|
| **dynamic_workflow.py** | Create workflows programmatically | `python examples/dynamic_workflow.py` |
| **workflow_ops.py** | Start, pause, resume, terminate workflows | `python examples/workflow_ops.py` |
| **workflow_status_listner.py** | Workflow event listeners | `python examples/workflow_status_listner.py` |
| **test_workflows.py** | Unit testing workflows | `python -m unittest examples.test_workflows` |

---

### AI/LLM Workflows

See [agentic_workflows/](agentic_workflows/) for the full set of AI agent examples.

| File | Description | Run |
|------|-------------|-----|
| **agentic_workflows/llm_chat.py** | Automated multi-turn LLM chat | `python examples/agentic_workflows/llm_chat.py` |
| **agentic_workflows/llm_chat_human_in_loop.py** | Interactive chat with WAIT task pauses | `python examples/agentic_workflows/llm_chat_human_in_loop.py` |
| **agentic_workflows/multiagent_chat.py** | Multi-agent debate with moderator routing | `python examples/agentic_workflows/multiagent_chat.py` |
| **agentic_workflows/function_calling_example.py** | LLM picks Python functions to call | `python examples/agentic_workflows/function_calling_example.py` |
| **agentic_workflows/mcp_weather_agent.py** | AI agent with MCP tool calling | `python examples/agentic_workflows/mcp_weather_agent.py "What's the weather?"` |
| **rag_workflow.py** | RAG pipeline: markitdown, pgvector, search, answer | `python examples/rag_workflow.py file.pdf "question"` |

---

### AI Agents

Durable agent authoring (`Agent`, `AgentRuntime`, tools, guardrails, handoffs, multi-agent
strategies) — a separate, more extensive catalog of 270+ examples, requiring
`pip install 'conductor-python[agents]'`. See [agents/README.md](agents/README.md).

---

### Monitoring

| File | Description | Run |
|------|-------------|-----|
| **metrics_example.py** | Prometheus metrics (HTTP server on :8000) | `python examples/metrics_example.py` |
| **event_listener_examples.py** | Custom event listeners (SLA, logging) | `python examples/event_listener_examples.py` |
| **task_listener_example.py** | Task lifecycle listeners | `python examples/task_listener_example.py` |

Access metrics: `curl http://localhost:8000/metrics`

---

### Advanced

| File | Description | Notes |
|------|-------------|-------|
| **task_configure.py** | Task definitions (retry, timeout, rate limits) | Programmatic task config |
| **kitchensink.py** | All task types (HTTP, JS, JQ, Switch) | Comprehensive |
| **shell_worker.py** | Execute shell commands | ⚠️ Educational only |
| **untrusted_host.py** | Self-signed SSL certificates | ⚠️ Dev/test only |

---

## 🎯 API Journey Examples

Complete working examples demonstrating 100% API coverage for major SDK features.

### Authorization & RBAC

| File | Description | APIs |
|------|-------------|------|
| **authorization_journey.py** | Complete RBAC implementation | 49 APIs |

**Scenario:** E-commerce platform with departments, teams, and role-based access control.

**Features:**
- User, group, and application management
- Custom roles with fine-grained permissions
- Resource access control and audit trails
- Automatic cleanup (use `--no-cleanup` to keep resources)

```bash
python examples/authorization_journey.py
```

---

### Schedule Management

| File | Description | APIs |
|------|-------------|------|
| **schedule_journey.py** | Complete scheduling system | 15 APIs |

**Scenario:** E-commerce order processing with scheduled batch workflows.

**Features:**
- Schedule CRUD operations
- Cron expressions with timezone support
- Pause/resume schedules
- Execution history and monitoring

```bash
python examples/schedule_journey.py
```

---

### Metadata Management

| File | Description | APIs |
|------|-------------|------|
| **metadata_journey.py** | Workflow & task definitions | 21 APIs |

**Scenario:** Online education platform with complex workflow orchestration.

**Features:**
- Task and workflow definition management
- Version control and tagging
- Rate limiting and monitoring
- Complex workflow patterns (SWITCH, FORK_JOIN, DECISION)

```bash
python examples/metadata_journey.py
```

---

### Prompt Management

| File | Description | APIs |
|------|-------------|------|
| **prompt_journey.py** | AI/LLM prompt templates | 8 APIs |

**Scenario:** AI-powered customer service with managed prompt templates.

**Features:**
- Prompt template CRUD operations
- Multi-language support
- Testing with AI models
- Version management and tagging

```bash
python examples/prompt_journey.py
```

---

### RAG Pipeline Setup

Complete RAG (Retrieval Augmented Generation) pipeline example:

```bash
# 1. Install dependencies
pip install conductor-python "markitdown[pdf]"

# 2. Configure (requires Orkes Conductor with AI/LLM support)
#    - Vector DB integration named "postgres-prod" (pgvector)
#    - LLM provider named "openai" with a valid API key
export CONDUCTOR_SERVER_URL="http://localhost:7001/api"

# 3. Run RAG workflow
python examples/rag_workflow.py examples/goog-20251231.pdf "What were Google's total revenues?"
```

**Pipeline:** `convert_to_markdown` → `LLM_INDEX_TEXT` → `WAIT` → `LLM_SEARCH_INDEX` → `LLM_CHAT_COMPLETE`

**Features:**
- Document conversion (PDF, Word, Excel → Markdown via [markitdown](https://github.com/microsoft/markitdown))
- Vector database ingestion into pgvector with OpenAI `text-embedding-3-small` embeddings
- Semantic search with configurable result count
- Context-aware answer generation with `gpt-4o-mini`

---

### MCP Tool Integration Setup

MCP (Model Context Protocol) agent example:

```bash
# 1. Install MCP weather server
pip install mcp-weather-server

# 2. Start MCP server
python3 -m mcp_weather_server \
  --mode streamable-http \
  --host localhost \
  --port 3001 \
  --stateless

# 3. Run AI agent
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
python examples/agentic_workflows/mcp_weather_agent.py "What's the weather in Tokyo?"

# Or simple mode (direct tool call):
python examples/agentic_workflows/mcp_weather_agent.py "Temperature in New York" --simple
```

**Features:**
- MCP tool discovery
- LLM-based planning (agent decides which tool to use)
- Tool execution via HTTP/Streamable transport
- Natural language response generation

---

## 🎓 Learning Path (60-Second Guide)

```bash
# 1. Basic workers (5 min)
python examples/workers_e2e.py

# 2. Long-running tasks (5 min)
python examples/task_context_example.py

# 3. Configuration (5 min)
python examples/worker_configuration_example.py

# 4. Workflows (10 min)
python examples/dynamic_workflow.py

# 5. AI/LLM Workflows (15 min)
python examples/agentic_workflows/llm_chat.py
python examples/rag_workflow.py examples/goog-20251231.pdf "What were Google's total revenues?"

# 6. Monitoring (5 min)
python examples/metrics_example.py
curl http://localhost:8000/metrics
```

---

## 📦 Package Structure

```
examples/
├── Core Workers
│   ├── workers_e2e.py                  # ⭐ Start here
│   ├── worker_example.py               # Comprehensive patterns
│   ├── worker_configuration_example.py # Env var configuration
│   ├── task_context_example.py         # Long-running tasks
│   ├── task_workers.py                 # Dataclass patterns
│   └── pythonic_usage.py               # Pythonic decorators
│
├── Workflows
│   ├── dynamic_workflow.py             # Workflow creation
│   ├── workflow_ops.py                 # Workflow management
│   ├── workflow_status_listner.py      # Workflow events
│   └── test_workflows.py               # Unit tests
│
├── AI/LLM Workflows
│   ├── rag_workflow.py                 # RAG pipeline (markitdown + pgvector)
│   └── agentic_workflows/             # Agentic AI examples
│       ├── llm_chat.py                # Multi-turn LLM chat
│       ├── llm_chat_human_in_loop.py  # Interactive chat with WAIT
│       ├── multiagent_chat.py         # Multi-agent debate
│       ├── function_calling_example.py # LLM function calling
│       └── mcp_weather_agent.py       # MCP tool calling agent
│
├── Monitoring
│   ├── metrics_example.py              # Prometheus metrics
│   ├── event_listener_examples.py      # Custom listeners
│   └── task_listener_example.py        # Task events
│
├── Advanced
│   ├── task_configure.py               # Task definitions
│   ├── kitchensink.py                  # All features
│   ├── shell_worker.py                 # Shell commands
│   └── untrusted_host.py               # SSL handling
│
├── API Journeys
│   ├── authorization_journey.py        # ⭐ All 49 authorization APIs
│   ├── schedule_journey.py             # ⭐ All 15 schedule APIs
│   ├── metadata_journey.py             # ⭐ All 21 metadata APIs
│   └── prompt_journey.py               # ⭐ All 8 prompt APIs
│
├── helloworld/                         # Simple examples
│   ├── greetings_worker.py
│   ├── greetings_workflow.py
│   └── helloworld.py
│
├── user_example/                       # HTTP + dataclass
│   ├── models.py
│   └── user_workers.py
│
├── worker_discovery/                   # Auto-discovery
│   ├── my_workers/
│   └── other_workers/
│
└── orkes/                             # Orkes-specific features
    ├── vector_db_helloworld.py        # Vector DB operations
    ├── agentic_workflow.py            # AI agent (AIOrchestrator)
    ├── http_poll.py
    ├── sync_updates.py
    └── wait_for_webhook.py
```

---

## 🔧 Configuration

### Worker Architecture

**Multiprocess** - one process per worker with automatic runner selection:

```python
# Sync worker → TaskRunner (ThreadPoolExecutor)
@worker_task(task_definition_name='cpu_task', thread_count=4)
def cpu_task(data: dict):
    return expensive_computation(data)

# Async worker → AsyncTaskRunner (event loop, 67% less memory)
@worker_task(task_definition_name='api_task', thread_count=50)
async def api_task(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```

### Environment Variables

```bash
# Required
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"

# Optional - Orkes Cloud
export CONDUCTOR_AUTH_KEY="your-key"
export CONDUCTOR_AUTH_SECRET="your-secret"

# Optional - Worker config
export conductor.worker.all.domain=production
export conductor.worker.all.poll_interval_millis=250
export conductor.worker.all.thread_count=20
```

---

## 🐛 Common Issues

**Workers not polling?**
- Check task names match between workflow and `@worker_task`
- Verify `CONDUCTOR_SERVER_URL` is correct
- Check auth credentials

**Async workers using threads?**
- Use `async def` (not `def`)
- Check logs for "Created AsyncTaskRunner"

**High memory?**
- Use `async def` for I/O tasks (lower memory)
- Reduce worker count or thread_count

---

## 📚 Documentation

### API References
- [Authorization API](../docs/AUTHORIZATION.md) - Complete RBAC system (49 APIs)
- [Metadata API](../docs/METADATA.md) - Task & workflow definitions (21 APIs)
- [Prompt API](../docs/PROMPT.md) - AI/LLM prompt templates (8 APIs)
- [Schedule API](../docs/SCHEDULE.md) - Workflow scheduling (15 APIs)
- [Task Management API](../docs/TASK_MANAGEMENT.md) - Task operations (11 APIs)
- [Workflow API](../docs/WORKFLOW.md) - Workflow operations
- [Integration API](../docs/INTEGRATION.md) - AI/LLM provider integrations
- [AI Agents](../docs/agents/README.md) - Durable agent authoring: `Agent`, `AgentRuntime`, tools, guardrails, handoffs

### Design Documents
- [Worker Design](../docs/design/WORKER_DESIGN.md) - Complete architecture guide
- [Worker Configuration](../WORKER_CONFIGURATION.md) - Hierarchical config system

### Main Documentation
- [Python SDK README](../README.md) - SDK overview and installation

---

**Repository**: https://github.com/conductor-oss/conductor-python
**License**: Apache 2.0
