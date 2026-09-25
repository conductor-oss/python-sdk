"""Keep the documented agent wire contract aligned with the serializer."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from conductor.ai.agents.agent import Agent
from conductor.ai.agents.config_serializer import AgentConfigSerializer
from conductor.ai.agents.guardrail import RegexGuardrail
from conductor.ai.agents.termination import TextMentionTermination
from conductor.ai.agents.tool import tool


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "docs" / "agents" / "reference" / "agent-schema.json"


@tool
def _schema_tool(query: str) -> dict:
    """Return a deterministic result for schema validation."""
    return {"query": query}


def test_agent_schema_is_valid_and_accepts_representative_serializer_output():
    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    agent = Agent(
        name="schema_root",
        model="openai/gpt-4o-mini",
        instructions="Return a concise answer.",
        tools=[_schema_tool],
        agents=[Agent(name="schema_child", model="openai/gpt-4o-mini")],
        strategy="handoff",
        guardrails=[RegexGuardrail(name="safe", patterns=[".*"])],
        termination=TextMentionTermination(text="DONE"),
        metadata={"owner": "docs"},
        max_tokens=100,
        temperature=0.1,
    )
    payload = AgentConfigSerializer().serialize(agent)
    jsonschema.validate(payload, schema)


def test_agent_schema_rejects_unknown_root_fields():
    schema = json.loads(SCHEMA_PATH.read_text())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"name": "valid_name", "unknownField": True}, schema)


def test_agent_schema_accepts_jev_definition():
    from conductor.ai.agents import JevAgent

    questions = {
        "team": {"type": "choice", "instructions": "Choose", "choices": {"a": "A", "b": "B"}},
        "priority": {"type": "score", "instructions": "Score", "scale": ["low", "high"]},
        "ready": {"type": "boolean", "instructions": "Ready?"},
    }
    schema = json.loads(SCHEMA_PATH.read_text())
    for fixed_questions in (questions, None):
        agent = JevAgent("jev", model="jev-1.13", questions=fixed_questions)
        jsonschema.validate(AgentConfigSerializer().serialize(agent), schema)
