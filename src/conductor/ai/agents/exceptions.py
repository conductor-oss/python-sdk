# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Backward-compat shim — the exception hierarchy moved to ``conductor.client.ai``.

Import from :mod:`conductor.client.ai.agent_errors` (or ``conductor.client.ai``)
going forward. This module re-exports the same objects, so existing
``except AgentspanError`` clauses and ``isinstance`` checks are unaffected.
"""

from __future__ import annotations

from conductor.client.ai.agent_errors import (  # noqa: F401
    AgentAPIError,
    AgentNotFoundError,
    AgentspanError,
    _raise_api_error,
)
