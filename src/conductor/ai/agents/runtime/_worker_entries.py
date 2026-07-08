# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Spawn-safe worker entry infrastructure.

Under the multiprocessing ``spawn`` start method (the SDK default on every
platform — see ``conductor.client.automator.task_handler``), every worker
handed to a ``Process`` is pickled at ``start()``. That imposes two rules the
agent runtime historically violated:

1. The worker callable must be resolvable by importable qualified name (no
   closures, no reassigned ``__name__``/``__qualname__``).
2. Any state the worker needs at execution time must travel *with* the worker
   — spawn children re-import modules fresh, so parent-populated module
   registries (``_dispatch._tool_def_registry`` etc.) are empty in the child.

This module provides the building blocks for spawn-safe workers:

- :class:`FunctionRef` — a picklable ``(module, qualname, unwrap_depth)``
  reference to a module-level function, resolved (and memoized) in the child.
- :class:`SpawnSafetyError` — raised at *registration* time with an
  actionable message, instead of an opaque ``PicklingError`` at process start.
- :func:`probe_spawn_safety` — a registration-time pickle probe, enabled per
  worker group as each group's workers become spawn-safe.

Design: idea-5 ``design.md`` in the combine-agentspan analysis workspace.

NOTE: deliberately NO ``from __future__ import annotations`` here — the task
runners read parameter types from ``inspect.signature(execute_function)``
(the class ``__call__``'s annotations for entry instances) and pass them to
``isinstance``-based input conversion; string annotations would break that
(``TypeError: isinstance() arg 2 must be a type``).
"""

import importlib
import inspect
import multiprocessing
import pickle
import sys
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet

# Mirrors conductor.client.worker.worker._MAX_UNWRAP_DEPTH.
_MAX_UNWRAP_DEPTH = 32

_REMEDIES = (
    "Define the callable at module level (importable by qualified name)."
)


class SpawnSafetyError(RuntimeError):
    """A worker (or a callable it needs) cannot cross a spawn process boundary.

    Raised at registration time so the offending callable is named while the
    user's stack frame is still on the call path — not 30 minutes later as a
    ``PicklingError`` inside ``TaskHandler.start_processes``.
    """


def _walk_qualname(module_obj, qualname: str):
    """getattr-walk ``qualname`` parts from a module object."""
    obj = module_obj
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return obj


# Per-process memo of resolved refs — repopulated naturally in each spawn
# child on first use (this is process-local state, never pickled).
_RESOLVE_CACHE: Dict["FunctionRef", Callable] = {}


@dataclass(frozen=True)
class FunctionRef:
    """Picklable reference to a module-level function.

    ``unwrap_depth`` counts ``__wrapped__`` hops from the module global down
    to the referenced function — e.g. 1 for a ``@tool``-decorated function,
    where the module global is the ``functools.wraps`` wrapper and
    ``ToolDef.func`` is the original underneath it.
    """

    module: str
    qualname: str
    unwrap_depth: int = 0

    @classmethod
    def of(cls, fn: Callable) -> "FunctionRef":
        """Build a ref for *fn*, or raise :class:`SpawnSafetyError`.

        Only plain functions qualify: callable instances should be pickled by
        value instead (module-level class + picklable attrs), and lambdas /
        nested functions / bound methods have no importable qualified name.
        """
        if not inspect.isfunction(fn):
            raise SpawnSafetyError(
                f"{fn!r} is not a plain function and cannot be referenced by "
                f"qualified name. {_REMEDIES}"
            )
        module = getattr(fn, "__module__", None)
        qualname = getattr(fn, "__qualname__", None)
        if not module or not qualname:
            raise SpawnSafetyError(f"{fn!r} has no module/qualname. {_REMEDIES}")
        if "<locals>" in qualname or "<lambda>" in qualname:
            raise SpawnSafetyError(
                f"'{qualname}' ({module}) is a lambda or is defined inside a "
                f"function, so a spawn child cannot import it. {_REMEDIES}"
            )
        module_obj = sys.modules.get(module)
        if module_obj is None:
            raise SpawnSafetyError(
                f"module '{module}' for '{qualname}' is not imported. {_REMEDIES}"
            )
        try:
            obj = _walk_qualname(module_obj, qualname)
        except AttributeError:
            raise SpawnSafetyError(
                f"'{qualname}' is not reachable in module '{module}' — its "
                f"name was rebound or deleted. {_REMEDIES}"
            ) from None
        if obj is fn:
            return cls(module, qualname, 0)
        # The global was rebound (typically by a wrapping decorator like
        # @tool). Walk the __wrapped__ chain to find fn, recording the depth.
        depth, current = 0, obj
        while hasattr(current, "__wrapped__") and depth < _MAX_UNWRAP_DEPTH:
            current = current.__wrapped__
            depth += 1
            if current is fn:
                return cls(module, qualname, depth)
        raise SpawnSafetyError(
            f"'{module}.{qualname}' does not resolve back to {fn!r} (rebound "
            f"without a __wrapped__ chain). {_REMEDIES}"
        )

    def resolve(self) -> Callable:
        """Import + walk + unwrap; memoized per process."""
        cached = _RESOLVE_CACHE.get(self)
        if cached is not None:
            return cached
        module_obj = importlib.import_module(self.module)
        obj = _walk_qualname(module_obj, self.qualname)
        for _ in range(self.unwrap_depth):
            obj = obj.__wrapped__
        _RESOLVE_CACHE[self] = obj
        return obj


# ── Worker entries ───────────────────────────────────────────────────────


class ToolWorkerEntry:
    """Spawn-safe replacement for ``make_tool_worker``'s nested ``tool_worker``.

    Pickles by value (module-level class + picklable attrs) — no closure, no
    identity spoof. The tool callable travels either as a :class:`FunctionRef`
    (module-level functions) or directly (``fn_direct``) for picklable
    callable instances and — under ``fork``, where nothing is pickled — legacy
    closures. Credential names are resolved at registration and carried here,
    because the parent's ``_dispatch`` registries are empty in spawn children.
    """

    def __init__(self, tool_name, fn_ref=None, fn_direct=None, guardrails=None,
                 credential_names=None, framework_callable=False):
        if (fn_ref is None) == (fn_direct is None):
            raise ValueError("exactly one of fn_ref/fn_direct is required")
        self.tool_name = tool_name
        self.fn_ref = fn_ref
        self.fn_direct = fn_direct
        self.guardrails = guardrails
        self.credential_names = list(credential_names) if credential_names else []
        # Carried explicitly: the parent sets _agentspan_framework_callable on
        # the function object, which a spawn child's re-imported copy lacks.
        self.framework_callable = framework_callable

    @classmethod
    def for_callable(cls, fn, tool_name, guardrails=None, credential_names=None):
        """Build an entry for *fn*, preferring by-reference transport.

        Falls back to direct transport for picklable callables (instances,
        bound methods of picklable objects); unpicklable closures are caught
        by the registration probe with an actionable error.
        """
        framework = bool(getattr(fn, "_agentspan_framework_callable", False))
        try:
            ref = FunctionRef.of(fn)
        except SpawnSafetyError:
            entry = cls(tool_name, fn_direct=fn, guardrails=guardrails,
                        credential_names=credential_names, framework_callable=framework)
        else:
            entry = cls(tool_name, fn_ref=ref, guardrails=guardrails,
                        credential_names=credential_names, framework_callable=framework)
        # Introspection compatibility (logging etc.). Plain string INSTANCE
        # attrs — unlike the old wrapper's reassigned function identity, these
        # don't participate in pickling-by-reference, so they can't break it.
        entry.__name__ = getattr(fn, "__name__", tool_name)
        entry.__qualname__ = getattr(fn, "__qualname__", tool_name)
        entry.__doc__ = getattr(fn, "__doc__", None)
        return entry

    def _target(self) -> Callable:
        return self.fn_ref.resolve() if self.fn_ref is not None else self.fn_direct

    def __call__(self, task):
        # Late import: _dispatch owns the execution helpers; importing it here
        # (not at module top) avoids an import cycle and works in the child.
        from conductor.ai.agents.runtime._dispatch import run_tool_task

        return run_tool_task(
            task,
            tool_name=self.tool_name,
            tool_func=self._target(),
            guardrails=self.guardrails,
            credential_names=self.credential_names,
            framework_callable=self.framework_callable,
        )


# ── User-callable transport helpers ──────────────────────────────────────


def wrap_callable(fn):
    """Best transport for a user callable: FunctionRef when resolvable, raw otherwise.

    Raw transport works for picklable callables (instances with plain-data
    attrs, bound methods of picklable objects); anything else is caught by the
    registration probe with an actionable error.
    """
    if fn is None:
        return None
    try:
        return FunctionRef.of(fn)
    except SpawnSafetyError:
        return fn


def unwrap_callable(x):
    return x.resolve() if isinstance(x, FunctionRef) else x


def _stringify_content(content) -> str:
    """Shared guardrail-content normalization (was duplicated in both closures)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    import json as _json

    try:
        return _json.dumps(content, default=str)
    except (TypeError, ValueError):
        return str(content)


# ── System worker entries (Group B — nested closures in AgentRuntime._register_*) ──
#
# Each replaces an `async def` closure with a picklable module-level class.
# `_call_user_fn` / `_resolve_loop_iteration` are imported lazily inside the
# calls: they live in runtime.py, which imports this module at registration
# time (top-level import here would be a cycle), and lazy import also works
# in the spawn child.


class GuardrailEntry:
    """One output guardrail (was ``guardrail_worker``)."""

    def __init__(self, func, name, on_fail, max_retries):
        self.func_t = wrap_callable(func)
        self.name = name
        self.on_fail = on_fail
        self.max_retries = max_retries

    async def _check(self, content_str, iteration):
        from conductor.ai.agents.runtime.runtime import _call_user_fn

        try:
            result = await _call_user_fn(unwrap_callable(self.func_t), content_str)
            if not result.passed:
                on_fail = self.on_fail
                fixed_output = getattr(result, "fixed_output", None)
                if on_fail == "retry" and iteration >= self.max_retries:
                    on_fail = "raise"
                if on_fail == "fix" and fixed_output is None:
                    on_fail = "raise"
                return {
                    "passed": False,
                    "message": result.message,
                    "on_fail": on_fail,
                    "fixed_output": fixed_output,
                    "guardrail_name": self.name,
                    "should_continue": on_fail == "retry",
                }
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                "Guardrail '%s' raised exception: %s", self.name, e
            )
            on_fail = self.on_fail
            if on_fail == "retry" and iteration >= self.max_retries:
                on_fail = "raise"
            return {
                "passed": False,
                "message": f"Guardrail error: {e}",
                "on_fail": on_fail,
                "fixed_output": None,
                "guardrail_name": self.name,
                "should_continue": on_fail == "retry",
            }
        return None

    async def __call__(self, content: object = None, iteration: int = 0) -> object:
        from conductor.ai.agents.runtime.runtime import _resolve_loop_iteration

        iteration = _resolve_loop_iteration(iteration)
        failure = await self._check(_stringify_content(content), iteration)
        if failure is not None:
            return failure
        return {
            "passed": True,
            "message": "",
            "on_fail": "pass",
            "fixed_output": None,
            "guardrail_name": "",
            "should_continue": False,
        }


class CombinedGuardrailEntry:
    """All of an agent's output guardrails in order (was ``combined_guardrail_worker``)."""

    def __init__(self, guardrails):
        self.entries = [
            GuardrailEntry(g.func, g.name, g.on_fail, g.max_retries) for g in guardrails
        ]

    async def __call__(self, content: object = None, iteration: int = 0) -> object:
        from conductor.ai.agents.runtime.runtime import _resolve_loop_iteration

        iteration = _resolve_loop_iteration(iteration)
        content_str = _stringify_content(content)
        for entry in self.entries:
            failure = await entry._check(content_str, iteration)
            if failure is not None:
                return failure
        return {
            "passed": True,
            "message": "",
            "on_fail": "pass",
            "fixed_output": None,
            "guardrail_name": "",
            "should_continue": False,
        }


class StopWhenEntry:
    """Loop stop predicate (was ``stop_when_worker``)."""

    def __init__(self, stop_when_fn):
        self.fn_t = wrap_callable(stop_when_fn)

    async def __call__(self, result: object = "", iteration: int = 0,
                       messages: object = None) -> object:
        from conductor.ai.agents.runtime.runtime import _call_user_fn, _resolve_loop_iteration

        iteration = _resolve_loop_iteration(iteration)
        context = {"result": result, "messages": messages or [], "iteration": iteration}
        try:
            should_stop = await _call_user_fn(unwrap_callable(self.fn_t), context)
            return {"should_continue": not should_stop}
        except Exception as e:
            import logging

            logging.getLogger(__name__).error("stop_when evaluation failed: %s", e)
            return {"should_continue": True}


class GateEntry:
    """Sequential-pipeline gate predicate (was ``gate_worker``)."""

    def __init__(self, gate_fn):
        self.fn_t = wrap_callable(gate_fn)

    async def __call__(self, result: str = "") -> object:
        from conductor.ai.agents.runtime.runtime import _call_user_fn

        try:
            output = {"result": result}
            should_continue = await _call_user_fn(unwrap_callable(self.fn_t), output)
            return {"decision": "continue" if should_continue else "stop"}
        except Exception as e:
            import logging

            logging.getLogger(__name__).error("Gate evaluation failed: %s", e)
            return {"decision": "continue"}  # safe fallback


class CallbackEntry:
    """Position callback worker (was ``callback_worker``).

    Carries the CallbackHandler instances (by value) and the legacy callable
    (by reference where possible) instead of the unpicklable ``chained``
    closure; the chain is rebuilt per call via
    ``_chain_callbacks_for_position``.
    """

    def __init__(self, position, handlers, legacy_fn, task_name):
        self.position = position
        self.handlers = list(handlers or [])
        self.legacy_t = wrap_callable(legacy_fn)
        self.task_name = task_name

    async def __call__(self, messages: object = None, llm_result: str = None) -> object:
        from conductor.ai.agents.callback import _chain_callbacks_for_position
        from conductor.ai.agents.runtime.runtime import _call_user_fn

        try:
            chained = _chain_callbacks_for_position(
                self.position, self.handlers, unwrap_callable(self.legacy_t)
            )
            if chained is None:
                return {}
            kwargs = {}
            if messages is not None:
                kwargs["messages"] = messages
            if llm_result is not None:
                kwargs["llm_result"] = llm_result
            result = await _call_user_fn(chained, **kwargs)
            return result if isinstance(result, dict) else {}
        except Exception as e:
            import logging

            logging.getLogger(__name__).error("Callback %s failed: %s", self.task_name, e)
            return {}


class TerminationEntry:
    """Termination-condition worker (was ``termination_worker``)."""

    def __init__(self, termination_cond):
        self.cond = termination_cond  # by value; conditions are plain-data classes

    async def __call__(self, result: str = "", iteration: int = 0) -> object:
        from conductor.ai.agents.runtime.runtime import _call_user_fn, _resolve_loop_iteration

        iteration = _resolve_loop_iteration(iteration)
        context = {"result": result, "messages": [], "iteration": iteration}
        try:
            outcome = await _call_user_fn(self.cond.should_terminate, context)
            return {"should_continue": not outcome.should_terminate, "reason": outcome.reason}
        except Exception as e:
            import logging

            logging.getLogger(__name__).error("termination condition evaluation failed: %s", e)
            return {"should_continue": True, "reason": ""}


class CheckTransferEntry:
    """Detect transfer tool calls (was ``check_transfer_worker``; stateless)."""

    async def __call__(self, tool_calls: object = None, _unused: str = "") -> object:
        for tc in tool_calls or []:
            name = tc.get("name", "")
            if "_transfer_to_" in name:
                return {"is_transfer": True, "transfer_to": name.split("_transfer_to_", 1)[1]}
        return {"is_transfer": False, "transfer_to": ""}


class TransferNoopEntry:
    """No-op transfer tool (was the nested ``transfer_worker``; handoff is
    detected by check_transfer from toolCalls output)."""

    async def __call__(self) -> object:
        return {}


class TransferUnreachableEntry:
    """Transfer tool for a target unreachable via allowed_transitions."""

    def __init__(self, tool_name):
        self.tool_name = tool_name

    async def __call__(self) -> str:
        return (
            f"ERROR: {self.tool_name} is not available. "
            f"Use a different transfer tool, or if you are "
            f"done, just provide your final response without "
            f"calling any transfer tool."
        )


class RouterEntry:
    """Function-based router (was ``router_worker``)."""

    def __init__(self, router_fn, agent_names):
        self.fn_t = wrap_callable(router_fn)
        self.agent_names = list(agent_names)

    async def __call__(self, prompt: str = "") -> object:
        from conductor.ai.agents.runtime.runtime import _call_user_fn

        try:
            result = await _call_user_fn(unwrap_callable(self.fn_t), prompt)
            return {"selected_agent": str(result)}
        except Exception as e:
            import logging

            logging.getLogger(__name__).error("Router function failed: %s", e)
            return {"selected_agent": self.agent_names[0] if self.agent_names else ""}


class HandoffCheckEntry:
    """Swarm handoff decision (was ``handoff_check_worker``).

    ``blocked_counts`` is instance state — per worker process, exactly the
    closure-cell semantics it replaces. HandoffConditions travel by value
    (``OnCondition`` lambdas are fork-only; the probe polices that).
    """

    def __init__(self, handoff_conditions, name_to_idx, idx_to_name, allowed,
                 max_blocked_retries=3):
        self.handoff_conditions = list(handoff_conditions or [])
        self.name_to_idx = dict(name_to_idx)
        self.idx_to_name = dict(idx_to_name)
        self.allowed = allowed
        self.max_blocked_retries = max_blocked_retries
        self.blocked_counts = {}

    @staticmethod
    def _is_transfer_truthy(val: object) -> bool:
        if val is True:
            return True
        if isinstance(val, str):
            return val.strip().lower() == "true"
        return False

    def _is_allowed(self, source_idx: str, target_name: str) -> bool:
        """Check if transition is allowed. No constraints → allow all."""
        if not self.allowed:
            return True
        source_name = self.idx_to_name.get(source_idx, "")
        return target_name in self.allowed.get(source_name, [])

    async def __call__(
        self,
        result: str = "",
        active_agent: str = "0",
        conversation: str = "",
        is_transfer: object = False,
        transfer_to: str = "",
    ) -> object:
        # Priority 1: Transfer tool detected
        if self._is_transfer_truthy(is_transfer):
            if self._is_allowed(active_agent, transfer_to):
                self.blocked_counts.pop(active_agent, None)
                target_idx = self.name_to_idx.get(transfer_to, active_agent)
                if target_idx != active_agent:
                    return {"active_agent": target_idx, "handoff": True}
            elif self.allowed:
                # Transfer blocked — give the agent a few retries to
                # self-correct, then exit the loop.
                count = self.blocked_counts.get(active_agent, 0) + 1
                self.blocked_counts[active_agent] = count
                if count <= self.max_blocked_retries:
                    return {"active_agent": active_agent, "handoff": True}
                # Max retries exceeded — exit the loop
                self.blocked_counts.pop(active_agent, None)
                return {"active_agent": active_agent, "handoff": False}

        # Priority 2: Condition-based handoffs (fallback)
        context = {
            "result": result,
            "messages": conversation,
            "tool_name": "",
            "tool_result": "",
        }
        for cond in self.handoff_conditions:
            if cond.should_handoff(context):
                if self._is_allowed(active_agent, cond.target):
                    target_idx = self.name_to_idx.get(cond.target, active_agent)
                    if target_idx != active_agent:
                        return {"active_agent": target_idx, "handoff": True}

        # Neither transfer nor condition → loop exits
        return {"active_agent": active_agent, "handoff": False}


class ProcessSelectionEntry:
    """Manual-strategy selection mapper (was ``process_selection_worker``)."""

    def __init__(self, name_to_idx):
        self.name_to_idx = dict(name_to_idx)

    async def __call__(self, human_output: object = None) -> object:
        if human_output is None:
            return {"selected": "0"}
        if isinstance(human_output, dict):
            selected = human_output.get("selected", human_output.get("agent", "0"))
            if selected in self.name_to_idx:
                return {"selected": self.name_to_idx[selected]}
            return {"selected": str(selected)}
        return {"selected": str(human_output)}


# ── Registration-time spawn probe ────────────────────────────────────────
#
# Groups are enabled stage-by-stage as each worker family is converted to a
# spawn-safe form (idea-5 implementation plan): probing an unconverted group
# would fail every registration immediately.
# - "tools": make_tool_worker/ToolWorkerEntry (native @tool, skill workers,
#   framework-extracted) — converted in Stage 2.
# - "system": AgentRuntime._register_* control workers (guardrails, callbacks,
#   termination, transfer, router, handoff, selection) — converted in Stage 3.
_ENABLED_PROBE_GROUPS: FrozenSet[str] = frozenset({"tools", "system"})


def _spawn_probe_active(group: str) -> bool:
    if group not in _ENABLED_PROBE_GROUPS:
        return False
    # None = not yet set; task_handler's import-time default makes it spawn.
    method = multiprocessing.get_start_method(allow_none=True) or "spawn"
    return method in ("spawn", "forkserver")


def probe_spawn_safety(execute_fn: Callable, task_name: str, *, group: str) -> None:
    """Pickle-probe a prospective worker at registration time.

    Builds a throwaway ``Worker`` (cheap — the ApiClient is lazy) and
    ``pickle.dumps`` it, converting any failure into a
    :class:`SpawnSafetyError` that names the worker. No-op under ``fork`` and
    for groups not yet converted.
    """
    if not _spawn_probe_active(group):
        return
    from conductor.client.worker.worker import Worker

    try:
        pickle.dumps(Worker(task_definition_name=task_name, execute_function=execute_fn))
    except Exception as e:
        raise SpawnSafetyError(
            f"worker '{task_name}' is not spawn-safe ({e!r}). {_REMEDIES}"
        ) from e
