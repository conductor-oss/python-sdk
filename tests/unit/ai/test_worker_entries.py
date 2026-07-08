# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""FunctionRef / SpawnSafetyError / probe / async-detection tests (idea-5 Stage 1).

Cross-process cases use the real 'spawn' context regardless of platform
default, so they exercise exactly what CI's Linux runners and macOS both do.
"""

import multiprocessing
import pickle

import pytest

from conductor.ai.agents.runtime import _worker_entries as we
from conductor.ai.agents.runtime._worker_entries import (
    FunctionRef,
    SpawnSafetyError,
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


# ── Registration-time probe ──────────────────────────────────────────────


class TestProbe:
    def test_probe_noop_when_group_disabled(self):
        # Ships with no groups enabled — even a lambda passes silently.
        probe_spawn_safety(lambda x: x, "t", group="not-enabled")

    def test_probe_rejects_closure_when_enabled(self, monkeypatch):
        monkeypatch.setattr(we, "_ENABLED_PROBE_GROUPS", frozenset({"tools"}))

        def nested(x):
            return x

        with pytest.raises(SpawnSafetyError, match="not spawn-safe"):
            probe_spawn_safety(nested, "nested_task", group="tools")

    def test_probe_accepts_module_level_fn_when_enabled(self, monkeypatch):
        monkeypatch.setattr(we, "_ENABLED_PROBE_GROUPS", frozenset({"tools"}))
        probe_spawn_safety(helpers.plain_sample, "plain_task", group="tools")

    def test_probe_accepts_picklable_instance_when_enabled(self, monkeypatch):
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
