"""Tests for declarative OCG configuration."""

import pytest

from conductor.ai.agents import Agent, OcgConfig
from conductor.ai.agents.config_serializer import AgentConfigSerializer


def serialize(agent: Agent) -> dict:
    return AgentConfigSerializer().serialize(agent)


def test_ocg_absent_omits_long_term_memory():
    config = serialize(Agent(name="assistant", model="openai/gpt-4o"))

    assert "longTermMemory" not in config


def test_ocg_uses_default_credential_and_generated_agent_identity():
    config = serialize(
        Agent(
            name="assistant",
            model="openai/gpt-4o",
            ocg=OcgConfig(url="https://ocg.example.com"),
        )
    )

    assert config["longTermMemory"] == {
        "ocgUrl": "https://ocg.example.com",
        "credential": "OCG_PUBLIC_KEY",
        "agent": "conductor-agent:assistant",
    }


def test_ocg_serializes_explicit_credential_and_user():
    config = serialize(
        Agent(
            name="assistant",
            model="openai/gpt-4o",
            ocg=OcgConfig(
                url="https://ocg.example.com",
                credential="ASSISTANT_OCG_KEY",
                user="user:123",
            ),
        )
    )

    assert config["longTermMemory"] == {
        "ocgUrl": "https://ocg.example.com",
        "credential": "ASSISTANT_OCG_KEY",
        "agent": "conductor-agent:assistant",
        "user": "user:123",
    }


@pytest.mark.parametrize(
    ("raw_url", "normalized_url"),
    [
        (" https://ocg.example.com/ ", "https://ocg.example.com"),
        ("https://ocg.example.com///", "https://ocg.example.com"),
    ],
)
def test_ocg_normalizes_url(raw_url, normalized_url):
    ocg = OcgConfig(url=raw_url)

    assert ocg.url == normalized_url


@pytest.mark.parametrize("url", ["", "   ", "///"])
def test_ocg_rejects_empty_url(url):
    with pytest.raises(ValueError, match="url must be non-empty"):
        OcgConfig(url=url)


@pytest.mark.parametrize("credential", ["", "   "])
def test_ocg_rejects_empty_credential(credential):
    with pytest.raises(ValueError, match="credential must be a non-empty secret name"):
        OcgConfig(url="https://ocg.example.com", credential=credential)


def test_ocg_does_not_accept_raw_api_key_parameter():
    with pytest.raises(TypeError):
        OcgConfig(url="https://ocg.example.com", api_key="raw-secret")


def test_ocg_emits_no_legacy_feedback_worker_or_config():
    config = serialize(
        Agent(
            name="assistant",
            model="openai/gpt-4o",
            ocg=OcgConfig(url="https://ocg.example.com"),
        )
    )

    assert "feedbackSink" not in config
    assert "feedbackWorker" not in config
    assert "memorySummaryModel" not in config["longTermMemory"]
    assert "tools" not in config
