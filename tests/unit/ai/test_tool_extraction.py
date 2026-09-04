"""Unit tests for tool-call and event extraction from an execution's tasks.

Covers the two surfaces the ``testing`` assertions read:
:meth:`AgentRuntime._extract_tool_calls` and :meth:`AgentRuntime._extract_events`.

Tasks are built as plain objects rather than ``MagicMock`` on purpose — a mock
answers every attribute with a truthy stub, which is how a fixture ends up
agreeing with a detection bug instead of catching it.
"""

from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from conductor.ai.agents.agent import Agent
from conductor.ai.agents.result import AgentStatus, EventType
from conductor.ai.agents.testing.assertions import assert_max_turns, assert_no_errors


class Task:
    """A minimal stand-in for ``conductor.client.http.models.Task``."""

    def __init__(
        self,
        *,
        task_type: str,
        reference_task_name: str = "ref",
        task_def_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "COMPLETED",
        task_id: Optional[str] = None,
    ):
        self.task_type = task_type
        self.reference_task_name = reference_task_name
        self.task_def_name = task_def_name
        self.input_data = input_data or {}
        self.output_data = output_data or {}
        self.status = status
        self.task_id = task_id or reference_task_name


class Workflow:
    """A minimal stand-in for a workflow execution with tasks."""

    def __init__(self, tasks=None, status="COMPLETED", output=None, reason=None):
        self.tasks = tasks or []
        self.status = status
        self.output = output
        self.reason = reason


@pytest.fixture()
def runtime():
    with patch("conductor.client.orkes_clients.OrkesClients"):
        with patch("conductor.ai.agents.runtime.worker_manager.TaskHandler", create=True):
            from conductor.ai.agents.runtime.config import AgentConfig
            from conductor.ai.agents.runtime.runtime import AgentRuntime

            return AgentRuntime(settings=AgentConfig(auto_start_workers=False))


# ── Tool identity does not depend on the provider's reference name ──────


class TestToolCallDetection:
    def test_detects_worker_tool_under_an_anthropic_call_id(self, runtime):
        """The reference name carries the provider's tool-call id, not ours."""
        task = Task(
            task_type="SIMPLE",
            reference_task_name="toolu_01PJDP6YvZbhFp3wBnQeC2D3",
            task_def_name="Read",
            input_data={"file_path": "/tmp/x"},
            output_data={"content": "hello"},
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert len(calls) == 1
        assert calls[0]["name"] == "Read"
        assert calls[0]["args"] == {"file_path": "/tmp/x"}
        assert calls[0]["result"] == {"content": "hello"}

    def test_detects_worker_tool_under_an_openai_call_id(self, runtime):
        task = Task(
            task_type="get_weather",
            reference_task_name="call_PMnNIdOPvm9EQ8e6tn2kbxPY_0__1",
            task_def_name="get_weather",
            input_data={"city": "NYC"},
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert [c["name"] for c in calls] == ["get_weather"]

    def test_preserves_camel_case_worker_names(self, runtime):
        task = Task(
            task_type="getWeather",
            reference_task_name="call_abc__0",
            task_def_name="getWeather",
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert calls[0]["name"] == "getWeather"

    def test_skips_framework_passthrough_wrapper(self, runtime):
        task = Task(
            task_type="my_agent_worker",
            reference_task_name="_fw_task",
            task_def_name="my_agent_worker",
        )

        assert runtime._extract_tool_calls(Workflow([task])) == []

    @pytest.mark.parametrize(
        "task_type",
        ["LLM_CHAT_COMPLETE", "SWITCH", "DO_WHILE", "INLINE", "SET_VARIABLE", "JOIN", "TERMINATE"],
    )
    def test_skips_system_tasks(self, runtime, task_type):
        task = Task(task_type=task_type, task_def_name=task_type.lower())

        assert runtime._extract_tool_calls(Workflow([task])) == []

    @pytest.mark.parametrize(
        "worker_name",
        [
            "support_stop_when",
            "support_gate",
            "support_termination",
            "support_check_transfer",
            "support_router_fn",
            "support_handoff_check",
            "support_process_selection",
            "support_before_model",
            "support_after_tool",
            "support_output_guardrail",
        ],
    )
    def test_skips_the_agents_own_machinery(self, runtime, worker_name):
        """Callbacks, guardrails and routing compile to SIMPLE tasks too."""
        task = Task(
            task_type=worker_name,
            reference_task_name=worker_name,
            task_def_name=worker_name,
        )

        assert runtime._extract_tool_calls(Workflow([task])) == []

    def test_skips_a_custom_guardrail_worker_named_by_the_user(self, runtime):
        task = Task(
            task_type="no_profanity",
            reference_task_name="support_output_guardrail_no_profanity_worker",
            task_def_name="no_profanity",
        )

        assert runtime._extract_tool_calls(Workflow([task])) == []

    def test_keeps_a_user_tool_whose_name_merely_mentions_guardrails(self, runtime):
        task = Task(
            task_type="guardrail_lookup",
            reference_task_name="toolu_01LOOKUP",
            task_def_name="guardrail_lookup",
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert [c["name"] for c in calls] == ["guardrail_lookup"]

    def test_dispatched_tool_wins_over_an_internal_name_suffix(self, runtime):
        """A user tool may legitimately be called ``open_gate``."""
        task = Task(
            task_type="open_gate",
            reference_task_name="toolu_01GATE",
            task_def_name="open_gate",
            input_data={"_agent_tool_name": "open_gate", "door": "front"},
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert [c["name"] for c in calls] == ["open_gate"]
        assert calls[0]["args"] == {"door": "front"}

    def test_keeps_swarm_transfer_tools(self, runtime):
        """``transfer_to_x`` is a tool the LLM chose to call, not machinery."""
        task = Task(
            task_type="support_transfer_to_billing",
            reference_task_name="call_abc__0",
            task_def_name="support_transfer_to_billing",
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert [c["name"] for c in calls] == ["support_transfer_to_billing"]


class TestToolKindsAndNaming:
    """Every row of the server's ``ToolCompiler.TYPE_MAP`` is a tool call."""

    @pytest.mark.parametrize(
        ("task_type", "tool_name"),
        [
            ("HTTP", "fetch_quote"),
            ("CALL_MCP_TOOL", "list_files"),
            ("HUMAN", "ask_question"),
            ("PULL_WORKFLOW_MESSAGES", "await_message"),
            ("GENERATE_IMAGE", "draw_logo"),
            ("GENERATE_AUDIO", "narrate"),
            ("GENERATE_VIDEO", "animate"),
            ("LLM_INDEX_TEXT", "index_docs"),
            ("LLM_SEARCH_INDEX", "search_docs"),
        ],
    )
    def test_non_worker_tool_kinds_are_detected_and_named(self, runtime, task_type, tool_name):
        task = Task(
            task_type=task_type,
            reference_task_name="whatever_0",
            task_def_name=task_type.lower(),
            input_data={"_agent_tool_name": tool_name, "query": "q"},
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert [c["name"] for c in calls] == [tool_name]
        assert calls[0]["args"] == {"query": "q"}

    def test_agent_tool_sub_workflow_is_a_tool_call(self, runtime):
        task = Task(
            task_type="SUB_WORKFLOW",
            reference_task_name="call_x__0",
            input_data={"_agent_tool_name": "research_agent", "prompt": "find it"},
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert [c["name"] for c in calls] == ["research_agent"]

    def test_handoff_sub_workflow_is_not_a_tool_call(self, runtime):
        """A strategy handoff has no ``_agent_tool_name``; it is not a tool."""
        task = Task(task_type="SUB_WORKFLOW", reference_task_name="support_handoff_0_billing")

        assert runtime._extract_tool_calls(Workflow([task])) == []

    def test_mcp_tool_name_falls_back_to_method(self, runtime):
        task = Task(
            task_type="CALL_MCP_TOOL",
            task_def_name="call_mcp_tool",
            input_data={"method": "read_file", "arguments": {"path": "/tmp/x"}},
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert calls[0]["name"] == "read_file"

    def test_internal_keys_are_stripped_from_args(self, runtime):
        task = Task(
            task_type="get_weather",
            task_def_name="get_weather",
            input_data={
                "city": "NYC",
                "_agent_tool_name": "get_weather",
                "_agent_state": {"turn": 1},
                "_allowed_commands": ["ls"],
                "method": "get_weather",
                "__humanTaskDefinition": {},
                "__conductor_agent_ctx__": {},
            },
        )

        calls = runtime._extract_tool_calls(Workflow([task]))

        assert calls[0]["args"] == {"city": "NYC"}


# ── Events on the default (non-streaming) path ──────────────────────────


class TestExtractEvents:
    def test_tool_task_yields_call_and_result(self, runtime):
        task = Task(
            task_type="SIMPLE",
            reference_task_name="toolu_01ABC",
            task_def_name="Read",
            input_data={"file_path": "/tmp/x"},
            output_data={"content": "hi"},
        )

        events = runtime._extract_events(Workflow([task]), "wf-1")
        by_type = [e.type for e in events]

        assert EventType.TOOL_CALL in by_type
        assert EventType.TOOL_RESULT in by_type
        call = next(e for e in events if e.type == EventType.TOOL_CALL)
        assert call.tool_name == "Read"
        assert call.args == {"file_path": "/tmp/x"}
        assert call.execution_id == "wf-1"

    def test_llm_task_yields_thinking(self, runtime):
        task = Task(task_type="LLM_CHAT_COMPLETE", reference_task_name="llm_0")

        events = runtime._extract_events(Workflow([task]), "wf-1")

        assert [e.type for e in events] == [EventType.THINKING, EventType.DONE]

    def test_handoff_sub_workflow_yields_handoff(self, runtime):
        task = Task(task_type="SUB_WORKFLOW", reference_task_name="support_handoff_0_billing")

        events = runtime._extract_events(Workflow([task]), "wf-1")
        handoffs = [e for e in events if e.type == EventType.HANDOFF]

        assert [e.target for e in handoffs] == ["billing"]

    def test_running_agent_tool_is_not_reported_as_a_handoff(self, runtime):
        """An ``agent_tool`` is a SUB_WORKFLOW; only a strategy handoff is one."""
        task = Task(
            task_type="SUB_WORKFLOW",
            reference_task_name="toolu_01SUB",
            status="IN_PROGRESS",
            input_data={"_agent_tool_name": "research_agent"},
        )

        events = runtime._extract_events(Workflow([task], status="RUNNING"), "wf-1")

        assert [e.type for e in events if e.type == EventType.HANDOFF] == []

    def test_guardrail_task_yields_pass_and_fail(self, runtime):
        ok = Task(
            task_type="SIMPLE",
            reference_task_name="support_regex_guardrail_pii",
            output_data={"passed": True, "guardrail_name": "pii"},
        )
        bad = Task(
            task_type="SIMPLE",
            reference_task_name="support_llm_guardrail_tone",
            output_data={"passed": False, "guardrail_name": "tone", "message": "rude"},
        )

        events = runtime._extract_events(Workflow([ok, bad]), "wf-1")

        assert [e.guardrail_name for e in events if e.type == EventType.GUARDRAIL_PASS] == ["pii"]
        assert [e.guardrail_name for e in events if e.type == EventType.GUARDRAIL_FAIL] == ["tone"]

    def test_completed_workflow_ends_with_done(self, runtime):
        wf = Workflow([], status="COMPLETED", output={"result": "42"})

        events = runtime._extract_events(wf, "wf-1")

        assert events[-1].type == EventType.DONE
        assert events[-1].output == "42"

    def test_failed_task_yields_error(self, runtime):
        task = Task(
            task_type="get_weather",
            task_def_name="get_weather",
            status="FAILED",
            output_data={"reason": "boom"},
        )

        events = runtime._extract_events(Workflow([task], status="FAILED"), "wf-1")
        errors = [e for e in events if e.type == EventType.ERROR]

        assert "boom" in errors[0].content
        assert errors[-1].content == "Execution FAILED"


# ── run() wires the events through ──────────────────────────────────────


class TestRunPopulatesEvents:
    def test_run_populates_events_without_an_on_event_callback(self, runtime):
        agent = Agent(name="test", model="openai/gpt-4o")
        runtime._prepare_workers = lambda *a, **k: None
        runtime._start_via_server = lambda *a, **k: ("wf-events", None, [])
        runtime._poll_status_until_complete = lambda *a, **k: AgentStatus(
            execution_id="wf-events",
            is_complete=True,
            output={"result": "sunny", "finishReason": "STOP"},
            status="COMPLETED",
        )

        wf = Workflow(
            [
                Task(task_type="LLM_CHAT_COMPLETE", reference_task_name="llm_0"),
                Task(
                    task_type="SIMPLE",
                    reference_task_name="toolu_01ABC",
                    task_def_name="get_weather",
                    input_data={"city": "NYC"},
                    output_data={"temp": 72},
                ),
            ],
            output={"result": "sunny"},
        )
        wf.variables = {"messages": []}

        calls = []

        def get_workflow(execution_id, include_tasks=False):
            calls.append(execution_id)
            return wf

        runtime._workflow_client.get_workflow = get_workflow

        with patch.object(runtime, "_fetch_agent_workflow", return_value=None):
            result = runtime.run(agent, "What's the weather?")

        assert [e.type for e in result.events] == [
            EventType.THINKING,
            EventType.TOOL_CALL,
            EventType.TOOL_RESULT,
            EventType.DONE,
        ]
        assert [tc["name"] for tc in result.tool_calls] == ["get_weather"]
        assert calls == ["wf-events"], "events must reuse the execution already fetched"

        assert_no_errors(result)
        assert_max_turns(result, 2)


# ── The eval runner's documented example ────────────────────────────────


class TestEvalRunnerAgainstAPolledRun:
    """The runner calls ``run()`` with no ``on_event``; its checks read events."""

    @pytest.fixture()
    def support_run(self, runtime):
        """A handoff run: one tool call, then a handoff to ``billing``."""
        wf = Workflow(
            [
                Task(task_type="LLM_CHAT_COMPLETE", reference_task_name="llm_0"),
                Task(
                    task_type="SIMPLE",
                    reference_task_name="toolu_01LOOKUP",
                    task_def_name="lookup_order",
                    input_data={"order_id": "123"},
                    output_data={"status": "shipped"},
                ),
                Task(
                    task_type="SUB_WORKFLOW",
                    reference_task_name="support_handoff_0_billing",
                ),
            ],
            output={"result": "Your refund is on its way."},
        )
        wf.variables = {"messages": []}

        runtime._prepare_workers = lambda *a, **k: None
        runtime._start_via_server = lambda *a, **k: ("wf-support", None, [])
        runtime._poll_status_until_complete = lambda *a, **k: AgentStatus(
            execution_id="wf-support",
            is_complete=True,
            output={"result": "Your refund is on its way.", "finishReason": "STOP"},
            status="COMPLETED",
        )
        runtime._workflow_client.get_workflow = lambda *a, **k: wf
        return runtime

    def test_documented_eval_case_passes(self, support_run):
        from conductor.ai.agents.testing.eval_runner import CorrectnessEval, EvalCase

        agent = Agent(name="support", model="openai/gpt-4o")
        with patch.object(support_run, "_fetch_agent_workflow", return_value=None):
            suite = CorrectnessEval(support_run).run(
                [
                    EvalCase(
                        name="billing_routes_correctly",
                        agent=agent,
                        prompt="I need a refund for order #123",
                        expect_tools=["lookup_order"],
                        expect_handoff_to="billing",
                        expect_output_contains=["refund"],
                    )
                ]
            )

        failures = [c for case in suite.cases for c in case.checks if not c.passed]
        assert failures == []

    def test_absence_checks_can_still_fail(self, support_run):
        """The four assertions that used to pass vacuously now see real evidence."""
        from conductor.ai.agents.testing.eval_runner import CorrectnessEval, EvalCase

        agent = Agent(name="support", model="openai/gpt-4o")
        with patch.object(support_run, "_fetch_agent_workflow", return_value=None):
            suite = CorrectnessEval(support_run).run(
                [
                    EvalCase(
                        name="wrongly_expects_no_billing",
                        agent=agent,
                        prompt="I need a refund for order #123",
                        expect_tools_not_used=["lookup_order"],
                        expect_no_handoff_to=["billing"],
                    )
                ]
            )

        failed = {c.check for case in suite.cases for c in case.checks if not c.passed}
        assert failed == {"tool_not_used:lookup_order", "no_handoff_to:billing"}
