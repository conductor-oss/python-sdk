"""Deep agent harness: planning, files and sub-agents on top of a plain ``Agent``.

A deep agent runs for a long time and does many steps. The harness keeps three
things out of the conversation so the model's context stays small:

- the plan, in ``_agent_state`` through :func:`write_todos`, private to the
  agent that wrote it and shown to it on every turn;
- large data, in files under a per-run workspace directory, shared with the
  sub-agents of the same run;
- delegated work, in sub-agents that return a short result and never see the
  parent's plan or history.

This is a proof of concept on the Python SDK alone: the todo and file tools are
ordinary ``@tool`` workers. See ``examples/agents/deep_agent_research.py``.

Example::

    from conductor.ai.agents.deep import deep_agent

    agent = deep_agent(
        name="researcher",
        model="openai/gpt-4o-mini",
        instructions="You are a travel assistant.",
        tools=[get_weather],
        subagents=[weather_analyst],
        workspace="./workspace",
        approval=["write_file"],
    )
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import os
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from conductor.ai.agents.agent import Agent
from conductor.ai.agents.tool import ToolContext, agent_tool, get_tool_def, tool
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients

WORKSPACE_ENV = "CONDUCTOR_DEEP_AGENT_WORKSPACE"
"""Environment variable naming the workspace root directory.

Tool workers run in separate processes, so the root is passed through the
environment rather than captured in a closure.
"""

DEFAULT_WORKSPACE = "./workspace"

TODOS_KEY = "todos"
"""Key under which the plan lives in ``ToolContext.state`` (``_agent_state``).

The value is ``{"items": [...]}`` rather than a bare list: the server merges a
list-valued update by appending its new items to the stored list, which would
keep every superseded step; an object-valued update replaces the stored one.
"""

TODO_STATUSES = ("pending", "in_progress", "completed")

FILE_TOOL_NAMES = ("ls", "read_file", "write_file", "edit_file")

DEFAULT_INSTRUCTIONS = """\
You are a capable agent that works through long tasks step by step. You have a
plan, a file workspace, and possibly sub-agents. Use them like this.

## Plan first with write_todos
If the task needs more than one step, your first action is write_todos with the
full list of steps, each with status "pending". Do this before any other tool
call. Then, as you work: set a step to "in_progress" when you start it, and
call write_todos again to mark it "completed" the moment it is done. Send the
whole list every time; it replaces the previous one. Call write_todos only when
a status changes, never twice in a row, and never skip the plan on a multi-step
task. Your current plan is shown to you under "Context" on every turn.

## Files
The workspace is private to this run. Paths are relative to it; "/report.md"
and "report.md" are the same file. Write anything long or anything worth
keeping to a file instead of repeating it in the conversation: research notes,
drafts, the final report. Read a file only when you need its content. Use
edit_file for small changes; use write_file to create or replace a whole file.
Use the file names your instructions ask for.

## Sub-agents
Each sub-agent is a tool. Delegate a self-contained piece of work with a clear
request and everything it needs to know; it does not see your plan or this
conversation. Ask it to write long results to a file in the workspace and to
return a short summary plus the file path. Delegate when a step would otherwise
fill your context with material you only need a summary of.

## Finishing
When every step is completed, give the user the result they asked for in your
final message, in the same turn or the next one. Marking the last todo
completed is not an answer, and the plan does not need further edits once it
is complete. If something cannot be done, say so and finish; do not rewrite
the plan to work around it.
"""


# ── Plan ────────────────────────────────────────────────────────────────


def _validate_todos(todos: Any) -> List[Dict[str, str]]:
    if not isinstance(todos, list):
        raise ValueError("todos must be a list of {content, status} items")
    cleaned: List[Dict[str, str]] = []
    for i, item in enumerate(todos):
        if not isinstance(item, dict):
            raise ValueError(f"todos[{i}] must be an object with content and status")
        content = str(item.get("content", "")).strip()
        status = str(item.get("status", "pending")).strip().lower()
        if not content:
            raise ValueError(f"todos[{i}].content is empty")
        if status not in TODO_STATUSES:
            raise ValueError(
                f"todos[{i}].status is {status!r}; expected one of {', '.join(TODO_STATUSES)}"
            )
        cleaned.append({"content": content, "status": status})
    return cleaned


@tool
def write_todos(todos: List[Dict[str, Any]], context: ToolContext = None) -> dict:
    """Replace the plan for this run with a new list of steps.

    Each item is {"content": "<what to do>", "status": "pending" | "in_progress" | "completed"}.
    Send the complete list every time; it replaces the previous plan. Keep one
    item in_progress at a time and mark a step completed as soon as it is done.

    Args:
        todos: The full list of steps with their current status.

    Returns:
        The stored plan and a one-line progress summary.
    """
    cleaned = _validate_todos(todos)
    previous = stored_todos(context.state) if context is not None else None
    if context is not None:
        context.state[TODOS_KEY] = {"items": cleaned}
    done = sum(1 for t in cleaned if t["status"] == "completed")
    out: Dict[str, Any] = {"todos": cleaned, "summary": f"{done}/{len(cleaned)} completed"}
    # A clear stop signal: models otherwise keep polishing a finished plan
    # instead of answering, until the turn limit ends the run.
    if done == len(cleaned):
        out["next"] = (
            "All steps are completed. Reply to the user with the result now; "
            "do not call write_todos again."
        )
    elif previous == cleaned:
        out["next"] = "The plan is unchanged. Continue with the in-progress step."
    return out


def stored_todos(state: Optional[Dict[str, Any]]) -> Optional[List[Dict[str, str]]]:
    """The plan held in an agent state dict, or None when none was written."""
    if not state:
        return None
    value = state.get(TODOS_KEY)
    if isinstance(value, dict):
        items = value.get("items")
        return list(items) if isinstance(items, list) else None
    return None


# The reflected schema for List[Dict[str, Any]] has no item properties, which
# leaves weaker models guessing the field names. Spell the item out.
write_todos._tool_def.input_schema = {  # type: ignore[attr-defined]
    "type": "object",
    "properties": {
        "todos": {
            "type": "array",
            "description": "The full list of steps with their current status.",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "What this step does."},
                    "status": {"type": "string", "enum": list(TODO_STATUSES)},
                },
                "required": ["content", "status"],
            },
        }
    },
    "required": ["todos"],
}


# ── Workspace ───────────────────────────────────────────────────────────

_root_cache: Dict[str, str] = {}
_root_lock = threading.Lock()


def resolve_root_execution_id(execution_id: str, workflow_client: Any) -> str:
    """Walk ``parent_workflow_id`` up from *execution_id* to the root run.

    A sub-agent runs as a sub-workflow with its own execution id; its files
    must land in the parent's workspace, so the directory is keyed by the root.
    Any lookup failure stops the walk and returns the furthest id reached.
    """
    root = execution_id
    seen = set()
    current = execution_id
    while current and current not in seen:
        seen.add(current)
        parent = _parent_of(workflow_client, current)
        if not parent:
            break
        root = parent
        current = parent
    return root


def _parent_of(workflow_client: Any, execution_id: str) -> Optional[str]:
    try:
        wf = workflow_client.get_workflow(execution_id, include_tasks=False)
    except Exception:
        return None
    return getattr(wf, "parent_workflow_id", None)


def _root_execution_id(execution_id: str) -> str:
    with _root_lock:
        cached = _root_cache.get(execution_id)
    if cached:
        return cached
    try:
        client = OrkesClients(configuration=Configuration()).get_workflow_client()
        root = resolve_root_execution_id(execution_id, client)
    except Exception:
        root = execution_id
    with _root_lock:
        _root_cache[execution_id] = root
    return root


def _run_id(context: Optional[ToolContext]) -> str:
    if context is None or not context.execution_id:
        return "local"
    return _root_execution_id(context.execution_id)


def _workspace_root(context: Optional[ToolContext]) -> Path:
    base = Path(os.environ.get(WORKSPACE_ENV) or DEFAULT_WORKSPACE)
    root = (base / _run_id(context)).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve(root: Path, path: str) -> Path:
    """Map a model-supplied path onto the workspace, refusing escapes."""
    rel = (path or "").strip().lstrip("/")
    target = (root / rel).resolve() if rel else root
    if target != root and root not in target.parents:
        raise ValueError(f"path {path!r} is outside the workspace")
    return target


# ── File tools ──────────────────────────────────────────────────────────


@tool
def ls(path: str = "/", context: ToolContext = None) -> dict:
    """List the files and directories at a path in the workspace.

    Args:
        path: Directory to list, relative to the workspace root. Default is the root.

    Returns:
        The entries with their type and size in bytes.
    """
    root = _workspace_root(context)
    target = _resolve(root, path)
    if not target.exists():
        return {"path": path, "entries": [], "error": "no such directory"}
    if not target.is_dir():
        return {"path": path, "entries": [], "error": "not a directory"}
    entries = [
        {
            "name": p.name,
            "type": "dir" if p.is_dir() else "file",
            "size": p.stat().st_size if p.is_file() else 0,
        }
        for p in sorted(target.iterdir())
    ]
    return {"path": path, "entries": entries}


@tool
def read_file(path: str, offset: int = 0, limit: int = 2000, context: ToolContext = None) -> dict:
    """Read a text file from the workspace.

    Args:
        path: File path relative to the workspace root.
        offset: First line to return, counting from 0.
        limit: Maximum number of lines to return.

    Returns:
        The requested lines and the file's total line count.
    """
    root = _workspace_root(context)
    target = _resolve(root, path)
    if not target.is_file():
        return {"path": path, "error": "no such file"}
    lines = target.read_text(encoding="utf-8").splitlines()
    chunk = lines[offset : offset + limit]
    return {
        "path": path,
        "content": "\n".join(chunk),
        "total_lines": len(lines),
        "offset": offset,
        "returned_lines": len(chunk),
    }


@tool
def write_file(path: str, content: str, context: ToolContext = None) -> dict:
    """Create or replace a text file in the workspace.

    Args:
        path: File path relative to the workspace root. Parent directories are created.
        content: The full file content.

    Returns:
        The path written and its size in bytes.
    """
    root = _workspace_root(context)
    target = _resolve(root, path)
    if target == root:
        raise ValueError("path must name a file")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode("utf-8")
    target.write_bytes(data)
    return {"path": path, "bytes": len(data)}


@tool
def edit_file(
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    context: ToolContext = None,
) -> dict:
    """Replace text in a workspace file.

    Args:
        path: File path relative to the workspace root.
        old_string: The exact text to find. It must occur once unless replace_all is set.
        new_string: The replacement text.
        replace_all: Replace every occurrence instead of requiring a unique match.

    Returns:
        The path edited and how many replacements were made.
    """
    root = _workspace_root(context)
    target = _resolve(root, path)
    if not target.is_file():
        return {"path": path, "error": "no such file"}
    if not old_string:
        raise ValueError("old_string is empty")
    text = target.read_text(encoding="utf-8")
    count = text.count(old_string)
    if count == 0:
        return {"path": path, "error": "old_string not found", "replacements": 0}
    if count > 1 and not replace_all:
        return {
            "path": path,
            "error": f"old_string occurs {count} times; include more context or set replace_all",
            "replacements": 0,
        }
    updated = (
        text.replace(old_string, new_string)
        if replace_all
        else text.replace(old_string, new_string, 1)
    )
    target.write_text(updated, encoding="utf-8")
    return {"path": path, "replacements": count if replace_all else 1}


FILE_TOOLS = (ls, read_file, write_file, edit_file)


# ── Harness entry point ─────────────────────────────────────────────────


def _with_approval(obj: Any, approval: Iterable[str]) -> Any:
    """Return *obj* with approval_required set when its name is in *approval*."""
    names = set(approval)
    if not names:
        return obj
    td = get_tool_def(obj)
    if td.name not in names or td.approval_required:
        return obj
    return dataclasses.replace(td, approval_required=True)


def _name_of(obj: Any) -> Optional[str]:
    try:
        return get_tool_def(obj).name
    except TypeError:
        return None


def _tool_names(tools: Sequence[Any]) -> set:
    return {n for n in (_name_of(t) for t in tools) if n}


def _describe(sub: Agent) -> str:
    meta = getattr(sub, "metadata", None) or {}
    desc = meta.get("description")
    if desc:
        return str(desc)
    return f"Delegate a self-contained task to the {sub.name} agent. Give it everything it needs."


def deep_agent(
    name: str,
    *,
    model: Union[str, Any] = "",
    instructions: str = "",
    tools: Optional[Sequence[Any]] = None,
    subagents: Optional[Sequence[Agent]] = None,
    workspace: Optional[Union[str, Path]] = None,
    approval: Iterable[str] = (),
    max_turns: int = 50,
    **agent_kwargs: Any,
) -> Agent:
    """Build an :class:`Agent` with planning, file tools and sub-agents.

    Args:
        name: Agent name.
        model: Model for the agent, as ``provider/model``.
        instructions: Your instructions. They follow the harness's default
            prompt, which explains planning, files and delegation.
        tools: Your own tools, in addition to the harness tools.
        subagents: Agents to expose as tools. Each gets the file tools so it
            can write to the shared workspace, and does not get ``write_todos``.
        workspace: Root directory for run workspaces. Each run gets a
            sub-directory named by its root execution id. Defaults to
            ``./workspace``.
        approval: Names of tools that pause for human approval before they
            run, for example ``["write_file"]``.
        max_turns: Turn limit for the agent loop; deep agents need more than
            the ``Agent`` default.
        **agent_kwargs: Passed through to :class:`Agent`.
    """
    if workspace is not None:
        os.environ[WORKSPACE_ENV] = str(Path(workspace).resolve())

    approval = tuple(approval)
    agent_tools: List[Any] = [write_todos]
    agent_tools.extend(_with_approval(t, approval) for t in FILE_TOOLS)
    agent_tools.extend(_with_approval(t, approval) for t in tools or ())

    for sub in subagents or ():
        existing = _tool_names(sub.tools or [])
        missing = [ft for ft in FILE_TOOLS if get_tool_def(ft).name not in existing]
        if missing:
            sub.tools = [*(sub.tools or []), *missing]
        agent_tools.append(agent_tool(sub, name=sub.name, description=_describe(sub)))

    # The model's idea of today comes from its training data, which makes it
    # argue with dated tool results; tell it the date.
    today = dt.date.today().strftime("%A, %B %d, %Y")
    full_instructions = f"{DEFAULT_INSTRUCTIONS}\nToday is {today}.\n"
    if instructions:
        full_instructions += f"\n## Your task\n{instructions.strip()}\n"

    return Agent(
        name=name,
        model=model,
        instructions=full_instructions,
        tools=agent_tools,
        max_turns=max_turns,
        **agent_kwargs,
    )


def workspace_dir(execution_id: str, workspace: Optional[Union[str, Path]] = None) -> Path:
    """The directory a run's files live in, for callers outside the agent."""
    base = (
        Path(workspace)
        if workspace is not None
        else Path(os.environ.get(WORKSPACE_ENV) or DEFAULT_WORKSPACE)
    )
    return (base / _root_execution_id(execution_id)).resolve()


__all__ = [
    "DEFAULT_INSTRUCTIONS",
    "FILE_TOOLS",
    "TODOS_KEY",
    "WORKSPACE_ENV",
    "deep_agent",
    "edit_file",
    "ls",
    "read_file",
    "resolve_root_execution_id",
    "stored_todos",
    "workspace_dir",
    "write_file",
    "write_todos",
]
