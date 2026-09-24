import pytest

from conductor.ai.agents import Agent, DecisionModelTool, agent
from conductor.ai.agents.config_serializer import AgentConfigSerializer


def test_fixed_questions_are_configuration_and_require_no_worker():
    questions = {
        "team": {
            "type": "choice",
            "instructions": "Select team",
            "choices": {"billing": "Payments", "support": "Technical help"},
        }
    }
    tool = DecisionModelTool(
        "decide", "Decide team", provider="jev", model="jev-1.13", questions=questions, max_calls=1
    )
    assert tool.func is None
    assert tool.credentials == []
    questions["team"]["instructions"] = "mutated"

    class Example:
        @agent(model="openai/configured-model", tools=[tool])
        def assistant(self):
            """Use the decision tool."""

    definition = Agent.from_instance(Example(), "assistant")
    data = AgentConfigSerializer().serialize(definition)["tools"][0]
    assert data["toolType"] == "decision_model"
    assert data["config"]["provider"] == "jev"
    assert data["config"]["questions"]["team"]["instructions"] == "Select team"
    assert set(data["inputSchema"]["properties"]) == {"state"}
    assert data["maxCalls"] == 1
    assert "credentials" not in data["config"]


def test_dynamic_questions_use_provider_neutral_schema():
    tool = DecisionModelTool("decide", "Evaluate questions", provider="another", model="v1")
    assert tool.input_schema["required"] == ["state", "questions"]
    variants = tool.input_schema["properties"]["questions"]["additionalProperties"]["oneOf"]
    assert [v["properties"]["type"]["enum"] for v in variants] == [
        ["choice"],
        ["score"],
        ["boolean"],
    ]
    assert "provider" not in tool.input_schema["properties"]
    assert "model" not in tool.input_schema["properties"]
    assert tool.config == {"provider": "another", "model": "v1"}


def test_invalid_config_fails_locally():
    with pytest.raises(ValueError):
        DecisionModelTool("decide", "Test", provider="", model="v1")
    with pytest.raises(ValueError):
        DecisionModelTool("decide", "Test", provider="jev", model="")
    with pytest.raises(ValueError):
        DecisionModelTool("decide", "Test", provider="jev", model="v1", questions={})
