# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Unit tests for ``agent_http`` — the worker HTTP path that posts to Agentspan
``/agent/*`` endpoints through the SDK ``ApiClient``.

Uses a real in-process HTTP server (no mocks, per repo test policy) serving both
the ``POST /api/token`` mint (counted) and the ``/api/agent/*`` endpoints, so we
can assert the SDK's single token authority: one mint per worker (per
``(server_url, auth_key)``), with ``X-Authorization`` on every agent request.
"""

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conductor.ai.agents._internal import agent_http
from conductor.ai.agents._internal.agent_http import agent_post


def _jwt(exp: int) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


_TOKEN = _jwt(4102444800)  # far future — no mid-test TTL refresh


class _Handler(BaseHTTPRequestHandler):
    mint_count = 0
    agent_requests = []  # list of {"path", "x_auth", "body"}
    agent_status = 200
    agent_body = {}

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        if self.path == "/api/token":
            body = json.loads(raw or b"{}")
            if body.get("keyId") != "kid" or body.get("keySecret") != "ksec":
                self._send(401)
                return
            type(self).mint_count += 1
            self._send_json(200, {"token": _TOKEN})
            return
        if self.path.startswith("/api/agent/"):
            type(self).agent_requests.append(
                {
                    "path": self.path,
                    "x_auth": self.headers.get("X-Authorization"),
                    "body": json.loads(raw) if raw else None,
                }
            )
            if type(self).agent_status >= 400:
                self._send(type(self).agent_status)
                return
            self._send_json(type(self).agent_status, type(self).agent_body)
            return
        self._send(404)

    def _send(self, code):
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # silence
        pass


@pytest.fixture()
def server():
    _Handler.mint_count = 0
    _Handler.agent_requests = []
    _Handler.agent_status = 200
    _Handler.agent_body = {}
    agent_http._API_CLIENTS.clear()  # fresh ApiClient cache per test

    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    # server_url == the SDK "host": already ends in /api.
    yield f"http://127.0.0.1:{srv.server_address[1]}/api"
    srv.shutdown()
    agent_http._API_CLIENTS.clear()


def test_post_mints_once_and_caches(server):
    """Two posts with the same (server_url, auth_key) ⇒ exactly ONE /token mint,
    and every agent request carries X-Authorization (single token authority)."""
    agent_post(server, "kid", "ksec", "/agent/events/e1", {"type": "a"})
    agent_post(server, "kid", "ksec", "/agent/events/e1", {"type": "b"})

    assert _Handler.mint_count == 1  # cached ApiClient ⇒ no per-call mint
    assert len(_Handler.agent_requests) == 2
    assert all(r["x_auth"] == _TOKEN for r in _Handler.agent_requests)
    assert [r["body"] for r in _Handler.agent_requests] == [{"type": "a"}, {"type": "b"}]


def test_read_response_returns_dict(server):
    _Handler.agent_body = {"executionId": "wf-123"}
    resp = agent_post(server, "kid", "ksec", "/agent/execution", {"workflowName": "w"},
                      read_response=True)
    assert resp == {"executionId": "wf-123"}


def test_read_response_false_returns_none_but_posts(server):
    _Handler.agent_body = {"executionId": "wf-123"}
    result = agent_post(server, "kid", "ksec", "/agent/events/e1", {"type": "x"})
    assert result is None  # fire-and-forget shape
    assert len(_Handler.agent_requests) == 1  # request still executed
    assert _Handler.agent_requests[0]["body"] == {"type": "x"}


def test_server_error_returns_none(server):
    _Handler.agent_status = 500
    resp = agent_post(server, "kid", "ksec", "/agent/execution", {}, read_response=True)
    assert resp is None  # ApiException swallowed → graceful degradation


def test_404_returns_none_not_raise(server):
    _Handler.agent_status = 404
    resp = agent_post(server, "kid", "ksec", "/agent/999/tasks", {}, read_response=True)
    assert resp is None  # degrades; does NOT raise AgentNotFoundError


def test_anonymous_no_mint_no_auth_header(server):
    """Empty auth_key ⇒ no authentication settings ⇒ no /token mint and no
    X-Authorization, but the agent request still goes out."""
    agent_post(server, "", "", "/agent/events/e1", {"type": "anon"})
    assert _Handler.mint_count == 0
    assert len(_Handler.agent_requests) == 1
    assert _Handler.agent_requests[0]["x_auth"] is None
