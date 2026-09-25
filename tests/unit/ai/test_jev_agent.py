import json

import pytest

from conductor.ai.agents import (
    Agent,
    AgentResult,
    BooleanQuestion,
    ChoiceQuestion,
    JevAgent,
    ScoreQuestion,
)
from conductor.ai.agents.config_serializer import AgentConfigSerializer
from conductor.ai.agents.jev import jev_questions
from conductor.ai.agents.runtime.runtime import AgentRuntime


def test_jev_agent_serializes_as_an_agent_and_as_a_child():
    definition = JevAgent(
        "choose",
        model="jev-1.13",
        questions={
            "action": ChoiceQuestion("Choose an action", {"go": "Proceed", "wait": "Wait"}),
            "quality": ScoreQuestion("Evaluate quality", ["low", "high"]),
            "ready": BooleanQuestion("Ready to proceed?"),
        },
    )
    assert isinstance(definition, Agent)
    config = AgentConfigSerializer().serialize(definition)
    assert config["kind"] == "jev"
    assert "decisionProvider" not in config
    assert config["questions"]["action"]["choices"] == {"go": "Proceed", "wait": "Wait"}
    assert "tools" not in config
    assert "credentials" not in config
    parent = Agent("parent", agents=[definition], strategy="sequential")
    assert AgentConfigSerializer().serialize(parent)["agents"][0]["kind"] == "jev"
    assert "kind" not in AgentConfigSerializer().serialize(Agent("chat", model="openai/model"))


def test_dynamic_questions_and_json_state():
    agent = JevAgent("choose", model="jev-1.13")
    assert "questions" not in AgentConfigSerializer().serialize(agent)
    runtime = AgentRuntime.__new__(AgentRuntime)
    assert json.loads(runtime._resolve_prompt({"ready": True, "value": None})) == {
        "ready": True,
        "value": None,
    }
    # No attempt to register Jev models as chat providers.
    runtime._ensure_models_for_agent(agent)
    assert jev_questions({"ready": BooleanQuestion("Ready?")})["ready"]["type"] == "boolean"


@pytest.mark.parametrize(
    "question",
    [
        {"type": "choice", "instructions": "Choose", "choices": {"only": "Only"}},
        {"type": "score", "instructions": "Score", "scale": []},
        {"type": "boolean", "instructions": "", "choices": {}},
    ],
)
def test_invalid_question_contract_is_rejected(question):
    with pytest.raises(ValueError, match=r"requires|invalid"):
        JevAgent("bad", model="jev-1.13", questions={"q": question})


def test_typed_result_preserves_provider_details_without_chat_wrapping():
    raw = {
        "model": "jev-1.13",
        "answers": {
            "action": {"type": "choice", "choice": "go", "confidence": 0.9},
            "score": {"type": "score", "score": 1.2},
            "ready": {"type": "boolean", "probability": 0.8},
        },
        "usage": {"inputTokens": 10, "outputTokens": 3, "cost": 0.001, "currency": "USD"},
        "requestId": "req",
        "latencyMs": 42,
    }
    result = AgentResult(output={"result": raw})
    assert result.jev.answers["action"].choice == "go"
    assert result.jev.answers["score"].score == raw["answers"]["score"]["score"]
    assert result.jev.answers["ready"].probability == raw["answers"]["ready"]["probability"]
    assert result.jev.usage == raw["usage"]
    assert result.jev.latency_ms == raw["latencyMs"]
    assert result.jev.request_id == "req"
    assert AgentResult(output={"result": "chat"}).jev is None


def test_failed_jev_has_no_typed_answer():
    result = AgentResult(status="FAILED", output={"agentKind": "jev", "result": {}})
    assert result.jev is None


@pytest.fixture
def runtime():
    from unittest.mock import patch
    from conductor.ai.agents.runtime.config import AgentConfig

    with patch("conductor.client.orkes_clients.OrkesClients"):
        with AgentRuntime(settings=AgentConfig(auto_start_workers=False)) as runtime:
            yield runtime


def test_agent_def_and_convenience_class_serialize_identically(runtime):
    from conductor.ai.agents import AgentDef

    questions = {"ready": BooleanQuestion("Ready?")}
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


@pytest.mark.parametrize("status", ["COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"])
def test_start_and_poll_preserves_structured_result_and_failure_reason(runtime, status):
    from unittest.mock import patch
    from conductor.ai.agents import AgentDef

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
    handle = runtime.start(
        definition, "Ready?", context={"questions": {"ready": BooleanQuestion("Ready?")}}
    )
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


def test_dynamic_questions_required_before_start(runtime):
    with pytest.raises(ValueError, match="questions"):
        runtime.start(JevAgent("ready", model="jev-1.13"), "Ready?")
    runtime._agent_client.start_agent.assert_not_called()


def test_async_start_and_dynamic_compile(runtime):
    import asyncio
    from unittest.mock import AsyncMock
    from conductor.ai.agents import AgentDef

    definition = AgentDef(name="ready", kind="jev", model="jev-1.13")
    context = {"questions": {"ready": BooleanQuestion("Ready?")}}
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


def test_jev_has_no_tool_or_internal_task_exports():
    import conductor.ai.agents as agents

    assert not hasattr(agents, "DecisionModelTool")
    assert not hasattr(agents, "DecisionAgent")
    assert not hasattr(agents, "JEV_AGENT")
