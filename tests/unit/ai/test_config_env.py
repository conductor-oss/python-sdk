# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for AgentConfig environment loading and SDK-wide log-level config.

AgentConfig holds only agent-runtime settings (worker pool + liveness).
Connection, auth, and the log level live on the conductor ``Configuration``.
"""

from __future__ import annotations

import logging
import os
from unittest import mock

from conductor.ai.agents.runtime.config import (
    AgentConfig,
    _env,
    _env_bool,
    _env_float,
    _env_int,
)
from conductor.client.configuration.configuration import Configuration


class TestEnvHelper:
    """Tests for the _env() helper function."""

    def test_reads_var(self):
        with mock.patch.dict(os.environ, {"AGENTSPAN_FOO": "bar"}, clear=False):
            assert _env("AGENTSPAN_FOO") == "bar"

    def test_returns_default_when_not_set(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert _env("AGENTSPAN_FOO", "default") == "default"

    def test_returns_none_when_no_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert _env("AGENTSPAN_FOO") is None


class TestEnvBool:
    """Tests for _env_bool() helper."""

    def test_true_values(self):
        for val in ("true", "True", "TRUE", "1", "yes"):
            with mock.patch.dict(os.environ, {"FLAG": val}, clear=True):
                assert _env_bool("FLAG") is True, f"Failed for {val!r}"

    def test_false_values(self):
        for val in ("false", "False", "0", "no"):
            with mock.patch.dict(os.environ, {"FLAG": val}, clear=True):
                assert _env_bool("FLAG") is False, f"Failed for {val!r}"

    def test_default_true(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert _env_bool("FLAG", True) is True

    def test_default_false(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert _env_bool("FLAG", False) is False

    def test_empty_string_uses_default(self):
        with mock.patch.dict(os.environ, {"FLAG": ""}, clear=True):
            assert _env_bool("FLAG", True) is True


class TestEnvInt:
    """Tests for _env_int() helper."""

    def test_reads_int(self):
        with mock.patch.dict(os.environ, {"NUM": "42"}, clear=True):
            assert _env_int("NUM") == 42

    def test_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert _env_int("NUM", 7) == 7

    def test_empty_string_uses_default(self):
        with mock.patch.dict(os.environ, {"NUM": ""}, clear=True):
            assert _env_int("NUM", 7) == 7


class TestEnvFloat:
    """Tests for _env_float() helper."""

    def test_reads_float(self):
        with mock.patch.dict(os.environ, {"SECS": "12.5"}, clear=True):
            assert _env_float("SECS") == 12.5

    def test_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert _env_float("SECS", 30.0) == 30.0

    def test_empty_string_uses_default(self):
        with mock.patch.dict(os.environ, {"SECS": ""}, clear=True):
            assert _env_float("SECS", 30.0) == 30.0


class TestAgentConfigFromEnv:
    """Tests for AgentConfig.from_env() — agent-runtime settings only."""

    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config = AgentConfig.from_env()
            assert config.worker_poll_interval_ms == 100
            assert config.worker_thread_count == 1
            assert config.auto_start_workers is True

    def test_boolean_env_vars(self):
        env = {
            "AGENTSPAN_DAEMON_WORKERS": "false",
            "AGENTSPAN_INTEGRATIONS_AUTO_REGISTER": "true",
            "AGENTSPAN_STREAMING_ENABLED": "no",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = AgentConfig.from_env()
            assert config.daemon_workers is False
            assert config.auto_register_integrations is True
            assert config.streaming_enabled is False

    def test_numeric_env_vars(self):
        env = {
            "AGENTSPAN_WORKER_POLL_INTERVAL": "250",
            "AGENTSPAN_WORKER_THREADS": "4",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = AgentConfig.from_env()
            assert config.worker_poll_interval_ms == 250
            assert config.worker_thread_count == 4

    def test_direct_construction(self):
        config = AgentConfig(worker_thread_count=8)
        assert config.worker_thread_count == 8


class TestLivenessConfig:
    """Liveness monitor settings (used by stateful runs)."""

    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config = AgentConfig.from_env()
            assert config.liveness_enabled is True
            assert config.liveness_stall_seconds == 30.0
            assert config.liveness_check_interval_seconds == 10.0

    def test_from_env(self):
        env = {
            "AGENTSPAN_LIVENESS_ENABLED": "false",
            "AGENTSPAN_LIVENESS_STALL_SECONDS": "45",
            "AGENTSPAN_LIVENESS_CHECK_INTERVAL_SECONDS": "5",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = AgentConfig.from_env()
            assert config.liveness_enabled is False
            assert config.liveness_stall_seconds == 45.0
            assert config.liveness_check_interval_seconds == 5.0


class TestConfigurationLogLevel:
    """The SDK-wide log level lives on Configuration (not AgentConfig)."""

    def test_default_is_info(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert Configuration().log_level == logging.INFO

    def test_debug_flag_sets_debug_level(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert Configuration(debug=True).log_level == logging.DEBUG

    def test_explicit_level_name(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert Configuration(log_level="WARNING").log_level == logging.WARNING

    def test_explicit_level_int(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert Configuration(log_level=logging.ERROR).log_level == logging.ERROR

    def test_conductor_log_level_env(self):
        with mock.patch.dict(os.environ, {"CONDUCTOR_LOG_LEVEL": "WARNING"}, clear=True):
            assert Configuration().log_level == logging.WARNING

    def test_agentspan_log_level_env_fallback(self):
        with mock.patch.dict(os.environ, {"AGENTSPAN_LOG_LEVEL": "DEBUG"}, clear=True):
            assert Configuration().log_level == logging.DEBUG

    def test_applied_to_logger_by_runtime(self):
        """AgentRuntime applies Configuration.log_level to the conductor.ai logger."""
        with mock.patch("conductor.client.orkes_clients.OrkesClients"):
            with mock.patch("conductor.ai.agents.runtime.worker_manager.WorkerManager"):
                from conductor.ai.agents.runtime.runtime import AgentRuntime

                AgentRuntime(Configuration(log_level="WARNING"))

        assert logging.getLogger("conductor.ai").level == logging.WARNING
        logging.getLogger("conductor.ai").setLevel(logging.INFO)  # reset
