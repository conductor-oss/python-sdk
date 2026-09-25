from unittest.mock import AsyncMock, patch
import asyncio

import pytest

from conductor.ai.agents import AgentDef, AgentRuntime, JevAgent
from conductor.ai.agents.config_serializer import AgentConfigSerializer
from conductor.ai.agents.runtime.config import AgentConfig

QUESTIONS = {"ready": {"type": "boolean", "instructions": "Ready?"}}


@pytest.fixture
def runtime():

    with patch("conductor.client.orkes_clients.OrkesClients"):
        with AgentRuntime(settings=AgentConfig(auto_start_workers=False)) as runtime:
            yield runtime


def test_agent_def_and_convenience_class_serialize_identically(runtime):

    questions = QUESTIONS
    definition = AgentDef(name="ready", kind="jev", model="jev-1.13", questions=questions)
    expected = {
        "name": "ready",
        "kind": "jev",
        "model": "jev-1.13",
        "questions": {"ready": {"type": "boolean", "instructions": "Ready?"}},
    }
    assert AgentConfigSerializer().serialize(definition) == expected
    assert (
        AgentConfigSerializer().serialize(JevAgent("ready", model="jev-1.13", questions=questions))
        == expected
    )
    runtime.plan(definition, "Ready to ship")
    runtime._agent_client.compile_agent.assert_called_once_with(
        {"agentConfig": expected, "prompt": "Ready to ship"}
    )
    runtime._agent_client.start_agent.assert_not_called()
    runtime._ensure_models_for_agent(JevAgent("ready", model="jev-1.13"))


@pytest.mark.parametrize("status", ["COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"])
def test_start_and_poll_preserves_structured_result_and_failure_reason(runtime, status):

    definition = AgentDef(name="ready", kind="jev", model="jev-1.13")
    raw = {
        "model": "jev-1.13",
        "answers": {"ready": {"type": "boolean", "probability": 0.8}},
        "usage": {"inputTokens": 10},
        "latencyMs": 42,
        "requestId": "request-1",
    }
    runtime._agent_client.start_agent.return_value = {
        "executionId": "execution-1",
        "requiredWorkers": [],
    }
    runtime._agent_client.get_status.side_effect = [
        {"isComplete": False, "status": "RUNNING"},
        {
            "isComplete": True,
            "status": status,
            "output": {"result": raw},
            "reasonForIncompletion": "provider failure" if status != "COMPLETED" else None,
        },
    ]
    handle = runtime.start(definition, "Ready?", context={"questions": QUESTIONS})
    assert handle.execution_id == "execution-1"
    payload = runtime._agent_client.start_agent.call_args.args[0]
    assert payload["agentConfig"] == {"name": "ready", "kind": "jev", "model": "jev-1.13"}
    assert payload["context"]["questions"]["ready"] == {"type": "boolean", "instructions": "Ready?"}
    assert not runtime._workers_started
    with patch("time.sleep"):
        result = handle.join(timeout=5)
    assert runtime._agent_client.get_status.call_count == 2
    assert result.output["result"] == raw
    assert result.is_success == (status == "COMPLETED")
    assert result.error == (None if status == "COMPLETED" else "provider failure")


def test_async_start_and_dynamic_compile(runtime):

    definition = AgentDef(name="ready", kind="jev", model="jev-1.13")
    context = {"questions": QUESTIONS}
    runtime.plan(definition, "Ready?", context=context)
    assert (
        runtime._agent_client.compile_agent.call_args.args[0]["context"]["questions"]["ready"][
            "type"
        ]
        == "boolean"
    )
    runtime._agent_client.start_agent_async = AsyncMock(
        return_value={"executionId": "async-1", "requiredWorkers": []}
    )
    handle = asyncio.run(runtime.start_async(definition, "Ready?", context=context))
    assert handle.execution_id == "async-1"
    assert (
        runtime._agent_client.start_agent_async.call_args.args[0]["context"]["questions"]["ready"][
            "type"
        ]
        == "boolean"
    )


def test_nested_jev_example_routes_to_named_agents(monkeypatch):
    import runpy
    from pathlib import Path

    examples = Path(__file__).resolve().parents[3] / "examples" / "agents"
    monkeypatch.syspath_prepend(str(examples))
    nested = runpy.run_path(str(examples / "jev_nested_triage.py"))["triage_agent"]()
    serializer = AgentConfigSerializer()
    config = serializer.serialize(nested)
    assert config["external"] is False
    assert not config.get("model")
    assert len(config["agents"]) == 3
    assert sum(len(team["agents"]) for team in config["agents"]) == 10
    for team in [config, *config["agents"]]:
        assert team["router"]["kind"] == "jev"
        assert set(team["router"]["questions"]["agent"]["choices"]) == {
            child["name"] for child in team["agents"]
        }
    luna = runpy.run_path(str(examples / "luna_jev_triage.py"))["triage_agent"]("configured/luna-6")
    config = serializer.serialize(luna)
    assert config["router"]["model"] == "configured/luna-6"
    assert len(config["agents"]) == 10
    assert all(child["kind"] == "jev" for child in config["agents"])
    assert config["maxTurns"] == 1
    assert config["synthesize"] is False
