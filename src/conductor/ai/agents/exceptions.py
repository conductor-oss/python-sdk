"""Backward-compat shim — the exception hierarchy moved to ``conductor.client.ai``.

Import from :mod:`conductor.client.ai.agent_errors` (or ``conductor.client.ai``)
going forward. This module re-exports the same objects.
"""

from __future__ import annotations

from conductor.client.ai.agent_errors import (  # noqa: F401
    AgentAPIError,
    AgentNotFoundError,
    ConductorAgentError,
    _raise_api_error,
)
