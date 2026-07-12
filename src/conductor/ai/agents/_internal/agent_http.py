# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Authenticated HTTP to Agentspan ``/agent/*`` endpoints via the SDK ``ApiClient``.

Framework workers (claude_agent_sdk, langchain, langgraph) run in spawned worker
processes and receive ``(server_url, auth_key, auth_secret)`` as plain strings — a
live ``ApiClient`` can't cross the process boundary. This module reconstructs an
``ApiClient`` from those strings inside the worker, cached per
``(server_url, auth_key)`` so the token mint in the constructor happens once per
worker, and posts through :meth:`ApiClient.call_api`. That reuses the SDK's single
token authority (mint/cache/TTL-refresh/401-retry) instead of a parallel token
cache.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("conductor.ai.agents.agent_http")

# The auth-setting name the generated clients use to drive X-Authorization
# injection (see OrkesAgentClient._AUTH_SETTINGS).
_AUTH_SETTINGS = ["api_key"]
_JSON_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

# One ApiClient per (server_url, auth_key). Building an ApiClient mints a token in
# its constructor, so caching is mandatory to avoid a /token mint on every call.
_API_CLIENTS: Dict[Tuple[str, str], Any] = {}
_API_CLIENTS_LOCK = threading.Lock()


def _agent_api_client(server_url: str, auth_key: str, auth_secret: str):
    """Return a cached ``ApiClient`` for ``(server_url, auth_key)``.

    Imports are lazy so importing this module stays cheap and side-effect free
    (spawn/pickle safety).
    """
    key = (server_url, auth_key or "")
    client = _API_CLIENTS.get(key)
    if client is not None:
        return client

    from conductor.client.configuration.configuration import Configuration
    from conductor.client.configuration.settings.authentication_settings import (
        AuthenticationSettings,
    )
    from conductor.client.http.api_client import ApiClient

    auth = (
        AuthenticationSettings(key_id=auth_key, key_secret=auth_secret or "")
        if auth_key
        else None
    )
    config = Configuration(server_api_url=server_url, authentication_settings=auth)
    with _API_CLIENTS_LOCK:
        client = _API_CLIENTS.get(key)
        if client is None:
            client = ApiClient(config)
            _API_CLIENTS[key] = client
    return client


def agent_post(
    server_url: str,
    auth_key: str,
    auth_secret: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    *,
    read_response: bool = False,
) -> Optional[Any]:
    """POST to an Agentspan ``/agent/*`` endpoint through the SDK ``ApiClient``.

    ``path`` is relative to the server host (which already ends in ``/api``), so it
    must start with ``/`` and omit ``/api`` — e.g. ``/agent/events/{id}``.

    Returns the deserialized JSON body when ``read_response`` is True, otherwise
    ``None``. Any transport/HTTP error (including a non-retryable ``ApiException``)
    is swallowed and returns ``None`` so callers degrade exactly as the previous
    raw-``requests`` paths did — a 401 is still auto-retried once inside
    :meth:`ApiClient.call_api`.
    """
    try:
        client = _agent_api_client(server_url, auth_key, auth_secret)
        return client.call_api(
            path,
            "POST",
            {},
            [],
            dict(_JSON_HEADERS),
            body=body if body is not None else {},
            post_params=[],
            files={},
            response_type="object" if read_response else None,
            auth_settings=_AUTH_SETTINGS,
            _return_http_data_only=True,
            _preload_content=True,
        )
    except Exception as exc:  # ApiException + any transport-level error
        logger.debug("agent_post failed (path=%s): %s", path, exc)
        return None
