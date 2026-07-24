# OpenAI Agents SDK compatibility — ``from conductor.ai import Runner``
from conductor.ai.agents.openai_compat import Runner, RunResult
from conductor.ai.agents.tool import tool as function_tool

__all__ = ["Runner", "RunResult", "function_tool"]
