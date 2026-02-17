import json
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Value
from typing import Optional


class FakeConductorSharedState:
    """
    Shared state for the fake server.

    Uses multiprocessing.Value (shared memory) to avoid requiring a local manager server,
    which may be blocked in some sandboxed environments.
    """
    def __init__(self):
        self.drop_first_n = Value("i", 0)
        self.requests_total = Value("i", 0)
        self.drops_total = Value("i", 0)
        self.poll_requests = Value("i", 0)
        self.poll_responses = Value("i", 0)
        self.update_requests = Value("i", 0)
        self.update_responses = Value("i", 0)

    def _inc(self, counter: Value, n: int = 1) -> None:
        with counter.get_lock():
            counter.value += n

    def _get(self, counter: Value) -> int:
        with counter.get_lock():
            return int(counter.value)

    def _set(self, counter: Value, value: int) -> None:
        with counter.get_lock():
            counter.value = int(value)


class FakeConductorHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, state: FakeConductorSharedState):
        super().__init__(server_address, RequestHandlerClass)
        self.state = state


class FakeConductorHandler(BaseHTTPRequestHandler):
    # Keep the handler quiet; chaos harness can print summaries itself.
    def log_message(self, format, *args):
        return

    def _should_drop(self) -> bool:
        # Deterministic: drop first N requests.
        remaining = self.server.state._get(self.server.state.drop_first_n)
        if remaining > 0:
            self.server.state._set(self.server.state.drop_first_n, remaining - 1)
            return True
        return False

    def _drop_connection(self) -> None:
        self.server.state._inc(self.server.state.drops_total)
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.connection.close()
        except Exception:
            pass

    def do_GET(self) -> None:
        self.server.state._inc(self.server.state.requests_total)

        if self._should_drop():
            self._drop_connection()
            return

        # Task poll used by TaskRunner: GET /api/tasks/poll/batch/{tasktype}
        if self.path.startswith("/api/tasks/poll/batch/"):
            self.server.state._inc(self.server.state.poll_requests)
            payload = "[]"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))
            self.server.state._inc(self.server.state.poll_responses)
            return

        if self.path == "/api/health":
            payload = json.dumps({"ok": True, "ts": time.time()})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        self.server.state._inc(self.server.state.requests_total)

        if self._should_drop():
            self._drop_connection()
            return

        # Task update used by TaskRunner: POST /api/tasks
        if self.path == "/api/tasks":
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > 0:
                _ = self.rfile.read(content_length)
            self.server.state._inc(self.server.state.update_requests)
            payload = "OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))
            self.server.state._inc(self.server.state.update_responses)
            return

        self.send_response(404)
        self.end_headers()


def serve_fake_conductor(shared_state: FakeConductorSharedState, port_queue, stop_event) -> None:
    """
    Run a minimal HTTP server that implements just enough Conductor endpoints for TaskRunner:
    - GET /api/tasks/poll/batch/{tasktype}
    - POST /api/tasks

    Supports request dropping via shared_state.drop_first_n.
    """
    server = FakeConductorHTTPServer(("127.0.0.1", 0), FakeConductorHandler, state=shared_state)
    server.timeout = 0.2
    port_queue.put(server.server_address[1])

    while not stop_event.is_set():
        server.handle_request()

    try:
        server.server_close()
    except Exception:
        pass
