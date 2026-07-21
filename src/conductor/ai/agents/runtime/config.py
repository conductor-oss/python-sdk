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


def _env(var: str, default=None, *, legacy_var: Optional[str] = None):
    """Read a canonical environment variable with an optional legacy fallback.

    Blank values are treated as unset.  The SDK documents only the canonical
    ``CONDUCTOR_AGENT_*`` names; ``AGENTSPAN_*`` remains a compatibility path
    for applications upgrading in place.
    """
    value = os.environ.get(var)
    if value is not None and value.strip() != "":
        return value
    if legacy_var:
        legacy_value = os.environ.get(legacy_var)
        if legacy_value is not None and legacy_value.strip() != "":
            return legacy_value
    return default


logger = logging.getLogger("conductor.ai.agents.config")


def _env_bool(var: str, default: bool = False, *, legacy_var: Optional[str] = None) -> bool:
    """Read a boolean environment variable; malformed values use *default*."""
    val = _env(var, legacy_var=legacy_var)
    if val is None:
        return default
    normalized = val.lower()
    if normalized in ("true", "1", "yes", "on"):
        return True
    if normalized in ("false", "0", "no", "off"):
        return False
    return default


def _env_int(var: str, default: int = 0, *, legacy_var: Optional[str] = None) -> int:
    """Read an integer environment variable; malformed values use *default*."""
    val = _env(var, legacy_var=legacy_var)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_float(var: str, default: float = 0.0, *, legacy_var: Optional[str] = None) -> float:
    """Read a float environment variable; malformed values use *default*."""
    val = _env(var, legacy_var=legacy_var)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


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
        """Create an ``AgentConfig`` from canonical environment variables.

        ``CONDUCTOR_AGENT_*`` wins over the corresponding legacy setting when
        both are supplied.
        """
        return cls(
            worker_poll_interval_ms=_env_int(
                "CONDUCTOR_AGENT_WORKER_POLL_INTERVAL", 100,
                legacy_var="AGENTSPAN_WORKER_POLL_INTERVAL",
            ),
            worker_thread_count=_env_int(
                "CONDUCTOR_AGENT_WORKER_THREADS", 1,
                legacy_var="AGENTSPAN_WORKER_THREADS",
            ),
            auto_start_workers=_env_bool(
                "CONDUCTOR_AGENT_AUTO_START_WORKERS", True,
                legacy_var="AGENTSPAN_AUTO_START_WORKERS",
            ),
            daemon_workers=_env_bool(
                "CONDUCTOR_AGENT_DAEMON_WORKERS", True,
                legacy_var="AGENTSPAN_DAEMON_WORKERS",
            ),
            auto_register_integrations=_env_bool(
                "CONDUCTOR_AGENT_INTEGRATIONS_AUTO_REGISTER", False,
                legacy_var="AGENTSPAN_INTEGRATIONS_AUTO_REGISTER",
            ),
            streaming_enabled=_env_bool(
                "CONDUCTOR_AGENT_STREAMING_ENABLED", True,
                legacy_var="AGENTSPAN_STREAMING_ENABLED",
            ),
            liveness_enabled=_env_bool(
                "CONDUCTOR_AGENT_LIVENESS_ENABLED", True,
                legacy_var="AGENTSPAN_LIVENESS_ENABLED",
            ),
            liveness_stall_seconds=_env_float(
                "CONDUCTOR_AGENT_LIVENESS_STALL_SECONDS", 30.0,
                legacy_var="AGENTSPAN_LIVENESS_STALL_SECONDS",
            ),
            liveness_check_interval_seconds=_env_float(
                "CONDUCTOR_AGENT_LIVENESS_CHECK_INTERVAL_SECONDS", 10.0,
                legacy_var="AGENTSPAN_LIVENESS_CHECK_INTERVAL_SECONDS",
            ),
        )
