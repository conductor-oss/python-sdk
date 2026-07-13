# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Regression tests for the liveness-knob / AgentConfig wiring (idea-12 P1).

A prior merge slimmed ``AgentConfig`` down to connection/auth-free runtime
knobs but dropped ``liveness_stall_seconds`` / ``liveness_check_interval_seconds``
while ``AgentHandle._maybe_start_liveness_monitor`` still read them as plain
attributes — any stateful ``result()``/``join()`` call raised
``AttributeError``. These tests pin (a) the three liveness fields exist on
``AgentConfig`` with the documented defaults, and (b) the liveness-monitor
startup path actually works end-to-end against a real ``AgentConfig``
instance — not just a mock that happens to define whatever attributes the
test author remembered to stub.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from conductor.ai.agents.result import AgentHandle
from conductor.ai.agents.runtime._liveness import ServerLivenessMonitor
from conductor.ai.agents.runtime.config import AgentConfig


class TestAgentConfigLivenessDefaults:
    """AgentConfig must expose all three liveness knobs with guide defaults."""

    def test_default_liveness_knobs(self):
        cfg = AgentConfig()
        assert cfg.liveness_enabled is True
        assert cfg.liveness_stall_seconds == 30.0
        assert cfg.liveness_check_interval_seconds == 10.0

    def test_from_env_liveness_knobs(self, monkeypatch):
        monkeypatch.delenv("AGENTSPAN_LIVENESS_ENABLED", raising=False)
        monkeypatch.delenv("AGENTSPAN_LIVENESS_STALL_SECONDS", raising=False)
        monkeypatch.delenv("AGENTSPAN_LIVENESS_CHECK_INTERVAL_SECONDS", raising=False)
        cfg = AgentConfig.from_env()
        assert cfg.liveness_enabled is True
        assert cfg.liveness_stall_seconds == 30.0
        assert cfg.liveness_check_interval_seconds == 10.0


def _make_stateful_handle(config):
    """Build an AgentHandle with a stateful run_id and a stubbed runtime."""
    runtime = MagicMock()
    runtime._config = config
    runtime._workflow_client = MagicMock()
    handle = AgentHandle(execution_id="wf-1", runtime=runtime, run_id="domain-uuid-1")
    return handle


class TestMaybeStartLivenessMonitor:
    """_maybe_start_liveness_monitor() is the code path that crashed (P1)."""

    def test_real_agent_config_does_not_raise(self):
        """The actual bug: a real AgentConfig() must not raise AttributeError."""
        handle = _make_stateful_handle(AgentConfig())
        try:
            handle._maybe_start_liveness_monitor()
            assert isinstance(handle._liveness_monitor, ServerLivenessMonitor)
            assert handle._liveness_monitor._stall_seconds == 30.0
            assert handle._liveness_monitor._check_interval == 10.0
        finally:
            handle._stop_liveness_monitor()

    def test_bare_config_missing_liveness_fields_raises(self):
        """Characterizes the historical bug: a config object exposing only
        ``liveness_enabled`` (the shape AgentConfig regressed to) still fails
        past the enabled-check and blows up on the stall/interval reads.
        If AgentConfig ever drops these fields again, its behavior will
        match this shape and this suite's "does not raise" test above will
        start failing — that is the regression signal.
        """
        bare_config = SimpleNamespace(liveness_enabled=True)
        handle = _make_stateful_handle(bare_config)
        try:
            with pytest.raises(AttributeError):
                handle._maybe_start_liveness_monitor()
        finally:
            handle._stop_liveness_monitor()

    def test_liveness_disabled_skips_monitor(self):
        config = AgentConfig(liveness_enabled=False)
        handle = _make_stateful_handle(config)
        handle._maybe_start_liveness_monitor()
        assert handle._liveness_monitor is None

    def test_stateless_run_skips_monitor(self):
        """run_id=None (stateless) must not attempt to start a monitor."""
        runtime = MagicMock()
        runtime._config = AgentConfig()
        runtime._workflow_client = MagicMock()
        handle = AgentHandle(execution_id="wf-1", runtime=runtime, run_id=None)
        handle._maybe_start_liveness_monitor()
        assert handle._liveness_monitor is None
