# Agentic Workflow Examples

AI workflow examples using Conductor's built-in system tasks, with Python workers where needed.

Chat examples use inline ChatMessage objects for system prompts. No named prompt templates or AIOrchestrator required.

## Prerequisites

The AI decision example requires server-side `AI_DECISION` support and Jev credentials. It needs no chat model or Python worker. The other examples require:

- Conductor server with AI/LLM support running (e.g., `http://localhost:7001/api`)
- LLM provider named `openai` configured with a valid API key
- `export CONDUCTOR_SERVER_URL=http://localhost:7001/api`

## Examples

| Example | Description | Interactive? | Pattern |
|---------|-------------|:------------:|---------|
| [ai_decision_routing.py](ai_decision_routing.py) | Route requests to billing or technical support | No | AI_DECISION + SwitchTask + SetVariableTask |
| [llm_chat.py](llm_chat.py) | Automated multi-turn science Q&A between two LLMs | No | LoopTask + LLM_CHAT_COMPLETE + worker for history |
| [llm_chat_human_in_loop.py](llm_chat_human_in_loop.py) | Interactive chat with WAIT task pauses for user input | Yes | LoopTask + WaitTask + LLM_CHAT_COMPLETE |
| [multiagent_chat.py](multiagent_chat.py) | Multi-agent debate with moderator routing between panelists | No | LoopTask + SwitchTask + SetVariableTask + JavaScript routing |
| [function_calling_example.py](function_calling_example.py) | LLM picks which Python function to call based on user query | Yes | LoopTask + WaitTask + LLM_CHAT_COMPLETE (json_output) + dispatch worker |
| [mcp_weather_agent.py](mcp_weather_agent.py) | AI agent using MCP tools to answer weather questions | No | ListMcpTools + CallMcpTool + LLM_CHAT_COMPLETE |

## Quick Start

```bash
# Jev request routing with server-managed credentials
CONDUCTOR_SERVER_URL=http://localhost:8080/api python -m examples.agentic_workflows.ai_decision_routing

# Automated multi-turn chat (no interaction needed)
python examples/agentic_workflows/llm_chat.py

# Multi-agent debate
python examples/agentic_workflows/multiagent_chat.py --topic "renewable energy"

# Interactive chat
python examples/agentic_workflows/llm_chat_human_in_loop.py

# Function calling agent
python examples/agentic_workflows/function_calling_example.py
```

## Key Patterns

### Passing dynamic messages to LLM_CHAT_COMPLETE

When passing a workflow reference as `messages`, set it via `input_parameters` AFTER construction:

```python
chat = LlmChatComplete(task_ref_name="ref", llm_provider="openai", model="gpt-4o-mini")
chat.input_parameters["messages"] = "${some_task.output.result}"  # CORRECT
```

Do NOT pass a string reference to the constructor `messages=` parameter -- it iterates the string as a list of characters.

### Worker parameter type annotations

Use `object` or `dict` for parameters that receive dynamic data from workflow references (lists, dicts, etc.). Avoid `List[dict]` -- it triggers conversion bugs in the worker framework on Python 3.12+.

### Single-parameter workers with `object` annotation

If a worker has exactly one parameter annotated as `object`, the framework treats it as a raw Task handler. Use `dict` instead, or add a second parameter.
