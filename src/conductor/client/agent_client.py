# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Abstract interface for the Agent Runtime API (``/agent/*`` control plane).

Follows the same interface + Orkes-implementation convention as
:class:`conductor.client.workflow_client.WorkflowClient` /
:class:`conductor.client.orkes.orkes_workflow_client.OrkesWorkflowClient`. The
concrete :class:`conductor.client.orkes.orkes_agent_client.OrkesAgentClient` is
built on the shared :class:`~conductor.client.http.api_client.ApiClient` (sync)
and :class:`~conductor.client.http.async_api_client.AsyncApiClient` (async), so
JWT minting / ``X-Authorization`` / TTL refresh / 401-retry are reused rather
than re-implemented.

This interface is transport only — no dependency on the agent-DX layer
(``conductor.ai.agents``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, Iterator, Optional


class SSEUnavailableError(Exception):
    """Raised when the server doesn't support SSE streaming."""


class AgentClient(ABC):
    """Client for the Agent Runtime API (``/agent/*``).

    Each control-plane operation has a synchronous method and an ``*_async``
    counterpart.
    """

    # ── start / deploy / compile ─────────────────────────────────────────
    @abstractmethod
    def start_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST /agent/start — start an agent execution."""
        pass

    @abstractmethod
    async def start_agent_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def deploy_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST /agent/deploy — deploy agent (compile + register, no execution)."""
        pass

    @abstractmethod
    async def deploy_agent_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def compile_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST /agent/compile — compile agent config to an agent/workflow def."""
        pass

    @abstractmethod
    async def compile_agent_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    # ── status / execution ───────────────────────────────────────────────
    @abstractmethod
    def get_status(self, execution_id: str) -> Dict[str, Any]:
        """GET /agent/{id}/status — fetch execution status."""
        pass

    @abstractmethod
    async def get_status_async(self, execution_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """GET /agent/execution/{id} — full execution tree."""
        pass

    @abstractmethod
    async def get_execution_async(self, execution_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_executions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET /agent/executions — search executions (query ``params``)."""
        pass

    @abstractmethod
    async def list_executions_async(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pass

    # ── HITL / control ───────────────────────────────────────────────────
    @abstractmethod
    def respond(self, execution_id: str, body: Dict[str, Any]) -> None:
        """POST /agent/{id}/respond — complete a pending human task."""
        pass

    @abstractmethod
    async def respond_async(self, execution_id: str, body: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def stop(self, execution_id: str) -> None:
        """POST /agent/{id}/stop — graceful deterministic stop."""
        pass

    @abstractmethod
    async def stop_async(self, execution_id: str) -> None:
        pass

    @abstractmethod
    def signal(self, execution_id: str, message: str) -> None:
        """POST /agent/{id}/signal — inject persistent context."""
        pass

    @abstractmethod
    async def signal_async(self, execution_id: str, message: str) -> None:
        pass

    # ── streaming ────────────────────────────────────────────────────────
    @abstractmethod
    def stream_sse(
        self, execution_id: str, last_event_id: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        """GET /agent/stream/{id} — consume SSE events (sync generator).

        Yields parsed event dicts. Auto-reconnects with ``Last-Event-ID`` on
        connection drops. Raises :class:`SSEUnavailableError` if the server
        doesn't support SSE or sends only heartbeats.
        """
        pass

    @abstractmethod
    def stream_sse_async(
        self, execution_id: str, last_event_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async counterpart of :meth:`stream_sse`."""
        pass

    # ── lifecycle ────────────────────────────────────────────────────────
    @abstractmethod
    def close(self) -> None:
        """Release any transport resources held by the client."""
        pass

    @abstractmethod
    async def close_async(self) -> None:
        pass
