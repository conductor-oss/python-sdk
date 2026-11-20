"""Run-scoped file storage behind the deep agent's file tools.

Every agent in a run sees one file tree. Two backends implement it:

- ``conductor`` (default): Conductor's file API. Each write uploads a new
  immutable file owned by the writing agent's execution, with the logical path
  in the file name. A path resolves to its newest version, so the last writer
  wins. The server lets a workflow read files owned by its ancestors and
  descendants, so a parent sees its sub-agents' files and a sub-agent sees its
  parent's. Sibling sub-agents do not see each other's files. Needs
  ``conductor.file-storage.enabled=true`` and the ``GET /api/files`` listing.
- ``local``: a directory per run on the worker's disk. For development only:
  workers on different machines do not share it.

Paths: ``/a/b.md`` is run-global. A relative path resolves to the calling
agent's home directory: the root for the top-level agent, and
``subagents/<name>-<id>`` for a sub-agent. A sub-agent may write only inside
its home directory; it may read any path it can see.
"""

from __future__ import annotations

import json
import os
import posixpath
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

from conductor.ai.agents.tool import ToolContext

STORAGE_ENV = "CONDUCTOR_DEEP_AGENT_STORAGE"
"""Selects the backend: ``conductor`` (default) or ``local``."""

SUBAGENTS_ENV = "CONDUCTOR_DEEP_AGENT_SUBAGENTS"
"""JSON list of sub-agent names, set by ``deep_agent()``.

Tool workers run in separate processes, so configuration travels through the
environment rather than a closure.
"""

WORKSPACE_ENV = "CONDUCTOR_DEEP_AGENT_WORKSPACE"
"""Root directory for the ``local`` backend."""

DEFAULT_WORKSPACE = "./workspace"


@dataclass
class FileEntry:
    """The newest version of one logical path."""

    path: str
    size: int
    owner: str = ""
    task_id: str = ""
    created_at: int = 0
    handle: Optional[str] = None


# ── paths ────────────────────────────────────────────────────────────────


def normalize(path: str) -> str:
    """Normalize a path to ``a/b.md`` form, refusing escapes from the run tree."""
    raw = (path or "").strip().lstrip("/")
    if not raw:
        return ""
    rel = posixpath.normpath(raw)
    if rel == ".":
        return ""
    if rel == ".." or rel.startswith("../"):
        raise ValueError(f"path {path!r} is outside the workspace")
    return rel


def subagent_names() -> List[str]:
    try:
        names = json.loads(os.environ.get(SUBAGENTS_ENV) or "[]")
    except ValueError:
        return []
    return [n for n in names if isinstance(n, str)]


def home_of(context: Optional[ToolContext]) -> str:
    """The calling agent's home directory: ``""`` for the top-level agent."""
    if context is None or context.agent_name not in subagent_names():
        return ""
    return f"subagents/{context.agent_name}-{(context.execution_id or 'local')[:8]}"


def resolve(context: Optional[ToolContext], path: str) -> str:
    """Resolve a tool path: absolute paths are run-global, relative ones start at home."""
    if (path or "").strip().startswith("/"):
        return normalize(path)
    return normalize(posixpath.join(home_of(context), (path or "").strip()))


SUBAGENTS_DIR = "subagents"


def check_writable(context: Optional[ToolContext], path: str) -> None:
    """Refuse writes outside the caller's own area.

    A sub-agent writes only inside its home directory. Every other agent,
    including the top-level one, may write anywhere except another sub-agent's
    directory, so what a sub-agent produced stays as it wrote it.
    """
    home = home_of(context)
    if not path:
        raise ValueError("path must name a file")
    if home:
        if path != home and not path.startswith(home + "/"):
            raise ValueError(
                f"a sub-agent may only write inside its own directory /{home}; "
                f"use a relative path such as {posixpath.basename(path)!r}"
            )
    elif path == SUBAGENTS_DIR or path.startswith(SUBAGENTS_DIR + "/"):
        raise ValueError(
            f"/{path} belongs to a sub-agent and only that sub-agent can change it; "
            "write your own file instead"
        )


# ── backends ─────────────────────────────────────────────────────────────


class _Backend:
    def list(self, context: Optional[ToolContext]) -> Dict[str, FileEntry]:
        raise NotImplementedError

    def read(self, context: Optional[ToolContext], entry: FileEntry) -> bytes:
        raise NotImplementedError

    def write(
        self, context: Optional[ToolContext], path: str, data: bytes
    ) -> Tuple[FileEntry, Optional[str]]:
        """Store *data* at *path*. Returns the entry and the previous owner if it differs."""
        raise NotImplementedError

    def written_by_task(self, context: Optional[ToolContext], path: str) -> Optional[FileEntry]:
        """The version of *path* this tool call already wrote, if it is a retried delivery."""
        return None


class LocalBackend(_Backend):
    """One directory per run, keyed by the root execution id."""

    def _root(self, context: Optional[ToolContext]) -> Path:
        from conductor.ai.agents.deep import _run_id  # root-id lookup lives with the harness

        base = Path(os.environ.get(WORKSPACE_ENV) or DEFAULT_WORKSPACE)
        root = (base / _run_id(context)).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    def list(self, context):
        root = self._root(context)
        out = {}
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                out[rel] = FileEntry(path=rel, size=p.stat().st_size)
        return out

    def read(self, context, entry):
        return (self._root(context) / entry.path).read_bytes()

    def write(self, context, path, data):
        target = self._root(context) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return FileEntry(path=path, size=len(data)), None


class ConductorBackend(_Backend):
    """Conductor's file API. Every write is a new version; the newest one wins."""

    def __init__(self):
        self._client = None
        self._lock = threading.Lock()

    def _files(self):
        with self._lock:
            if self._client is None:
                from conductor.client.configuration.configuration import Configuration
                from conductor.client.file_client import FileClient

                self._client = FileClient(Configuration())
            return self._client

    def _execution(self, context: Optional[ToolContext]) -> str:
        if context is None or not context.execution_id:
            raise ValueError("the conductor file backend needs a running execution")
        return context.execution_id

    def versions(self, context: Optional[ToolContext]) -> List[Dict[str, Any]]:
        """Every uploaded version visible to the caller, oldest first."""
        client = self._files()
        items = client._api_client.call_api(  # listing is not in FileClient yet
            "/files",
            "GET",
            {},
            [("workflowId", self._execution(context))],
            {"Accept": "application/json"},
            response_type="object",
            auth_settings=["api_key"],
            _return_http_data_only=True,
            _preload_content=True,
        )
        return list(items or [])

    def list(self, context):
        out: Dict[str, FileEntry] = {}
        for item in self.versions(context):
            path = unquote(item.get("fileName") or "")
            if not path:
                continue
            out[path] = _entry(path, item)  # oldest first, so the newest version wins
        return out

    def read(self, context, entry):
        return self._files().download_bytes(self._execution(context), entry.handle)

    def written_by_task(self, context, path):
        task_id = context.task_id if context else ""
        if not task_id:
            return None
        execution = self._execution(context)
        for item in self.versions(context):
            if (
                unquote(item.get("fileName") or "") == path
                and item.get("taskId") == task_id
                and item.get("workflowId") == execution
            ):
                return _entry(path, item)
        return None

    def write(self, context, path, data):
        from conductor.client.file_client import FileUploadOptions

        execution = self._execution(context)
        task_id = context.task_id if context else ""
        previous = None
        for item in self.versions(context):
            if unquote(item.get("fileName") or "") != path:
                continue
            # A retried delivery of the same tool call: return what it already wrote.
            if task_id and item.get("taskId") == task_id and item.get("workflowId") == execution:
                return _entry(path, item), None
            previous = item
        handle = self._files().upload_bytes(
            execution,
            data,
            FileUploadOptions(
                file_name=quote(path, safe=""),
                content_type="text/plain; charset=utf-8",
                task_id=task_id or None,
            ),
        )
        entry = FileEntry(
            path=path, size=len(data), owner=execution, task_id=task_id, handle=handle
        )
        replaced = None
        if previous is not None and previous.get("workflowId") != execution:
            replaced = previous.get("workflowId")
        return entry, replaced


def _entry(path: str, item: Dict[str, Any]) -> FileEntry:
    return FileEntry(
        path=path,
        size=int(item.get("fileSize") or 0),
        owner=item.get("workflowId") or "",
        task_id=item.get("taskId") or "",
        created_at=int(item.get("createdAt") or 0),
        handle=item.get("fileHandleId"),
    )


_conductor_backend = ConductorBackend()
_local_backend = LocalBackend()


def backend() -> _Backend:
    if (os.environ.get(STORAGE_ENV) or "conductor").strip().lower() == "local":
        return _local_backend
    return _conductor_backend


# ── helpers for code outside the agent ──────────────────────────────────


def list_run_files(execution_id: str) -> Dict[str, FileEntry]:
    """Every file in a run, newest version per path. Pass the root execution id."""
    return backend().list(ToolContext(execution_id=execution_id))


def read_run_file(execution_id: str, path: str) -> str:
    """Read one file of a run as text. Pass the root execution id."""
    context = ToolContext(execution_id=execution_id)
    entry = backend().list(context).get(normalize(path))
    if entry is None:
        raise FileNotFoundError(path)
    return backend().read(context, entry).decode("utf-8")


def export_files(
    context: Optional[ToolContext], dest: "os.PathLike[str] | str", prefix: str = ""
) -> List[str]:
    """Copy the newest version of every file the caller can see into *dest*.

    Paths keep their workspace layout under *dest*. Pass *prefix* (a workspace
    path such as ``"/src"``) to export one directory only. Returns the exported
    workspace paths. Used to run tools such as test runners over the workspace,
    and to inspect a run's files on disk.
    """
    root = Path(dest)
    want = normalize(prefix)
    store = backend()
    exported = []
    for path, entry in store.list(context).items():
        if want and path != want and not path.startswith(want + "/"):
            continue
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(store.read(context, entry))
        exported.append(path)
    return exported


def export_run(execution_id: str, dest: "os.PathLike[str] | str", prefix: str = "") -> List[str]:
    """Copy a run's files into *dest* for inspection. Pass the root execution id."""
    return export_files(ToolContext(execution_id=execution_id), dest, prefix)
