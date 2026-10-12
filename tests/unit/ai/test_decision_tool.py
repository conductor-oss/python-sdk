import pytest

from conductor.ai.agents import Agent, Strategy, ToolDef
from conductor.ai.agents.config_serializer import AgentConfigSerializer
from examples.agents.decision_router import support_router
from examples.agents.decision_tool import support_agent


def test_decision_router_example_serializes_inline_selector(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_DECISION_PROVIDER", "typesafe")
    config = AgentConfigSerializer().serialize(support_router())
    selector = config["router"]

    assert config["external"] is False
    assert selector["kind"] == "decision"
    assert selector["model"] == "jev-1.13"
    assert selector["provider"] == "typesafe"
    assert set(selector["questions"]["agent"]["choices"]) == {
        child["name"] for child in config["agents"]
    }
    assert Agent(name="existing_workflow").external is True


@pytest.mark.parametrize(
    ("tool_type", "config", "message"),
    [
        ("http", {}, "Only a decision ToolDef"),
        ("decision", {"questions": {}}, "requires 'model'"),
        ("decision", {"model": "jev-1.13"}, "requires 'questions'"),
    ],
)
def test_decision_router_rejects_invalid_selector(tool_type, config, message):
    agent = Agent(
        name="router",
        strategy=Strategy.ROUTER,
        router=ToolDef(name="selector", tool_type=tool_type, config=config),
    )
    with pytest.raises(ValueError, match=message):
        AgentConfigSerializer().serialize(agent)


def test_decision_tool_example_uses_existing_tool_serialization():
    config = AgentConfigSerializer().serialize(support_agent)
    tool = config["tools"][0]
    assert tool["toolType"] == "decision"
    assert tool["config"]["model"] == "jev-1.13"
    assert set(tool["config"]["questions"]["department"]["choices"]) == {"billing", "technical"}
