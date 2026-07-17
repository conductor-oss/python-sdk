"""Unit tests for conductor.client.automator.worker_isolation.

Every test that applies the patch restores the touched globals afterwards
(task_handler.Process / task_handler.Queue, signal.signal, the idempotency
flag): other suites — e.g. test_task_handler.test_start_processes — assert
against the real multiprocessing primitives and must not see a patched world.
"""

import multiprocessing
import queue
import signal
import threading
from unittest.mock import Mock, patch

import pytest

from conductor.client.automator import task_handler, worker_isolation
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.automator.task_runner import TaskRunner
from conductor.client.configuration.configuration import Configuration
from tests.unit.resources.workers import ClassWorker
from conductor.client.automator.worker_isolation import (
    ISOLATION_PROCESS,
    ISOLATION_THREAD,
    WORKER_ISOLATION_ENV,
    _ThreadAsProcess,
    apply_thread_isolation,
    isolation_mode,
)


@pytest.fixture
def restore_globals():
    """Snapshot and restore everything apply_thread_isolation() mutates."""
    orig_process = task_handler.Process
    orig_queue = task_handler.Queue
    orig_signal = signal.signal
    had_flag = getattr(task_handler, "_thread_isolation_applied", False)
    orig_warned = worker_isolation._invalid_mode_warned
    yield
    task_handler.Process = orig_process
    task_handler.Queue = orig_queue
    signal.signal = orig_signal
    if had_flag:
        task_handler._thread_isolation_applied = True
    elif hasattr(task_handler, "_thread_isolation_applied"):
        del task_handler._thread_isolation_applied
    worker_isolation._invalid_mode_warned = orig_warned


# ── isolation_mode() ─────────────────────────────────────────────────────────


def test_default_when_unset(monkeypatch):
    monkeypatch.delenv(WORKER_ISOLATION_ENV, raising=False)
    assert isolation_mode() == ISOLATION_PROCESS


def test_explicit_process(monkeypatch):
    monkeypatch.setenv(WORKER_ISOLATION_ENV, "process")
    assert isolation_mode() == ISOLATION_PROCESS


def test_thread_case_insensitive_and_trimmed(monkeypatch):
    for value in ("thread", "THREAD", "  Thread  "):
        monkeypatch.setenv(WORKER_ISOLATION_ENV, value)
        assert isolation_mode() == ISOLATION_THREAD


def test_empty_value_means_default(monkeypatch):
    monkeypatch.setenv(WORKER_ISOLATION_ENV, "   ")
    assert isolation_mode() == ISOLATION_PROCESS


def test_invalid_value_warns_once_and_falls_back(monkeypatch, caplog, restore_globals):
    worker_isolation._invalid_mode_warned = False
    monkeypatch.setenv(WORKER_ISOLATION_ENV, "threads")
    with caplog.at_level("WARNING", logger=worker_isolation.logger.name):
        assert isolation_mode() == ISOLATION_PROCESS
        assert isolation_mode() == ISOLATION_PROCESS  # second call: no new warning
    warnings = [r for r in caplog.records if WORKER_ISOLATION_ENV in r.getMessage()]
    assert len(warnings) == 1
    assert "threads" in warnings[0].getMessage()


# ── default world (G1, module level) ─────────────────────────────────────────


def test_module_import_has_no_side_effects():
    """Importing worker_isolation must not patch anything by itself."""
    assert task_handler.Process is multiprocessing.Process
    assert task_handler.Queue is multiprocessing.Queue
    assert not getattr(task_handler, "_thread_isolation_applied", False)


# ── apply_thread_isolation() ─────────────────────────────────────────────────


def test_apply_swaps_process_and_queue(restore_globals):
    apply_thread_isolation()
    assert task_handler.Process is _ThreadAsProcess
    assert task_handler.Queue is queue.Queue
    assert task_handler._thread_isolation_applied is True


def test_apply_is_idempotent(restore_globals):
    apply_thread_isolation()
    signal_after_first = signal.signal
    apply_thread_isolation()
    # A second call must not re-wrap signal.signal (or anything else).
    assert signal.signal is signal_after_first
    assert task_handler.Process is _ThreadAsProcess


def test_signal_noop_off_main_thread(restore_globals):
    apply_thread_isolation()

    # Off the main thread: the exact call every worker target makes at
    # startup must not raise ValueError.
    errors = []

    def target():
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    t = threading.Thread(target=target)
    t.start()
    t.join()
    assert errors == []

    # On the main thread: still delegates to the real signal.signal.
    current = signal.getsignal(signal.SIGINT)
    assert signal.signal(signal.SIGINT, current) is current


# ── _ThreadAsProcess shim interface ──────────────────────────────────────────


def test_shim_satisfies_process_interface():
    ran = threading.Event()
    p = _ThreadAsProcess(target=ran.set, daemon=True)
    assert p.pid is None
    assert p.exitcode is None
    p.start()
    p.join(timeout=5)
    assert ran.is_set()
    assert not p.is_alive()
    # Process-interface methods exist and are safe no-ops.
    p.terminate()
    p.kill()


def test_shim_passes_args_and_kwargs():
    seen = {}

    def target(a, b=None):
        seen["a"] = a
        seen["b"] = b

    p = _ThreadAsProcess(target=target, args=(1,), kwargs={"b": 2}, daemon=True)
    p.start()
    p.join(timeout=5)
    assert seen == {"a": 1, "b": 2}


# ── TaskHandler gate (G2 / G5) ───────────────────────────────────────────────


def _stop_logger(th):
    """End the logger thread via its None sentinel (same as the SDK's atexit)."""
    th.queue.put(None)
    th.logger_process.join(timeout=2)


def test_task_handler_construction_applies_thread_isolation(monkeypatch, restore_globals):
    monkeypatch.setenv(WORKER_ISOLATION_ENV, "thread")
    th = TaskHandler(
        configuration=Configuration(),
        workers=[],
        scan_for_annotated_workers=False,
        monitor_processes=False,
    )
    try:
        assert task_handler.Process is _ThreadAsProcess
        assert task_handler.Queue is queue.Queue
        assert isinstance(th.queue, queue.Queue)
        assert isinstance(th.logger_process, _ThreadAsProcess)
    finally:
        _stop_logger(th)


def test_task_handler_default_mode_untouched(monkeypatch, restore_globals):
    monkeypatch.delenv(WORKER_ISOLATION_ENV, raising=False)
    th = TaskHandler(
        configuration=Configuration(),
        workers=[],
        scan_for_annotated_workers=False,
        monitor_processes=False,
    )
    try:
        assert task_handler.Process is multiprocessing.Process
        assert task_handler.Queue is multiprocessing.Queue
        assert not getattr(task_handler, "_thread_isolation_applied", False)
        assert isinstance(th.logger_process, multiprocessing.Process)
    finally:
        th.queue.put(None)
        th.logger_process.join(timeout=5)


def test_thread_mode_start_stop_smoke(monkeypatch, restore_globals):
    """G5: full worker lifecycle in thread mode — no signal ValueError."""
    monkeypatch.setenv(WORKER_ISOLATION_ENV, "thread")
    thread_errors = []
    monkeypatch.setattr(threading, "excepthook", lambda args: thread_errors.append(args))

    with patch.object(TaskRunner, "run", Mock(return_value=None)):
        th = TaskHandler(
            configuration=Configuration(),
            workers=[ClassWorker("task")],
            scan_for_annotated_workers=False,
            monitor_processes=False,
        )
        try:
            th.start_processes()
            assert len(th.task_runner_processes) == 1
            for p in th.task_runner_processes:
                assert isinstance(p, _ThreadAsProcess)
                # run() is mocked to return, so the target must complete —
                # proving signal.signal + TaskRunner construction worked in
                # a non-main thread.
                p.join(timeout=5)
                assert not p.is_alive()
            th.stop_processes()
        finally:
            _stop_logger(th)
    assert thread_errors == []
