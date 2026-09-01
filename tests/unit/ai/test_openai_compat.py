"""Regression tests for the OpenAI Agents compatibility Runner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

agents = pytest.importorskip("agents")
Agent = agents.Agent
function_tool = agents.function_tool

from conductor.ai.agents import Agent as ConductorAgent  # noqa: E402
from conductor.ai.agents.openai_compat import Runner, _run_agent  # noqa: E402


def test_runner_converts_openai_agent_for_non_openai_model(monkeypatch):
    """A configured non-OpenAI model must use Conductor's native path."""
    monkeypatch.setenv("CONDUCTOR_AGENT_LLM_MODEL", "anthropic/claude-sonnet-4-6")
    agent = Agent(name="assistant", instructions="Be helpful.")
    fake_result = MagicMock(output={"result": "ok"}, execution_id="execution-1")

    with patch("conductor.ai.agents.run.run", return_value=fake_result) as run:
        result = Runner.run_sync(agent, "Hello")

    resolved_agent = run.call_args.args[0]
    default_max_turns = Runner.run_sync.__kwdefaults__["max_turns"]
    assert isinstance(resolved_agent, ConductorAgent)
    assert resolved_agent.model == "anthropic/claude-sonnet-4-6"
    assert resolved_agent.max_turns == default_max_turns
    assert result.final_output == "ok"


def test_runner_keeps_openai_agent_for_openai_model(monkeypatch):
    """The existing OpenAI framework path remains unchanged for OpenAI models."""
    monkeypatch.setenv("CONDUCTOR_AGENT_LLM_MODEL", "openai/gpt-4o")
    agent = Agent(name="assistant", instructions="Be helpful.")

    assert _run_agent(agent, max_turns=10) is agent


def test_runner_preserves_openai_function_tools_when_converting(monkeypatch):
    """Converting for another provider must not discard OpenAI function tools."""

    @function_tool
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello, {name}!"

    monkeypatch.setenv("CONDUCTOR_AGENT_LLM_MODEL", "anthropic/claude-sonnet-4-6")
    agent = Agent(name="assistant", instructions="Be helpful.", tools=[greet])

    resolved_agent = _run_agent(agent, max_turns=10)

    assert len(resolved_agent.tools) == 1
    assert resolved_agent.tools[0].name == "greet"
    assert resolved_agent.tools[0].func(name="Ada") == "Hello, Ada!"
