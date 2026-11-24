"""Tests for FileClient, the /api/files client.

Uses a real in-process HTTP server (no mocks, per repo test policy) that emulates
the file API with the Conductor-managed backend: file records, the raw content
endpoints the server hands out as upload and download URLs, and the
upload-complete transition.
"""

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.file_client import (
    FileClient,
    FileStorageError,
    FileUploadOptions,
)


class _FileServer:
    """In-memory state shared by the handler."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.records = {}
        self.content = {}
        self.next_id = 0
        self.requests = []
        # Failure knobs: number of times to fail, and with which status.
        self.fail_put = 0
        self.fail_put_status = 503
        self.fail_complete = 0
        self.storage_type = "CONDUCTOR"
        self.base = ""


STATE = _FileServer()


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _empty(self, status):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _record(self):
        STATE.requests.append((self.command, self.path, dict(self.headers)))

    def do_POST(self):
        self._record()
        if self.path == "/api/files":
            req = json.loads(self._body())
            STATE.next_id += 1
            file_id = f"f{STATE.next_id}"
            STATE.records[file_id] = {
                "fileHandleId": f"conductor://file/{file_id}",
                "fileName": req.get("fileName"),
                "contentType": req.get("contentType"),
                "workflowId": req["workflowId"],
                "taskId": req.get("taskId"),
                "storageType": STATE.storage_type,
                "uploadStatus": "UPLOADING",
            }
            return self._json(
                201,
                {
                    **STATE.records[file_id],
                    "uploadUrl": f"{STATE.base}/api/files/content/{req['workflowId']}/{file_id}",
                },
            )
        m = re.fullmatch(r"/api/files/([^/]+)/([^/]+)/upload-complete", self.path)
        if m:
            wf, file_id = m.groups()
            rec = STATE.records.get(file_id)
            if rec is None or rec["workflowId"] != wf:
                return self._json(403, {"message": "forbidden"})
            if STATE.fail_complete:
                STATE.fail_complete -= 1
                # The server applied the change but the response was lost.
                rec["uploadStatus"] = "UPLOADED"
                return self._json(503, {"message": "unavailable"})
            if rec["uploadStatus"] == "UPLOADED":
                return self._json(409, {"message": "already uploaded"})
            rec["uploadStatus"] = "UPLOADED"
            rec["fileSize"] = len(STATE.content.get(file_id, b""))
            return self._json(
                200, {"fileHandleId": rec["fileHandleId"], "uploadStatus": "UPLOADED"}
            )
        return self._json(404, {"message": "not found"})

    def do_PUT(self):
        self._record()
        m = re.fullmatch(r"/api/files/content/([^/]+)/([^/]+)", self.path)
        if not m:
            return self._json(404, {})
        body = self._body()
        if STATE.fail_put:
            STATE.fail_put -= 1
            return self._empty(STATE.fail_put_status)
        STATE.content[m.group(2)] = body
        return self._empty(204)

    def do_GET(self):
        self._record()
        m = re.fullmatch(r"/api/files/content/([^/]+)/([^/]+)", self.path)
        if m:
            data = STATE.content.get(m.group(2))
            if data is None:
                return self._json(404, {})
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        m = re.fullmatch(r"/api/files/([^/]+)/([^/]+)(/[a-z-]+)?", self.path)
        if not m:
            return self._json(404, {})
        wf, file_id, suffix = m.groups()
        rec = STATE.records.get(file_id)
        if rec is None:
            return self._json(404, {"message": "not found"})
        if suffix is None:
            return self._json(200, rec)
        if suffix == "/upload-url":
            return self._json(
                200,
                {
                    "fileHandleId": rec["fileHandleId"],
                    "uploadUrl": f"{STATE.base}/api/files/content/{wf}/{file_id}",
                },
            )
        if suffix == "/download-url":
            if rec["uploadStatus"] != "UPLOADED":
                return self._json(400, {"message": "not uploaded"})
            return self._json(
                200,
                {
                    "fileHandleId": rec["fileHandleId"],
                    "downloadUrl": f"{STATE.base}/api/files/content/{wf}/{file_id}",
                },
            )
        return self._json(404, {})


@pytest.fixture(scope="module")
def server():
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    STATE.base = f"http://127.0.0.1:{httpd.server_port}"
    yield httpd
    httpd.shutdown()


@pytest.fixture
def client(server):
    STATE.reset()
    STATE.base = f"http://127.0.0.1:{server.server_port}"
    config = Configuration(server_api_url=f"{STATE.base}/api")
    return FileClient(config, retry_count=2)


def test_upload_and_download_bytes_round_trip(client):
    handle = client.upload_bytes(
        "wf-1", b"hello", FileUploadOptions(file_name="a.txt", content_type="text/plain")
    )

    assert handle == "conductor://file/f1"
    assert client.download_bytes("wf-1", handle) == b"hello"
    meta = client.get_metadata("wf-1", handle)
    assert meta.upload_status == "UPLOADED"
    assert meta.file_name == "a.txt"
    assert meta.content_type == "text/plain"
    assert meta.workflow_id == "wf-1"


def test_upload_path_uses_file_name_and_default_content_type(client, tmp_path):
    source = tmp_path / "report.md"
    source.write_text("# report")

    handle = client.upload("wf-1", source)

    meta = client.get_metadata("wf-1", handle)
    assert meta.file_name == "report.md"
    assert meta.content_type == "application/octet-stream"


def test_upload_records_task_id(client):
    handle = client.upload_bytes(
        "wf-1", b"x", FileUploadOptions(file_name="a.txt", task_id="task-9")
    )

    assert client.get_metadata("wf-1", handle).task_id == "task-9"


def test_download_to_path_replaces_destination(client, tmp_path):
    handle = client.upload_bytes("wf-1", b"new", FileUploadOptions(file_name="a.txt"))
    target = tmp_path / "out" / "a.txt"
    target.parent.mkdir()
    target.write_bytes(b"old")

    result = client.download("wf-1", handle, target)

    assert result == target
    assert target.read_bytes() == b"new"
    assert [p.name for p in target.parent.iterdir()] == ["a.txt"]


def test_upload_retries_transient_put_failure_with_fresh_url(client):
    STATE.fail_put = 1

    handle = client.upload_bytes("wf-1", b"data", FileUploadOptions(file_name="a.txt"))

    assert client.download_bytes("wf-1", handle) == b"data"
    paths = [p for (m, p, _) in STATE.requests]
    assert "/api/files/wf-1/f1/upload-url" in paths


def test_upload_fails_fast_on_non_retryable_put_status(client):
    STATE.fail_put = 1
    STATE.fail_put_status = 400

    with pytest.raises(FileStorageError) as err:
        client.upload_bytes("wf-1", b"data", FileUploadOptions(file_name="a.txt"))

    assert "HTTP 400" in str(err.value)


def test_upload_gives_up_after_retry_count(client):
    STATE.fail_put = 10

    with pytest.raises(FileStorageError):
        client.upload_bytes("wf-1", b"data", FileUploadOptions(file_name="a.txt"))

    puts = [p for (m, p, _) in STATE.requests if m == "PUT"]
    assert len(puts) == 3


def test_lost_completion_response_is_reconciled(client):
    STATE.fail_complete = 1

    handle = client.upload_bytes("wf-1", b"data", FileUploadOptions(file_name="a.txt"))

    assert client.get_metadata("wf-1", handle).upload_status == "UPLOADED"


def test_azure_upload_sends_block_blob_header(client):
    STATE.storage_type = "AZURE_BLOB"

    client.upload_bytes("wf-1", b"data", FileUploadOptions(file_name="a.txt"))

    put_headers = [h for (m, _, h) in STATE.requests if m == "PUT"][0]
    assert put_headers.get("x-ms-blob-type") == "BlockBlob"


def test_transfers_do_not_send_conductor_credentials(client):
    client.upload_bytes("wf-1", b"data", FileUploadOptions(file_name="a.txt"))

    put_headers = [h for (m, _, h) in STATE.requests if m == "PUT"][0]
    assert "X-Authorization" not in put_headers


@pytest.mark.parametrize("name", ["", ".", "..", "a/b.txt", "a\\b.txt", "a:b", "x" * 256])
def test_unsafe_file_names_are_rejected(client, name):
    with pytest.raises(FileStorageError):
        client.upload_bytes("wf-1", b"x", FileUploadOptions(file_name=name))
    assert STATE.requests == []


@pytest.mark.parametrize(
    "handle", [None, "", "f1", "s3://file/f1", "conductor://file/", "conductor://file/../x"]
)
def test_malformed_handles_are_rejected(client, handle):
    with pytest.raises(FileStorageError):
        client.download_bytes("wf-1", handle)
    assert STATE.requests == []


def test_workflow_id_is_required(client):
    with pytest.raises(FileStorageError):
        client.upload_bytes("", b"x", FileUploadOptions(file_name="a.txt"))


def test_upload_bytes_requires_file_name(client):
    with pytest.raises(FileStorageError):
        client.upload_bytes("wf-1", b"x", FileUploadOptions())


def test_download_destination_must_not_be_a_directory(client, tmp_path):
    handle = client.upload_bytes("wf-1", b"x", FileUploadOptions(file_name="a.txt"))

    with pytest.raises(FileStorageError):
        client.download("wf-1", handle, tmp_path)
