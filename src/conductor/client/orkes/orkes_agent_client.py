# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Orkes implementation of :class:`AgentClient` for the ``/agent/*`` control plane.

All wire calls go through the shared :class:`ApiClient` (sync) /
:class:`AsyncApiClient` (async) built from the :class:`Configuration`, so JWT
minting, ``X-Authorization`` injection, TTL refresh and 401-retry are reused —
never re-implemented here. The one exception is SSE streaming, which the
generated ``call_api`` cannot do; it uses ``requests`` / ``httpx`` directly but
still borrows the auth header from the ``ApiClient``'s token machinery.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from conductor.client.agent_client import AgentClient, SSEUnavailableError
from conductor.client.ai.agent_errors import AgentAPIError, AgentNotFoundError
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.async_api_client import AsyncApiClient
from conductor.client.http.rest import ApiException
from conductor.client.orkes.orkes_base_client import OrkesBaseClient

logger = logging.getLogger(
    Configuration.get_logging_formatted_name("conductor.client.orkes.orkes_agent_client")
)

_SSE_NO_EVENT_TIMEOUT = 15  # seconds to wait for a real event before declaring SSE unavailable
_AUTH_SETTINGS = ["api_key"]


def _raise_from_api_exception(exc: ApiException, url: str = "") -> None:
    """Map a conductor :class:`ApiException` to an agent-SDK exception."""
    status = getattr(exc, "status", 0) or 0
    body = getattr(exc, "body", None) or getattr(exc, "reason", None) or str(exc)
    if status == 404:
        raise AgentNotFoundError(status, body, url) from exc
    raise AgentAPIError(status, body, url) from exc


class OrkesAgentClient(OrkesBaseClient, AgentClient):
    def __init__(self, configuration: Configuration):
        super(OrkesAgentClient, self).__init__(configuration)
        self._configuration = configuration
        self._server_url = (configuration.host or "").rstrip("/")
        self._async_api_client: Optional[AsyncApiClient] = None
        self._schedule_client_instance: Any = None
        # Persistent httpx client for async SSE streaming (created lazily).
        self._sse_async_client: Any = None

    # ── internal helpers ─────────────────────────────────────────────────

    def _async(self) -> AsyncApiClient:
        if self._async_api_client is None:
            self._async_api_client = AsyncApiClient(self._configuration)
        return self._async_api_client

    def _json_headers(self) -> Dict[str, str]:
        return {
            "Accept": self.api_client.select_header_accept(["application/json"]),
            "Content-Type": self.api_client.select_header_content_type(["application/json"]),
        }

    def _agent_url(self, path: str) -> str:
        return f"{self._server_url}/agent{path}"

    def _sync_auth_header(self) -> Dict[str, str]:
        """Flat ``X-Authorization`` header reused from the sync ApiClient ({} if none)."""
        headers = self.api_client.get_authentication_headers()
        if not headers:
            return {}
        return dict(headers.get("header", {}))

    async def _async_auth_header(self) -> Dict[str, str]:
        headers = await self._async().get_authentication_headers()
        if not headers:
            return {}
        return dict(headers.get("header", {}))

    def _call(self, path: str, method: str, body=None, response_type=None, query_params=None):
        try:
            return self.api_client.call_api(
                path, method,
                {}, query_params or [], self._json_headers(),
                body=body,
                post_params=[],
                files={},
                response_type=response_type,
                auth_settings=_AUTH_SETTINGS,
                _return_http_data_only=True,
                _preload_content=True,
            )
        except ApiException as exc:
            _raise_from_api_exception(exc, url=self._agent_url(path[len("/agent"):]))

    async def _call_async(self, path: str, method: str, body=None, response_type=None, query_params=None):
        try:
            return await self._async().call_api(
                path, method,
                {}, query_params or [], self._json_headers(),
                body=body,
                post_params=[],
                files={},
                response_type=response_type,
                auth_settings=_AUTH_SETTINGS,
                _return_http_data_only=True,
                _preload_content=True,
            )
        except ApiException as exc:
            _raise_from_api_exception(exc, url=self._agent_url(path[len("/agent"):]))

    # ── start / deploy / compile ─────────────────────────────────────────

    def start_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call("/agent/start", "POST", body=payload, response_type="object") or {}

    async def start_agent_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._call_async("/agent/start", "POST", body=payload, response_type="object") or {}

    def deploy_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call("/agent/deploy", "POST", body=payload, response_type="object") or {}

    async def deploy_agent_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._call_async("/agent/deploy", "POST", body=payload, response_type="object") or {}

    def compile_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call("/agent/compile", "POST", body=payload, response_type="object") or {}

    async def compile_agent_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._call_async("/agent/compile", "POST", body=payload, response_type="object") or {}

    # ── status / execution ───────────────────────────────────────────────

    def get_status(self, execution_id: str) -> Dict[str, Any]:
        return self._call(f"/agent/{execution_id}/status", "GET", response_type="object") or {}

    async def get_status_async(self, execution_id: str) -> Dict[str, Any]:
        return await self._call_async(f"/agent/{execution_id}/status", "GET", response_type="object") or {}

    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        return self._call(f"/agent/execution/{execution_id}", "GET", response_type="object") or {}

    async def get_execution_async(self, execution_id: str) -> Dict[str, Any]:
        return await self._call_async(f"/agent/execution/{execution_id}", "GET", response_type="object") or {}

    def list_executions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        query = list((params or {}).items())
        return self._call("/agent/executions", "GET", response_type="object", query_params=query) or {}

    async def list_executions_async(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        query = list((params or {}).items())
        return await self._call_async(
            "/agent/executions", "GET", response_type="object", query_params=query
        ) or {}

    # ── HITL / control ───────────────────────────────────────────────────

    def respond(self, execution_id: str, body: Dict[str, Any]) -> None:
        self._call(f"/agent/{execution_id}/respond", "POST", body=body)

    async def respond_async(self, execution_id: str, body: Dict[str, Any]) -> None:
        await self._call_async(f"/agent/{execution_id}/respond", "POST", body=body)

    def stop(self, execution_id: str) -> None:
        self._call(f"/agent/{execution_id}/stop", "POST")

    async def stop_async(self, execution_id: str) -> None:
        await self._call_async(f"/agent/{execution_id}/stop", "POST")

    def signal(self, execution_id: str, message: str) -> None:
        self._call(f"/agent/{execution_id}/signal", "POST", body={"message": message})

    async def signal_async(self, execution_id: str, message: str) -> None:
        await self._call_async(f"/agent/{execution_id}/signal", "POST", body={"message": message})

    # ── streaming (SSE — not call_api-able; reuses the ApiClient token) ───

    def stream_sse(
        self, execution_id: str, last_event_id: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        import requests

        url = self._agent_url(f"/stream/{execution_id}")
        base_headers = {**self._sync_auth_header(), "Accept": "text/event-stream"}
        first_connect = True
        got_real_event = False

        while True:
            try:
                req_headers = dict(base_headers)
                if last_event_id is not None:
                    req_headers["Last-Event-ID"] = last_event_id
                with requests.get(url, headers=req_headers, stream=True, timeout=(5, 30)) as resp:
                    if resp.status_code != 200:
                        if first_connect:
                            raise SSEUnavailableError(f"Server returned {resp.status_code}")
                        logger.warning("SSE reconnect failed (status=%s), stopping", resp.status_code)
                        return
                    first_connect = False
                    connect_time = time.monotonic()
                    for sse_event in self._parse_sse(resp.iter_lines()):
                        if sse_event.get("_heartbeat"):
                            if (not got_real_event
                                    and time.monotonic() - connect_time > _SSE_NO_EVENT_TIMEOUT):
                                raise SSEUnavailableError(
                                    "SSE connected but no events received "
                                    f"(only heartbeats for {_SSE_NO_EVENT_TIMEOUT}s)"
                                )
                            continue
                        if sse_event.get("id"):
                            last_event_id = sse_event["id"]
                        got_real_event = True
                        yield sse_event
                return
            except SSEUnavailableError:
                raise
            except Exception as e:
                if first_connect:
                    raise SSEUnavailableError(str(e))
                logger.warning("SSE connection lost (%s), reconnecting in 1s...", e)
                time.sleep(1)

    async def stream_sse_async(
        self, execution_id: str, last_event_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        import asyncio

        import httpx

        url = self._agent_url(f"/stream/{execution_id}")
        base_headers = {**(await self._async_auth_header()), "Accept": "text/event-stream"}
        first_connect = True
        got_real_event = False

        while True:
            try:
                req_headers = dict(base_headers)
                if last_event_id is not None:
                    req_headers["Last-Event-ID"] = last_event_id
                client = self._get_sse_async_client()
                async with client.stream(
                    "GET", url, headers=req_headers, timeout=httpx.Timeout(30.0, connect=5.0)
                ) as resp:
                    if resp.status_code != 200:
                        if first_connect:
                            raise SSEUnavailableError(f"Server returned {resp.status_code}")
                        logger.warning("SSE reconnect failed (status=%s), stopping", resp.status_code)
                        return
                    first_connect = False
                    connect_time = time.monotonic()
                    async for sse_event in self._parse_sse_async(resp.aiter_lines()):
                        if sse_event.get("_heartbeat"):
                            if (not got_real_event
                                    and time.monotonic() - connect_time > _SSE_NO_EVENT_TIMEOUT):
                                raise SSEUnavailableError(
                                    "SSE connected but no events received "
                                    f"(only heartbeats for {_SSE_NO_EVENT_TIMEOUT}s)"
                                )
                            continue
                        if sse_event.get("id"):
                            last_event_id = sse_event["id"]
                        got_real_event = True
                        yield sse_event
                return
            except SSEUnavailableError:
                raise
            except Exception as e:
                if first_connect:
                    raise SSEUnavailableError(str(e))
                logger.warning("SSE connection lost (%s), reconnecting in 1s...", e)
                await asyncio.sleep(1)

    def _get_sse_async_client(self):
        import httpx

        if self._sse_async_client is None or self._sse_async_client.is_closed:
            self._sse_async_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
        return self._sse_async_client

    @staticmethod
    def _parse_sse(lines: Iterator[Any]) -> Iterator[Dict[str, Any]]:
        """Parse SSE wire format into event dicts (sync). Heartbeats → ``{"_heartbeat": True}``."""
        event_type: Optional[str] = None
        event_id: Optional[str] = None
        data_lines: List[str] = []
        for raw_line in lines:
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if line.startswith(":"):
                yield {"_heartbeat": True}
                continue
            if line == "":
                if data_lines:
                    data_str = "\n".join(data_lines)
                    try:
                        data = json.loads(data_str)
                    except (json.JSONDecodeError, ValueError):
                        data = {"content": data_str}
                    yield {"event": event_type, "id": event_id, "data": data}
                event_type = event_id = None
                data_lines = []
                continue
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("id:"):
                event_id = line[3:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

    @staticmethod
    async def _parse_sse_async(lines: AsyncIterator[str]) -> AsyncIterator[Dict[str, Any]]:
        """Async counterpart of :meth:`_parse_sse`."""
        event_type: Optional[str] = None
        event_id: Optional[str] = None
        data_lines: List[str] = []
        async for raw_line in lines:
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if line.startswith(":"):
                yield {"_heartbeat": True}
                continue
            if line == "":
                if data_lines:
                    data_str = "\n".join(data_lines)
                    try:
                        data = json.loads(data_str)
                    except (json.JSONDecodeError, ValueError):
                        data = {"content": data_str}
                    yield {"event": event_type, "id": event_id, "data": data}
                event_type = event_id = None
                data_lines = []
                continue
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("id:"):
                event_id = line[3:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

    # ── schedules convenience (in-layer SchedulerClient) ─────────────────

    @property
    def schedules(self) -> Any:
        """Cron schedule lifecycle client (:class:`SchedulerClient`) for this config."""
        if self._schedule_client_instance is None:
            from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient

            self._schedule_client_instance = OrkesSchedulerClient(self._configuration)
        return self._schedule_client_instance

    # ── lifecycle ────────────────────────────────────────────────────────

    def close(self) -> None:  # sync transport holds no persistent connections
        pass

    async def close_async(self) -> None:
        if self._sse_async_client is not None and not self._sse_async_client.is_closed:
            await self._sse_async_client.aclose()
            self._sse_async_client = None
        if self._async_api_client is not None:
            try:
                await self._async_api_client.close()
            except Exception:
                pass
            self._async_api_client = None
