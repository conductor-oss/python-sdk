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


# ── Registration-time spawn probe ────────────────────────────────────────
#
# Groups are enabled stage-by-stage as each worker family is converted to a
# spawn-safe form (idea-5 implementation plan): probing an unconverted group
# would fail every registration immediately.
_ENABLED_PROBE_GROUPS: FrozenSet[str] = frozenset()


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
