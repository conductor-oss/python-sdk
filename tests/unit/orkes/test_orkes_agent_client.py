# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for OrkesAgentClient — the /agent/* control-plane client.

Uses a real in-process HTTP server (no mocks, per repo test policy) that emulates
the agent endpoints plus the POST /token mint. Verifies request path/method/body,
that the X-Authorization JWT is minted via the shared ApiClient and sent, and that
HTTP errors map to the agent SDK exceptions.
"""

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conductor.client.agent_client import AgentClient
from conductor.client.ai.agent_errors import AgentAPIError, AgentNotFoundError
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_agent_client import OrkesAgentClient


def _jwt(exp: int) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


_JWT = _jwt(4102444800)  # far future


class _AgentHandler(BaseHTTPRequestHandler):
    # Recorded for assertions.
    last_path = None
    last_method = None
    last_body = None
    last_x_authorization = None
    mint_count = 0
    # Test knobs.
    status_for_agent = 200

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else None

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):  # noqa: N802
        body = self._read_body()
        if self.path == "/api/token":
            type(self).mint_count += 1
            self._json(200, {"token": _JWT})
            return
        self._record()
        type(self).last_body = body
        self._json(type(self).status_for_agent, {"executionId": "wf-1", "ok": True})

    def do_GET(self):  # noqa: N802
        self._record()
        self._json(type(self).status_for_agent, {"status": "COMPLETED", "results": []})

    def _record(self):
        type(self).last_path = self.path
        type(self).last_method = self.command
        type(self).last_x_authorization = self.headers.get("X-Authorization")

    def log_message(self, *args):  # silence
        pass


@pytest.fixture()
def server():
    _AgentHandler.last_path = None
    _AgentHandler.last_method = None
    _AgentHandler.last_body = None
    _AgentHandler.last_x_authorization = None
    _AgentHandler.mint_count = 0
    _AgentHandler.status_for_agent = 200
    srv = HTTPServer(("127.0.0.1", 0), _AgentHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/api"
    srv.shutdown()


def _client(server_url, *, auth=False):
    from conductor.client.configuration.settings.authentication_settings import (
        AuthenticationSettings,
    )

    cfg = Configuration(server_api_url=server_url)
    if auth:
        cfg.authentication_settings = AuthenticationSettings(key_id="kid", key_secret="ksec")
    else:
        cfg.authentication_settings = None
    return OrkesAgentClient(cfg)


def test_is_agent_client_interface(server):
    assert isinstance(_client(server), AgentClient)


def test_start_agent_path_and_body(server):
    c = _client(server)
    result = c.start_agent({"prompt": "hello"})
    assert result["executionId"] == "wf-1"
    assert _AgentHandler.last_path == "/api/agent/start"
    assert _AgentHandler.last_method == "POST"
    assert _AgentHandler.last_body == {"prompt": "hello"}


def test_deploy_and_compile_paths(server):
    c = _client(server)
    c.deploy_agent({"agentConfig": {}})
    assert _AgentHandler.last_path == "/api/agent/deploy"
    c.compile_agent({"agentConfig": {}})
    assert _AgentHandler.last_path == "/api/agent/compile"


def test_status_execution_and_hitl_paths(server):
    c = _client(server)
    c.get_status("wf-9")
    assert _AgentHandler.last_path == "/api/agent/wf-9/status"
    assert _AgentHandler.last_method == "GET"
    c.get_execution("wf-9")
    assert _AgentHandler.last_path == "/api/agent/execution/wf-9"
    c.respond("wf-9", {"approved": True})
    assert _AgentHandler.last_path == "/api/agent/wf-9/respond"
    c.stop("wf-9")
    assert _AgentHandler.last_path == "/api/agent/wf-9/stop"
    c.signal("wf-9", "note")
    assert _AgentHandler.last_path == "/api/agent/wf-9/signal"
    assert _AgentHandler.last_body == {"message": "note"}


def test_list_executions_sends_query(server):
    c = _client(server)
    c.list_executions({"agentName": "a", "size": 5})
    assert _AgentHandler.last_path.startswith("/api/agent/executions?")
    assert "agentName=a" in _AgentHandler.last_path


def test_anonymous_sends_no_auth_header(server):
    c = _client(server)
    c.start_agent({"prompt": "x"})
    assert _AgentHandler.last_x_authorization is None
    assert _AgentHandler.mint_count == 0


def test_auth_mints_jwt_and_sends_x_authorization(server):
    c = _client(server, auth=True)
    c.start_agent({"prompt": "x"})
    # ApiClient mints once (eagerly) and sends the JWT as X-Authorization.
    assert _AgentHandler.mint_count >= 1
    assert _AgentHandler.last_x_authorization == _JWT


def test_404_maps_to_agent_not_found(server):
    _AgentHandler.status_for_agent = 404
    c = _client(server)
    with pytest.raises(AgentNotFoundError) as exc:
        c.get_status("missing")
    assert exc.value.status_code == 404


def test_500_maps_to_agent_api_error(server):
    _AgentHandler.status_for_agent = 500
    c = _client(server)
    with pytest.raises(AgentAPIError) as exc:
        c.start_agent({"prompt": "x"})
    assert exc.value.status_code == 500
    assert not isinstance(exc.value, AgentNotFoundError)


def test_parse_sse_events_and_heartbeats():
    lines = [
        ": heartbeat",
        "event: thinking",
        'data: {"content": "processing"}',
        "",
        "event: done",
        "id: 42",
        'data: {"output": "result"}',
        "",
    ]
    events = list(OrkesAgentClient._parse_sse(iter(lines)))
    assert events[0] == {"_heartbeat": True}
    assert events[1]["event"] == "thinking"
    assert events[1]["data"]["content"] == "processing"
    assert events[2]["event"] == "done"
    assert events[2]["id"] == "42"
    assert events[2]["data"]["output"] == "result"
