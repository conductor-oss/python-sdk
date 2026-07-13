# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""FunctionRef / SpawnSafetyError / probe / async-detection tests (idea-5 Stage 1).

Cross-process cases use the real 'spawn' context regardless of platform
default, so they exercise exactly what CI's Linux runners and macOS both do.
"""

import multiprocessing
import pickle

import pytest

from conductor.ai.agents.guardrail import Guardrail, OnFail, Position, RegexGuardrail
from conductor.ai.agents.runtime import _worker_entries as we
from conductor.ai.agents.runtime._worker_entries import (
    FunctionRef,
    SpawnSafetyError,
    ToolWorkerEntry,
    probe_spawn_safety,
)
from conductor.ai.agents.tool import get_tool_def
from conductor.client.automator.task_handler import _is_async_execute_callable
from tests.unit.resources import worker_entry_helpers as helpers


# ── FunctionRef.of accept/reject matrix ─────────────────────────────────


class TestFunctionRefOf:
    def test_module_level_function_depth_0(self):
        ref = FunctionRef.of(helpers.plain_sample)
        assert ref == FunctionRef(helpers.__name__, "plain_sample", 0)

    def test_tool_wrapper_global_depth_0(self):
        # The module global IS the @tool wraps-wrapper — resolves directly.
        ref = FunctionRef.of(helpers.decorated_sample)
        assert ref.qualname == "decorated_sample"
        assert ref.unwrap_depth == 0

    def test_tool_original_fn_depth_1(self):
        # ToolDef.func is the original underneath the wrapper — one hop.
        original = get_tool_def(helpers.decorated_sample).func
        assert original is not helpers.decorated_sample
        ref = FunctionRef.of(original)
        assert ref.unwrap_depth == 1
        assert ref.resolve() is original

    def test_lambda_rejected(self):
        with pytest.raises(SpawnSafetyError, match="lambda"):
            FunctionRef.of(lambda x: x)

    def test_nested_function_rejected(self):
        def nested(x):
            return x

        with pytest.raises(SpawnSafetyError, match="inside a function"):
            FunctionRef.of(nested)

    def test_bound_method_rejected(self):
        with pytest.raises(SpawnSafetyError, match="not a plain function"):
            FunctionRef.of(helpers.SyncCallEntry(2).__call__)

    def test_callable_instance_rejected(self):
        # Instances pickle by value; refs are for functions only.
        with pytest.raises(SpawnSafetyError, match="not a plain function"):
            FunctionRef.of(helpers.SyncCallEntry(2))

    def test_rebound_name_without_wrapped_chain_rejected(self, monkeypatch):
        original = helpers.plain_sample
        # Rebind the module global to something unrelated (no __wrapped__
        # chain back) — the original function is now unreachable by name.
        monkeypatch.setattr(helpers, "plain_sample", helpers.async_sample)
        with pytest.raises(SpawnSafetyError, match="does not resolve back"):
            FunctionRef.of(original)


class TestFunctionRefResolve:
    def test_resolve_plain(self):
        assert FunctionRef.of(helpers.plain_sample).resolve()(4) == 8

    def test_resolve_is_memoized_per_process(self):
        ref = FunctionRef.of(helpers.plain_sample)
        assert ref.resolve() is ref.resolve()
        assert ref in we._RESOLVE_CACHE

    def test_ref_pickles(self):
        ref = FunctionRef.of(helpers.plain_sample)
        assert pickle.loads(pickle.dumps(ref)) == ref

    def test_cross_process_spawn_roundtrip(self):
        """The headline case: ref crosses a REAL spawn boundary and executes."""
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        ref_bytes = pickle.dumps(FunctionRef.of(helpers.plain_sample))
        p = ctx.Process(target=helpers.resolve_and_call_child, args=(ref_bytes, 21, q))
        p.start()
        try:
            assert q.get(timeout=30) == 42
        finally:
            p.join(timeout=30)
        assert p.exitcode == 0


# ── Container-attribute hop (langchain @tool → StructuredTool) ───────────


class TestFunctionRefContainerHop:
    """Decorators that rebind the global to a container object, not a
    wraps-wrapper — the suite11 CI failure (langchain's @tool)."""

    def test_sync_container_func_attr(self):
        raw = helpers.container_sample.func
        ref = FunctionRef.of(raw)
        assert ref == FunctionRef(helpers.__name__, "container_sample", 0, "func")
        assert ref.resolve() is raw

    def test_async_container_coroutine_attr(self):
        raw = helpers.async_container_sample.coroutine
        ref = FunctionRef.of(raw)
        assert ref.attr_hop == "coroutine"
        assert ref.resolve() is raw

    def test_ref_with_hop_pickles(self):
        raw = helpers.container_sample.func
        ref = pickle.loads(pickle.dumps(FunctionRef.of(raw)))
        assert ref.resolve()(4) == 15

    def test_entry_transports_container_held_fn_by_ref(self):
        # Pre-fix this fell to fn_direct, whose reference pickling then found
        # the container at the global name: "it's not the same object as …".
        raw = helpers.container_sample.func
        entry = ToolWorkerEntry.for_callable(raw, "container_tool")
        assert entry.fn_ref is not None
        clone = pickle.loads(pickle.dumps(entry))
        assert clone._target() is raw

    def test_real_langchain_tool_roundtrip(self):
        pytest.importorskip("langchain_core")
        from tests.unit.resources import langchain_entry_helpers as lch

        raw = lch.lc_multiply.func
        ref = FunctionRef.of(raw)
        assert ref.attr_hop == "func"
        assert pickle.loads(pickle.dumps(ref)).resolve() is raw

        raw_async = lch.lc_multiply_async.coroutine
        ref_async = FunctionRef.of(raw_async)
        assert ref_async.attr_hop == "coroutine"
        assert ref_async.resolve() is raw_async

    def test_cross_process_spawn_roundtrip_with_hop(self):
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        ref_bytes = pickle.dumps(FunctionRef.of(helpers.container_sample.func))
        p = ctx.Process(target=helpers.resolve_and_call_child, args=(ref_bytes, 4, q))
        p.start()
        try:
            assert q.get(timeout=30) == 15  # container_sample(4) == 4 + 11
        finally:
            p.join(timeout=30)
        assert p.exitcode == 0


# ── Guardrail spawn transport ─────────────────────────────────────────────


class TestGuardrailSpawnTransport:
    """Guardrail.func travels via wrap_callable — the suite8 CI failure:
    @guardrail extracts the raw function (the global is the wraps-wrapper),
    so pickling it by reference found the wrapper instead."""

    @staticmethod
    def _guard():
        return Guardrail(
            helpers.sample_guardrail, position=Position.INPUT, on_fail=OnFail.RAISE
        )

    def test_decorated_guardrail_pickles(self):
        g = self._guard()
        clone = pickle.loads(pickle.dumps(g))
        assert clone.name == "no_marker"
        assert clone.func is g.func  # FunctionRef resolves to the same object
        assert clone.check("has MARKER").passed is False
        assert clone.check("clean").passed is True

    def test_tool_entry_with_guardrail_pickles(self):
        # The exact suite8 shape: @guardrail func attached to a tool worker.
        entry = ToolWorkerEntry.for_callable(
            helpers.plain_sample, "safe_query", guardrails=[self._guard()]
        )
        clone = pickle.loads(pickle.dumps(entry))
        assert clone.guardrails[0].check("MARKER!").passed is False

    def test_regex_guardrail_bound_method_still_pickles(self):
        rg = RegexGuardrail(patterns=[r"foo"], name="no_foo", message="no foo")
        clone = pickle.loads(pickle.dumps(rg))
        assert clone.check("has foo").passed is False
        assert clone.check("clean").passed is True

    def test_external_guardrail_pickles(self):
        g = Guardrail(name="external_ref")
        clone = pickle.loads(pickle.dumps(g))
        assert clone.external is True
        assert clone.func is None


# ── ToolWorkerEntry across a real spawn boundary ─────────────────────────


class TestToolWorkerEntrySpawn:
    def test_entry_executes_tool_task_in_spawn_child(self):
        """Full worker unit crosses spawn and runs a Task with NO parent registry
        state — the exact scenario the 20 CI pickle failures never reached."""
        from conductor.ai.agents.runtime._dispatch import make_tool_worker
        from conductor.ai.agents.tool import get_tool_def

        td = get_tool_def(helpers.decorated_sample)
        entry = make_tool_worker(td.func, "decorated_sample", tool_def=td)
        entry_bytes = pickle.dumps(entry)  # must pickle — this raised pre-fix

        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        p = ctx.Process(target=helpers.run_tool_entry_child, args=(entry_bytes, 5, q))
        p.start()
        try:
            status, output = q.get(timeout=30)
        finally:
            p.join(timeout=30)
        assert p.exitcode == 0
        assert "COMPLETED" in status
        assert output == {"result": 12}  # decorated_sample(5) == 5 + 7


class TestCodeExecutionEntrySpawn:
    def test_code_execution_entry_runs_in_spawn_child(self):
        """CodeExecutionEntry (was the _make_code_execution_tool closure)
        pickles and executes real code across a spawn boundary."""
        from conductor.ai.agents.code_execution_config import CodeExecutionEntry
        from conductor.ai.agents.code_executor import LocalCodeExecutor

        entry = CodeExecutionEntry(
            LocalCodeExecutor(language="python", timeout=30),
            allowed_languages=["python"],
            allowed_commands=[],
            timeout=30,
        )
        entry_bytes = pickle.dumps(entry)  # closure could never do this

        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        p = ctx.Process(
            target=helpers.run_code_entry_child,
            args=(entry_bytes, "print('spawn-ok')", q),
        )
        p.start()
        try:
            result = q.get(timeout=60)
        finally:
            p.join(timeout=60)
        assert p.exitcode == 0
        assert result["status"] == "success"
        assert "spawn-ok" in result["stdout"]

    def test_as_tool_entry_is_picklable(self):
        from conductor.ai.agents.code_executor import LocalCodeExecutor

        tool_fn = LocalCodeExecutor(language="python", timeout=10).as_tool()
        td = tool_fn._tool_def
        restored = pickle.loads(pickle.dumps(td.func))
        assert restored.executor.language == "python"


# ── System worker entries (Group B) ──────────────────────────────────────


class TestSystemEntries:
    def test_stop_when_entry_async_spawn_roundtrip(self):
        """An async entry (was an async-def closure) crosses spawn and runs."""
        from conductor.ai.agents.runtime._worker_entries import StopWhenEntry

        entry = StopWhenEntry(helpers.stop_after_two)
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        p = ctx.Process(
            target=helpers.run_async_entry_child,
            args=(pickle.dumps(entry), {"result": "r", "iteration": 3}, q),
        )
        p.start()
        try:
            assert q.get(timeout=30) == {"should_continue": False}
        finally:
            p.join(timeout=30)
        assert p.exitcode == 0

    def test_handoff_check_entry_pickles_and_decides(self):
        import asyncio

        from conductor.ai.agents.runtime._worker_entries import HandoffCheckEntry

        entry = HandoffCheckEntry(
            [], {"root": "0", "sub": "1"}, {"0": "root", "1": "sub"},
            allowed={"root": ["sub"]},
        )
        restored = pickle.loads(pickle.dumps(entry))
        out = asyncio.run(restored(is_transfer=True, active_agent="0", transfer_to="sub"))
        assert out == {"active_agent": "1", "handoff": True}
        # Blocked target retries then gives up (per-process instance state).
        blocked = asyncio.run(restored(is_transfer=True, active_agent="1", transfer_to="root"))
        assert blocked == {"active_agent": "1", "handoff": True}  # retry 1 of 3

    def test_callback_entry_rebuilds_chain(self):
        import asyncio

        from conductor.ai.agents.runtime._worker_entries import CallbackEntry

        entry = CallbackEntry("before_model", [], helpers.legacy_before_model, "t_before_model")
        restored = pickle.loads(pickle.dumps(entry))
        out = asyncio.run(restored(messages=[{"role": "user"}]))
        assert out == {"seen": ["messages"]}

    def test_transfer_entries_pickle(self):
        import asyncio

        from conductor.ai.agents.runtime._worker_entries import (
            TransferNoopEntry,
            TransferUnreachableEntry,
        )

        assert asyncio.run(pickle.loads(pickle.dumps(TransferNoopEntry()))()) == {}
        # Echoes the hand-off message so it is visible in the task output.
        assert asyncio.run(pickle.loads(pickle.dumps(TransferNoopEntry()))(message="do X")) == {
            "message": "do X"
        }
        msg = asyncio.run(pickle.loads(pickle.dumps(TransferUnreachableEntry("a_transfer_to_b")))())
        assert "a_transfer_to_b is not available" in msg

    def test_check_transfer_extracts_message(self):
        import asyncio

        from conductor.ai.agents.runtime._worker_entries import CheckTransferEntry

        entry = pickle.loads(pickle.dumps(CheckTransferEntry()))
        out = asyncio.run(
            entry(
                tool_calls=[
                    {
                        "name": "ceo_transfer_to_engineering_lead",
                        "inputParameters": {
                            "method": "ceo_transfer_to_engineering_lead",
                            "message": "Design the REST API",
                        },
                    }
                ]
            )
        )
        assert out == {
            "is_transfer": True,
            "transfer_to": "engineering_lead",
            "transfer_message": "Design the REST API",
        }

    def test_check_transfer_no_transfer_and_missing_message(self):
        import asyncio

        from conductor.ai.agents.runtime._worker_entries import CheckTransferEntry

        entry = CheckTransferEntry()
        assert asyncio.run(entry(tool_calls=None)) == {
            "is_transfer": False,
            "transfer_to": "",
            "transfer_message": "",
        }
        # Transfer without a message arg (older tool schema) → empty message
        out = asyncio.run(
            entry(tool_calls=[{"name": "a_transfer_to_b", "inputParameters": {"method": "x"}}])
        )
        assert out == {"is_transfer": True, "transfer_to": "b", "transfer_message": ""}

    def test_check_transfer_multiple_calls_first_wins_and_reports_dropped(self):
        import asyncio

        from conductor.ai.agents.runtime._worker_entries import CheckTransferEntry

        entry = CheckTransferEntry()
        out = asyncio.run(
            entry(
                tool_calls=[
                    {
                        "name": "ceo_transfer_to_engineering_lead",
                        "inputParameters": {"message": "eng task"},
                    },
                    {
                        "name": "ceo_transfer_to_marketing_lead",
                        "inputParameters": {"message": "mkt task"},
                    },
                ]
            )
        )
        assert out["is_transfer"] is True
        assert out["transfer_to"] == "engineering_lead"
        assert out["transfer_message"] == "eng task"
        assert out["dropped_transfers"] == [
            {"transfer_to": "marketing_lead", "message": "mkt task"}
        ]


# ── Framework worker entries (Group C) ───────────────────────────────────


class TestFrameworkEntries:
    def test_graph_worker_entry_spawn_roundtrip(self):
        """A langgraph node worker crosses a real spawn boundary and executes."""
        from conductor.ai.agents.runtime._worker_entries import GraphWorkerEntry

        entry = GraphWorkerEntry("make_node_worker", helpers.graph_node, "test_node")
        entry_bytes = pickle.dumps(entry)  # the nested worker never pickled

        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        p = ctx.Process(target=helpers.run_graph_entry_child, args=(entry_bytes, q))
        p.start()
        try:
            status, output = q.get(timeout=30)
        finally:
            p.join(timeout=30)
        assert p.exitcode == 0
        assert "COMPLETED" in status
        assert output["state"]["result"] == "node-saw-7"

    def test_passthrough_entry_with_plain_payload_pickles(self):
        from conductor.ai.agents.runtime._worker_entries import PassthroughWorkerEntry

        entry = PassthroughWorkerEntry(
            "conductor.ai.agents.frameworks.claude_agent_sdk",
            "make_claude_agent_sdk_worker_from_config",
            {"system_prompt": "hi", "max_turns": 3},
            "w1", "http://localhost:8085/api", "", "",
        )
        restored = pickle.loads(pickle.dumps(entry))
        assert restored.payload == {"system_prompt": "hi", "max_turns": 3}
        assert restored._worker is None  # memo never pickled

    def test_passthrough_entry_unpicklable_payload_fails_probe(self, force_spawn_probe):
        import threading

        from conductor.ai.agents.runtime._worker_entries import PassthroughWorkerEntry

        entry = PassthroughWorkerEntry(
            "conductor.ai.agents.frameworks.langchain",
            "make_langchain_worker",
            threading.Lock(),  # stands in for a live executor/compiled graph
            "w2", "url", "", "",
        )
        with pytest.raises(SpawnSafetyError, match="not spawn-safe"):
            probe_spawn_safety(entry, "w2", group="framework")

    def test_claude_options_config_rejects_callables(self):
        claude_sdk = pytest.importorskip("claude_code_sdk")
        from conductor.ai.agents.frameworks.claude_agent_sdk import (
            claude_options_to_plain_config,
        )

        options = claude_sdk.ClaudeCodeOptions(
            system_prompt="x", can_use_tool=lambda *a: True
        )
        with pytest.raises(SpawnSafetyError, match="can_use_tool"):
            claude_options_to_plain_config(options)

    def test_claude_options_config_roundtrip(self):
        claude_sdk = pytest.importorskip("claude_code_sdk")
        from conductor.ai.agents.frameworks.claude_agent_sdk import (
            claude_options_to_plain_config,
        )

        options = claude_sdk.ClaudeCodeOptions(system_prompt="x", max_turns=2)
        config = claude_options_to_plain_config(options)
        assert "debug_stderr" not in config  # child re-defaults its own stderr
        assert config["system_prompt"] == "x" and config["max_turns"] == 2
        pickle.dumps(config)  # the whole point
        rebuilt = claude_sdk.ClaudeCodeOptions(**config)
        assert rebuilt.system_prompt == "x"


@pytest.fixture
def force_spawn_probe(monkeypatch):
    """Pin the probe's start-method check to 'spawn'."""
    monkeypatch.setattr(
        we.multiprocessing, "get_start_method", lambda allow_none=True: "spawn"
    )


class TestUserCallablePolicy:
    """Design §7: lambdas fail fast at registration with a named offender."""

    def test_lambda_callback_fails_fast_at_registration(self, force_spawn_probe):
        from conductor.ai.agents.runtime._worker_entries import CallbackEntry

        entry = CallbackEntry("before_model", [], lambda **kw: {}, "t_before_model")
        with pytest.raises(SpawnSafetyError, match="not spawn-safe"):
            probe_spawn_safety(entry, "t_before_model", group="system")

    def test_module_level_callback_passes_probe(self, force_spawn_probe):
        from conductor.ai.agents.runtime._worker_entries import CallbackEntry

        entry = CallbackEntry("before_model", [], helpers.legacy_before_model, "t")
        probe_spawn_safety(entry, "t", group="system")  # no raise


# ── Registration-time probe ──────────────────────────────────────────────


class TestProbe:
    def test_probe_noop_when_group_disabled(self):
        # Ships with no groups enabled — even a lambda passes silently.
        probe_spawn_safety(lambda x: x, "t", group="not-enabled")

    def test_probe_rejects_closure_when_enabled(self, monkeypatch, force_spawn_probe):
        monkeypatch.setattr(we, "_ENABLED_PROBE_GROUPS", frozenset({"tools"}))

        def nested(x):
            return x

        with pytest.raises(SpawnSafetyError, match="not spawn-safe"):
            probe_spawn_safety(nested, "nested_task", group="tools")

    def test_probe_accepts_module_level_fn_when_enabled(self, monkeypatch, force_spawn_probe):
        monkeypatch.setattr(we, "_ENABLED_PROBE_GROUPS", frozenset({"tools"}))
        probe_spawn_safety(helpers.plain_sample, "plain_task", group="tools")

    def test_probe_accepts_picklable_instance_when_enabled(self, monkeypatch, force_spawn_probe):
        monkeypatch.setattr(we, "_ENABLED_PROBE_GROUPS", frozenset({"tools"}))
        probe_spawn_safety(helpers.SyncCallEntry(3), "entry_task", group="tools")


# ── Async detection (task_handler fix) ───────────────────────────────────


class TestAsyncDetection:
    def test_plain_sync_function(self):
        assert _is_async_execute_callable(helpers.plain_sample) is False

    def test_plain_async_function(self):
        assert _is_async_execute_callable(helpers.async_sample) is True

    def test_instance_with_async_call(self):
        assert _is_async_execute_callable(helpers.AsyncCallEntry(1)) is True

    def test_instance_with_sync_call(self):
        assert _is_async_execute_callable(helpers.SyncCallEntry(1)) is False
