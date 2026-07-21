# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""SDK-level exceptions for the agent API clients.

Provides a consistent exception hierarchy so users don't need to catch
library-specific HTTP errors from ``requests`` or ``httpx``.

This module is the canonical home of the hierarchy formerly defined in
``conductor.ai.agents.exceptions``. ``AgentspanError`` remains an alias for
backward compatibility; new code should catch ``ConductorAgentError``.
"""

from __future__ import annotations


class ConductorAgentError(Exception):
    """Base exception for all agent SDK errors."""


# Kept as the identical class object so existing ``except`` clauses and
# ``isinstance`` checks continue to work during the naming migration.
AgentspanError = ConductorAgentError


class AgentAPIError(ConductorAgentError):
    """An HTTP error from the agent runtime API."""

    def __init__(self, status_code: int, message: str, url: str = ""):
        self.status_code = status_code
        self.message = message
        self.url = url
        super().__init__(f"HTTP {status_code}: {message}" + (f" ({url})" if url else ""))


class AgentNotFoundError(AgentAPIError):
    """Raised when the workflow/agent ID is not found (404)."""


def _raise_api_error(exc: Exception, url: str = "") -> None:
    """Convert an HTTP library exception to an SDK exception and raise it.

    Handles both ``requests.HTTPError`` and ``httpx.HTTPStatusError``.
    """
    status_code = 0
    message = str(exc)

    # requests.HTTPError
    if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        status_code = exc.response.status_code
        try:
            body = exc.response.text
        except Exception:
            body = message
        message = body or message

    # httpx.HTTPStatusError
    if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        status_code = exc.response.status_code
        try:
            message = exc.response.text or message
        except Exception:
            pass

    if status_code == 404:
        raise AgentNotFoundError(status_code, message, url) from exc
    raise AgentAPIError(status_code, message, url) from exc
