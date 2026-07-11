# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Agentspan Agents SDK — durable, scalable, observable AI agents.

This is the public API surface.  Import everything you need from here::

    from conductor.ai.agents import Agent, AgentRuntime, tool

Quick start::

    from conductor.ai.agents import Agent, AgentRuntime, tool

    @tool
    def get_weather(city: str) -> str:
        \"\"\"Get current weather for a city.\"\"\"
        return f"72F and sunny in {city}"

    agent = Agent(name="weatherbot", model="openai/gpt-4o", tools=[get_weather])

    with AgentRuntime() as runtime:
        result = runtime.run(agent, "What's the weather in NYC?")
        print(result.output)
"""

from __future__ import annotations

# Core primitive
from conductor.ai.agents.agent import (
    Agent,
    AgentDef,
    ConfigurationError,
    PromptTemplate,
    Strategy,
    agent,
    scatter_gather,
)

# Callback handlers
from conductor.ai.agents.callback import CallbackHandler

# Claude Code configuration
from conductor.ai.agents.claude_code import ClaudeCode
from conductor.ai.agents.cli_config import CliConfig, TerminalToolError

# Code execution
from conductor.ai.agents.code_execution_config import CodeExecutionConfig
from conductor.ai.agents.code_executor import (
    CodeExecutor,
    DockerCodeExecutor,
    ExecutionResult,
    JupyterCodeExecutor,
    LocalCodeExecutor,
    ServerlessCodeExecutor,
)

# Exceptions
from conductor.ai.agents.exceptions import AgentAPIError, AgentNotFoundError, AgentspanError

# Extended agent types
from conductor.ai.agents.ext import GPTAssistantAgent

# Guardrails
from conductor.ai.agents.guardrail import (
    Guardrail,
    GuardrailDef,
    GuardrailResult,
    LLMGuardrail,
    OnFail,
    Position,
    RegexGuardrail,
    guardrail,
)

# Handoff conditions (for swarm strategy)
from conductor.ai.agents.handoff import HandoffCondition, OnCondition, OnTextMention, OnToolResult

# Memory
from conductor.ai.agents.memory import ConversationMemory

# Typed plan builders + convenience constructor (Strategy.PLAN_EXECUTE)
from conductor.ai.agents.plans import (
    Action,
    Context,
    Generate,
    Op,
    Plan,
    Ref,
    Step,
    Validation,
    coerce_plan,
    plan_execute,
)

# Result types
from conductor.ai.agents.result import (
    AgentEvent,
    AgentHandle,
    AgentResult,
    AgentStatus,
    AgentStream,
    AsyncAgentStream,
    DeploymentInfo,
    EventType,
    FinishReason,
    Status,
    TokenUsage,
)

# Execution API
from conductor.ai.agents.run import (
    configure,
    deploy,
    deploy_async,
    plan,
    resume,
    resume_async,
    run,
    run_async,
    serve,
    shutdown,
    start,
    start_async,
    stream,
    stream_async,
)

# Runtime (for context manager and advanced usage)
from conductor.ai.agents.runtime.config import AgentConfig

# Credential management
from conductor.ai.agents.runtime.credentials.accessor import get_secret
from conductor.ai.agents.runtime.credentials.types import (
    CredentialAuthError,
    CredentialNotFoundError,
    CredentialRateLimitError,
    CredentialServiceError,
)

# Skills
from conductor.ai.agents.skill import (
    SkillLoadError,
    format_prompt_with_params,
    format_skill_params,
    load_skills,
    skill,
)


def resolve_credentials(task: object, names: list) -> dict:
    """Resolve declared credentials for an external (non-``@tool``) worker.

    Secured hosts resolve a worker's declared ``TaskDef.runtimeMetadata`` secret
    names at poll time and deliver the values on the wire-only
    ``Task.runtimeMetadata`` (conductor-oss PR #1255). This reads those values off
    the polled ``task`` — there is no separate fetch call or execution token.

    Args:
        task: The Conductor ``Task`` object delivered to the worker.
        names: Credential names to resolve (must be declared on the tool/agent so
            the server resolves them).

    Returns:
        Dict mapping credential name to resolved plaintext value.

    Raises:
        CredentialNotFoundError: If any declared name was not delivered by the host.
    """
    from conductor.ai.agents.runtime._dispatch import _resolve_secrets_from_task

    return _resolve_secrets_from_task(task, names)


# Agent discovery
# OCG (Open Context Graph) retrieval sub-agent
from conductor.ai.agents.ocg import OCG_SYSTEM_PROMPT, ocg_agent, ocg_tools

# OpenAI Agents SDK compatibility
from conductor.ai.agents.openai_compat import Runner, RunResult
from conductor.ai.agents.runtime.discovery import discover_agents

# MCP discovery utilities
from conductor.ai.agents.runtime.mcp_discovery import clear_discovery_cache
from conductor.ai.agents.runtime.runtime import VALID_RETRY_POLICIES, AgentRuntime
from conductor.ai.agents.schedule import (
    InvalidCronExpression,
    Schedule,
    ScheduleError,
    ScheduleInfo,
    ScheduleNameConflict,
    ScheduleNotFound,
    schedules,
)
from conductor.ai.agents.semantic_memory import MemoryEntry, MemoryStore, SemanticMemory

# Termination conditions
from conductor.ai.agents.termination import (
    MaxMessageTermination,
    StopMessageTermination,
    TerminationCondition,
    TerminationResult,
    TextMentionTermination,
    TokenUsageTermination,
)

# Tool decorator and constructors
from conductor.ai.agents.tool import (
    PrefillToolCall,
    ToolContext,
    ToolDef,
    agent_tool,
    api_tool,
    audio_tool,
    http_tool,
    human_tool,
    image_tool,
    index_tool,
    mcp_tool,
    pdf_tool,
    search_tool,
    tool,
    video_tool,
    wait_for_message_tool,
)

# openai-agents name alias — ``from conductor.ai.agents import function_tool``
function_tool = tool

# Tracing (optional — only activates if opentelemetry is installed)
from conductor.ai.agents.tracing import is_tracing_enabled

__all__ = [
    # OpenAI Agents SDK compatibility
    "Runner",
    "RunResult",
    "function_tool",
    # Core
    "Agent",
    "AgentDef",
    "ClaudeCode",
    "PromptTemplate",
    "Strategy",
    "agent",
    "scatter_gather",
    "AgentRuntime",
    "VALID_RETRY_POLICIES",
    "AgentConfig",
    # Extended agent types
    "GPTAssistantAgent",
    # Tools
    "tool",
    "ToolDef",
    "ToolContext",
    "agent_tool",
    "api_tool",
    "http_tool",
    # OCG retrieval sub-agent
    "OCG_SYSTEM_PROMPT",
    "ocg_agent",
    "ocg_tools",
    "human_tool",
    "mcp_tool",
    "wait_for_message_tool",
    "image_tool",
    "audio_tool",
    "video_tool",
    "pdf_tool",
    "index_tool",
    "search_tool",
    "clear_discovery_cache",
    # Convenience execution (uses a singleton AgentRuntime)
    "configure",
    "deploy",
    "deploy_async",
    "plan",
    "resume",
    "resume_async",
    "run",
    "run_async",
    "serve",
    "shutdown",
    "start",
    "start_async",
    "stream",
    "stream_async",
    # Results
    "AgentResult",
    "DeploymentInfo",
    "AgentHandle",
    "AgentStatus",
    "AgentStream",
    "AsyncAgentStream",
    "AgentEvent",
    "EventType",
    "FinishReason",
    "Status",
    "TokenUsage",
    # Guardrails
    "guardrail",
    "Guardrail",
    "GuardrailDef",
    "GuardrailResult",
    "OnFail",
    "Position",
    "RegexGuardrail",
    "LLMGuardrail",
    # Termination conditions
    "TerminationCondition",
    "TerminationResult",
    "TextMentionTermination",
    "StopMessageTermination",
    "MaxMessageTermination",
    "TokenUsageTermination",
    # Scheduling
    "Schedule",
    "ScheduleInfo",
    "ScheduleError",
    "ScheduleNameConflict",
    "ScheduleNotFound",
    "InvalidCronExpression",
    "schedules",
    # Memory
    "ConversationMemory",
    "SemanticMemory",
    "MemoryStore",
    "MemoryEntry",
    # Code execution
    "CodeExecutionConfig",
    "CliConfig",
    "TerminalToolError",
    "CodeExecutor",
    "LocalCodeExecutor",
    "DockerCodeExecutor",
    "JupyterCodeExecutor",
    "ServerlessCodeExecutor",
    "ExecutionResult",
    # Callback handlers
    "CallbackHandler",
    # Handoff conditions
    "HandoffCondition",
    "OnToolResult",
    "OnTextMention",
    "OnCondition",
    # Exceptions
    "AgentspanError",
    "AgentAPIError",
    "AgentNotFoundError",
    # Agent discovery
    "discover_agents",
    # Tracing
    "is_tracing_enabled",
    # Credentials
    "get_secret",
    "resolve_credentials",
    "CredentialNotFoundError",
    "CredentialAuthError",
    "CredentialRateLimitError",
    "CredentialServiceError",
    # Configuration errors
    "ConfigurationError",
    # Skills
    "skill",
    "load_skills",
    "SkillLoadError",
]
