"""Tests for the deep agent's Conductor file backend.

Uses a real in-process HTTP server (no mocks, per repo test policy) that emulates
the file API, including ``GET /api/files?workflowId=`` (a ``SearchResult``) and the workflow-family
access rule: a workflow sees files owned by itself, its ancestors and its
descendants.
"""

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from conductor.ai.agents import deep_files
from conductor.ai.agents.deep import (
    STORAGE_ENV,
    SUBAGENTS_ENV,
    edit_file,
    ls,
    read_file,
    write_file,
)
from conductor.ai.agents.tool import ToolContext

# root has two sub-agent executions; they are siblings.
PARENTS = {"sub-a": "root", "sub-b": "root"}


def family(wf):
    out = {wf}
    p = wf
    while p in PARENTS:
        p = PARENTS[p]
        out.add(p)
    out.update(c for c, parent in PARENTS.items() if parent == wf)
    return out


class _State:
    def reset(self):
        self.records = {}
        self.content = {}
        self.clock = 0
        self.base = ""


STATE = _State()


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

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def do_POST(self):
        if self.path == "/api/files":
            req = json.loads(self._body())
            STATE.clock += 1
            file_id = f"f{STATE.clock}"
            STATE.records[file_id] = {
                "fileHandleId": f"conductor://file/{file_id}",
                "fileName": req.get("fileName"),
                "workflowId": req["workflowId"],
                "taskId": req.get("taskId"),
                "storageType": "CONDUCTOR",
                "uploadStatus": "UPLOADING",
                "createdAt": STATE.clock,
            }
            return self._json(201, {
                **STATE.records[file_id],
                "uploadUrl": f"{STATE.base}/api/files/content/{req['workflowId']}/{file_id}",
            })
        m = re.fullmatch(r"/api/files/([^/]+)/([^/]+)/upload-complete", self.path)
        if m:
            rec = STATE.records[m.group(2)]
            rec["uploadStatus"] = "UPLOADED"
            rec["fileSize"] = len(STATE.content.get(m.group(2), b""))
            return self._json(200, {"uploadStatus": "UPLOADED"})
        return self._json(404, {})

    def do_PUT(self):
        m = re.fullmatch(r"/api/files/content/([^/]+)/([^/]+)", self.path)
        STATE.content[m.group(2)] = self._body()
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/files":
            caller = parse_qs(url.query)["workflowId"][0]
            visible = family(caller)
            items = [r for r in STATE.records.values()
                     if r["uploadStatus"] == "UPLOADED" and r["workflowId"] in visible]
            results = sorted(items, key=lambda r: r["createdAt"])
            return self._json(200, {"totalHits": len(results), "results": results})
        m = re.fullmatch(r"/api/files/content/([^/]+)/([^/]+)", url.path)
        if m:
            data = STATE.content[m.group(2)]
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        m = re.fullmatch(r"/api/files/([^/]+)/([^/]+)/download-url", url.path)
        if m:
            caller, file_id = m.groups()
            if STATE.records[file_id]["workflowId"] not in family(caller):
                return self._json(403, {"message": "forbidden"})
            return self._json(200, {"downloadUrl":
                                    f"{STATE.base}/api/files/content/{caller}/{file_id}"})
        return self._json(404, {})


@pytest.fixture(scope="module")
def server():
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd
    httpd.shutdown()


@pytest.fixture
def files(server, monkeypatch):
    STATE.reset()
    STATE.base = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("CONDUCTOR_SERVER_URL", f"{STATE.base}/api")
    monkeypatch.setenv(STORAGE_ENV, "conductor")
    monkeypatch.setenv(SUBAGENTS_ENV, '["analyst"]')
    # A fresh client per test so it picks up this server's URL.
    monkeypatch.setattr(deep_files, "_conductor_backend", deep_files.ConductorBackend())
    return STATE


def ctx(execution_id="root", agent_name="planner", task_id="t1"):
    return ToolContext(execution_id=execution_id, agent_name=agent_name, task_id=task_id)


def test_write_then_read_and_list(files):
    out = write_file.__wrapped__(path="notes/a.md", content="one\ntwo", context=ctx())
    assert out == {"path": "/notes/a.md", "bytes": 7}

    assert read_file.__wrapped__(path="/notes/a.md", context=ctx())["content"] == "one\ntwo"
    listing = ls.__wrapped__(path="notes", context=ctx())
    assert listing["entries"] == [
        {"name": "a.md", "type": "file", "size": 7, "written_by": "you"}
    ]
    # The logical path travels in the file name, encoded so it has no slash.
    assert next(iter(files.records.values()))["fileName"] == "notes%2Fa.md"


def test_newest_version_wins_and_versions_are_kept(files):
    write_file.__wrapped__(path="r.md", content="v1", context=ctx(task_id="t1"))
    write_file.__wrapped__(path="r.md", content="v2", context=ctx(task_id="t2"))

    assert read_file.__wrapped__(path="r.md", context=ctx())["content"] == "v2"
    assert len(files.records) == 2


def test_retried_write_does_not_create_another_version(files):
    write_file.__wrapped__(path="r.md", content="v1", context=ctx(task_id="t1"))
    write_file.__wrapped__(path="r.md", content="v1", context=ctx(task_id="t1"))

    assert len(files.records) == 1


def test_retried_edit_is_not_applied_twice(files):
    write_file.__wrapped__(path="r.md", content="a b", context=ctx(task_id="t1"))
    first = edit_file.__wrapped__(
        path="r.md", old_string="a", new_string="z", context=ctx(task_id="t2")
    )
    again = edit_file.__wrapped__(
        path="r.md", old_string="a", new_string="z", context=ctx(task_id="t2")
    )

    assert first["replacements"] == 1
    assert again["note"] == "already applied"
    assert read_file.__wrapped__(path="r.md", context=ctx())["content"] == "z b"
    assert len(files.records) == 2


def test_parent_and_subagent_see_each_others_files(files):
    sub = ctx(execution_id="sub-a", agent_name="analyst", task_id="s1")
    out = write_file.__wrapped__(path="result.md", content="r", context=sub)
    assert out["path"] == "/subagents/analyst-sub-a/result.md"

    parent = ctx()
    got = read_file.__wrapped__(path=out["path"], context=parent)
    assert got["content"] == "r"
    assert ls.__wrapped__(path=out["path"].rsplit("/", 1)[0], context=parent)["entries"][0][
        "written_by"
    ] == "another agent (sub-a)"

    write_file.__wrapped__(path="/brief.md", content="b", context=parent)
    assert read_file.__wrapped__(path="/brief.md", context=sub)["content"] == "b"


def test_sibling_subagents_do_not_see_each_others_files(files):
    a = ctx(execution_id="sub-a", agent_name="analyst", task_id="s1")
    b = ctx(execution_id="sub-b", agent_name="analyst", task_id="s2")
    path = write_file.__wrapped__(path="result.md", content="r", context=a)["path"]

    assert read_file.__wrapped__(path=path, context=b)["error"] == "no such file"


def test_overwriting_another_agents_version_is_reported(files):
    write_file.__wrapped__(path="/shared.md", content="sub", context=ctx("sub-a", "x", "s1"))
    out = write_file.__wrapped__(path="/shared.md", content="parent", context=ctx())

    assert out["note"] == "This replaced a version written by another agent (sub-a)."


def test_read_run_file_and_list_run_files(files):
    write_file.__wrapped__(path="report.md", content="final", context=ctx())

    assert deep_files.read_run_file("root", "/report.md") == "final"
    assert list(deep_files.list_run_files("root")) == ["report.md"]


def test_export_run_downloads_every_visible_file(files, tmp_path):
    write_file.__wrapped__(path="/src/m.py", content="x = 1", context=ctx())
    sub = ctx(execution_id="sub-a", agent_name="analyst", task_id="s1")
    tests = write_file.__wrapped__(path="test_m.py", content="t", context=sub)["path"]

    exported = deep_files.export_run("root", tmp_path)

    assert sorted(exported) == sorted(["src/m.py", tests.lstrip("/")])
    assert (tmp_path / "src" / "m.py").read_text() == "x = 1"
