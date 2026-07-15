# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Worker isolation mode — ``process`` (default) or ``thread``.

``CONDUCTOR_WORKER_ISOLATION=thread`` replaces :class:`TaskHandler`'s
multiprocessing primitives (``Process``, ``Queue``) with thread equivalents.
For environments where multiprocessing's fork+exec bootstraps (spawn
children, ``resource_tracker``) fail — e.g. minimal microVM guests. Threads
share the parent's memory, so the log relay needs no IPC and worker payloads
need no pickling.

The default (``process``, or the variable unset) leaves every existing code
path untouched: ``multiprocessing.Process`` under the ``spawn`` start method.

Tradeoffs (thread mode only): no per-worker force-kill (``terminate``/``kill``
are no-ops; shutdown is cooperative), CPU-bound workers share the GIL, and
``signal.signal`` becomes a no-op off the main thread instead of raising
``ValueError``.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
from typing import Any

logger = logging.getLogger(__name__)

WORKER_ISOLATION_ENV = "CONDUCTOR_WORKER_ISOLATION"
ISOLATION_PROCESS = "process"
ISOLATION_THREAD = "thread"
_VALID_MODES = frozenset({ISOLATION_PROCESS, ISOLATION_THREAD})

_invalid_mode_warned = False


def isolation_mode() -> str:
    """Return the configured worker isolation mode.

    Reads ``CONDUCTOR_WORKER_ISOLATION`` (case-insensitive, whitespace
    trimmed). Invalid values warn once and fall back to ``process`` — failing
    open to the default behavior rather than bricking every worker on a typo.
    """
    global _invalid_mode_warned
    raw = os.environ.get(WORKER_ISOLATION_ENV, "")
    mode = raw.strip().lower() or ISOLATION_PROCESS
    if mode not in _VALID_MODES:
        if not _invalid_mode_warned:
            logger.warning(
                "Ignoring invalid %s=%r; valid values are %s; using %r",
                WORKER_ISOLATION_ENV,
                raw,
                sorted(_VALID_MODES),
                ISOLATION_PROCESS,
            )
            _invalid_mode_warned = True
        mode = ISOLATION_PROCESS
    return mode


class _ThreadAsProcess(threading.Thread):
    """threading.Thread shim that satisfies the multiprocessing.Process interface."""

    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None
    ):
        super().__init__(
            group=group, target=target, name=name, args=args, kwargs=kwargs or {}, daemon=daemon
        )
        self.exitcode: Any = None

    def terminate(self) -> None:
        pass

    def kill(self) -> None:
        pass

    @property
    def pid(self) -> None:
        return None


def apply_thread_isolation() -> None:
    """Swap ``task_handler``'s multiprocessing primitives for thread equivalents.

    Idempotent. Must run before the first :class:`TaskHandler` is constructed:
    its ``__init__`` creates the logging ``Queue`` and starts the logger
    ``Process`` immediately.
    """
    from conductor.client.automator import task_handler as _th_module  # lazy: no import cycle

    if getattr(_th_module, "_thread_isolation_applied", False):
        return

    _th_module.Process = _ThreadAsProcess  # type: ignore[attr-defined]

    # With every worker a thread, the log relay is same-process: a plain
    # thread-safe queue replaces the IPC Queue, whose SemLock would drag in
    # the resource_tracker bootstrap this mode exists to avoid.
    _th_module.Queue = queue.Queue  # type: ignore[attr-defined]

    # The worker/logger process targets call signal.signal(SIGINT, SIG_IGN)
    # at startup — valid in a child process but a ValueError in a non-main
    # thread. Make signal.signal skip silently off the main thread.
    import signal as _signal_mod

    _orig_signal_fn = _signal_mod.signal

    def _thread_safe_signal(signalnum, handler):
        if threading.current_thread() is threading.main_thread():
            return _orig_signal_fn(signalnum, handler)
        # Non-main thread: skip silently

    _signal_mod.signal = _thread_safe_signal  # type: ignore[assignment]

    _th_module._thread_isolation_applied = True  # type: ignore[attr-defined]
