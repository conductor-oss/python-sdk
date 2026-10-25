"""Regression tests for issue #482 — framework agents must route by the
configured model.

The openai-agents ``Agent`` leaves ``model`` unset unless the author sets it.
The framework serialization path previously forwarded that ``None`` to the
server, which then fell back to OpenAI regardless of
``CONDUCTOR_AGENT_LLM_MODEL`` — so an Anthropic-configured run hit OpenAI with
an empty key and silently failed.

These tests exercise the public ``serialize_agent`` contract (which exists on
the original code) so they fail with an assertion before the fix.
"""

import pytest

pytest.importorskip("agents")

from agents import Agent  # noqa: E402

from conductor.ai.agents.frameworks.serializer import serialize_agent  # noqa: E402


def test_unset_agent_model_resolves_from_env(monkeypatch):
    """An openai Agent with no model inherits CONDUCTOR_AGENT_LLM_MODEL."""
    monkeypatch.setenv("CONDUCTOR_AGENT_LLM_MODEL", "anthropic/claude-sonnet-4-6")

    agent = Agent(name="Assistant", instructions="You only respond in haikus.")
    config, _ = serialize_agent(agent)

    assert config["model"] == "anthropic/claude-sonnet-4-6"


def test_unset_agent_model_resolves_bare_env_model(monkeypatch):
    """A bare provider-less env model is qualified with its provider."""
    monkeypatch.setenv("CONDUCTOR_AGENT_LLM_MODEL", "claude-opus-4-6")

    agent = Agent(name="Assistant", instructions="haiku")
    config, _ = serialize_agent(agent)

    assert config["model"] == "anthropic/claude-opus-4-6"


def test_explicit_agent_model_is_preserved(monkeypatch):
    """An explicitly declared model wins over the configured default."""
    monkeypatch.setenv("CONDUCTOR_AGENT_LLM_MODEL", "anthropic/claude-sonnet-4-6")

    agent = Agent(name="Assistant", instructions="haiku", model="gpt-4o")
    config, _ = serialize_agent(agent)

    assert config["model"] == "gpt-4o"


def test_no_env_and_no_model_stays_unset(monkeypatch):
    """Without a configured default the model is left untouched."""
    monkeypatch.delenv("CONDUCTOR_AGENT_LLM_MODEL", raising=False)

    agent = Agent(name="Assistant", instructions="haiku")
    config, _ = serialize_agent(agent)

    assert not config.get("model")
