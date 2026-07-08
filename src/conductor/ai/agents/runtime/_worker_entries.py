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
"""

from __future__ import annotations

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
    "Define the callable at module level (importable by qualified name), "
    "or run with CONDUCTOR_MP_START_METHOD=fork (compatibility mode; see the "
    "start-method notes in conductor.client.automator.task_handler)."
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

        Falls back to direct transport for callable instances (picklable by
        value) and for closures — the latter only work under ``fork``; the
        registration probe polices that under ``spawn``.
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


# ── Registration-time spawn probe ────────────────────────────────────────
#
# Groups are enabled stage-by-stage as each worker family is converted to a
# spawn-safe form (idea-5 implementation plan): probing an unconverted group
# would fail every registration immediately.
# - "tools": make_tool_worker/ToolWorkerEntry (native @tool, skill workers,
#   framework-extracted) — converted in Stage 2.
_ENABLED_PROBE_GROUPS: FrozenSet[str] = frozenset({"tools"})


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
