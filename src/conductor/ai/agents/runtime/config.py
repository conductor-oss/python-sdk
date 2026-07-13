# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Configuration — load settings from environment variables.

Uses ``dataclasses`` with a ``from_env()`` classmethod for env var loading.
Constructor kwargs allow direct overrides (useful for tests).

Usage::

    config = AgentConfig.from_env()               # load from env
    config = AgentConfig(worker_thread_count=4)   # explicit override
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional


def _env(var: str, default=None):
    """Read an environment variable, returning *default* if unset."""
    return os.environ.get(var, default)


logger = logging.getLogger("conductor.ai.agents.config")


def _env_bool(var: str, default: bool = False) -> bool:
    """Read a boolean environment variable (true/1/yes → True)."""
    val = os.environ.get(var)
    if val is None or val.strip() == "":
        return default
    return val.lower() in ("true", "1", "yes")


def _env_int(var: str, default: int = 0) -> int:
    """Read an integer environment variable."""
    val = os.environ.get(var)
    if val is None or val.strip() == "":
        return default
    return int(val)


def _env_float(var: str, default: float = 0.0) -> float:
    """Read a float environment variable."""
    val = os.environ.get(var)
    if val is None or val.strip() == "":
        return default
    return float(val)


@dataclass
class AgentConfig:
    """Agent-runtime settings.

    Server connection and auth (URL, credentials) and the SDK-wide log level
    live on the conductor :class:`Configuration`, not here — this holds only
    agent-runtime concerns (worker pool + liveness monitoring).

    Attributes:
        worker_poll_interval_ms: Worker polling interval in milliseconds.
        worker_thread_count: Number of threads per worker.
        auto_start_workers: Whether to auto-start worker processes.
        daemon_workers: Whether worker processes are daemon (killed on exit).
        auto_register_integrations: Auto-create LLM integrations on startup.
        streaming_enabled: Whether ``stream()`` uses server-sent events.
        liveness_enabled: Start a server-liveness monitor for stateful runs so
            ``result()`` / ``join()`` don't block forever if the worker dies.
        liveness_stall_seconds: Idle window (no polls) before a run is
            considered stalled.
        liveness_check_interval_seconds: How often the monitor polls.
    """

    worker_poll_interval_ms: int = 100
    worker_thread_count: int = 1
    auto_start_workers: bool = True
    daemon_workers: bool = True
    auto_register_integrations: bool = False
    streaming_enabled: bool = True
    liveness_enabled: bool = True
    liveness_stall_seconds: float = 30.0
    liveness_check_interval_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> AgentConfig:
        """Create an ``AgentConfig`` by reading ``AGENTSPAN_*`` env vars."""
        return cls(
            worker_poll_interval_ms=_env_int("AGENTSPAN_WORKER_POLL_INTERVAL", 100),
            worker_thread_count=_env_int("AGENTSPAN_WORKER_THREADS", 1),
            auto_start_workers=_env_bool("AGENTSPAN_AUTO_START_WORKERS", True),
            daemon_workers=_env_bool("AGENTSPAN_DAEMON_WORKERS", True),
            auto_register_integrations=_env_bool("AGENTSPAN_INTEGRATIONS_AUTO_REGISTER", False),
            streaming_enabled=_env_bool("AGENTSPAN_STREAMING_ENABLED", True),
            liveness_enabled=_env_bool("AGENTSPAN_LIVENESS_ENABLED", True),
            liveness_stall_seconds=_env_float("AGENTSPAN_LIVENESS_STALL_SECONDS", 30.0),
            liveness_check_interval_seconds=_env_float(
                "AGENTSPAN_LIVENESS_CHECK_INTERVAL_SECONDS", 10.0
            ),
        )
