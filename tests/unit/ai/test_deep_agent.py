"""Tests for the deep agent harness: plan tool, file tools, and the entry point."""

import pytest

from conductor.ai.agents import Agent
from conductor.ai.agents import deep
from conductor.ai.agents.deep import (
    DEFAULT_INSTRUCTIONS,
    STORAGE_ENV,
    SUBAGENT_INSTRUCTIONS,
    SUBAGENTS_ENV,
    TODOS_KEY,
    WORKSPACE_ENV,
    deep_agent,
    edit_file,
    ls,
    read_file,
    resolve_root_execution_id,
    stored_todos,
    write_file,
    write_todos,
)
from conductor.ai.agents.tool import ToolContext, get_tool_def


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A local workspace root in tmp, with root-id resolution short-circuited."""
    monkeypatch.setenv(STORAGE_ENV, "local")
    monkeypatch.setenv(SUBAGENTS_ENV, '["analyst"]')
    monkeypatch.setenv(WORKSPACE_ENV, str(tmp_path))
    monkeypatch.setattr(deep, "_root_execution_id", lambda eid: eid)
    return tmp_path


def ctx(execution_id="exec-1", state=None, agent_name="t"):
    return ToolContext(
        execution_id=execution_id,
        agent_name=agent_name,
        state=state if state is not None else {},
    )


# ── write_todos ─────────────────────────────────────────────────────────


def test_write_todos_stores_the_plan_in_state():
    c = ctx()
    out = write_todos.__wrapped__(
        todos=[
            {"content": "Look up Beijing", "status": "completed"},
            {"content": "Look up Shanghai", "status": "in_progress"},
            {"content": "Write the report", "status": "pending"},
        ],
        context=c,
    )
    # Stored as an object so a later write replaces it; the server appends
    # list-valued updates instead of replacing them.
    assert c.state[TODOS_KEY] == {"items": out["todos"]}
    assert stored_todos(c.state) == out["todos"]
    assert out["summary"] == "1/3 completed"
    assert [t["status"] for t in out["todos"]] == ["completed", "in_progress", "pending"]


def test_write_todos_rejects_bad_status_and_empty_content():
    with pytest.raises(ValueError, match="status"):
        write_todos.__wrapped__(todos=[{"content": "x", "status": "done"}], context=ctx())
    with pytest.raises(ValueError, match="content"):
        write_todos.__wrapped__(todos=[{"content": "  ", "status": "pending"}], context=ctx())


def test_write_todos_defaults_status_to_pending():
    out = write_todos.__wrapped__(todos=[{"content": "x"}], context=ctx())
    assert out["todos"][0]["status"] == "pending"
    assert "next" not in out


def test_stored_todos_handles_missing_or_malformed_state():
    assert stored_todos(None) is None
    assert stored_todos({}) is None
    assert stored_todos({TODOS_KEY: ["not", "an", "object"]}) is None
    assert stored_todos({TODOS_KEY: {"items": [{"content": "x", "status": "pending"}]}}) == [
        {"content": "x", "status": "pending"}
    ]


def test_write_todos_tells_the_model_when_to_stop():
    c = ctx()
    plan = [{"content": "a", "status": "completed"}, {"content": "b", "status": "in_progress"}]
    out = write_todos.__wrapped__(todos=plan, context=c)
    assert "next" not in out
    out = write_todos.__wrapped__(todos=plan, context=c)
    assert out["next"].startswith("The plan is unchanged")
    out = write_todos.__wrapped__(
        todos=[{"content": "a", "status": "completed"}, {"content": "b", "status": "completed"}],
        context=c,
    )
    assert out["next"].startswith("All steps are completed")


def test_write_todos_schema_spells_out_the_item_fields():
    schema = get_tool_def(write_todos).input_schema
    todos = schema["properties"]["todos"]
    assert todos["type"] == "array"
    item = todos["items"]
    assert item["required"] == ["content", "status"]
    assert item["properties"]["status"]["enum"] == ["pending", "in_progress", "completed"]
    assert "context" not in schema["properties"]


# ── file tools ──────────────────────────────────────────────────────────


def test_file_tools_round_trip(workspace):
    c = ctx()
    assert (
        write_file.__wrapped__(path="/notes/a.md", content="one\ntwo\nthree\n", context=c)["bytes"]
        == 14
    )
    assert (workspace / "exec-1" / "notes" / "a.md").read_text() == "one\ntwo\nthree\n"

    got = read_file.__wrapped__(path="notes/a.md", context=c)
    assert got["content"] == "one\ntwo\nthree"
    assert got["total_lines"] == 3

    got = read_file.__wrapped__(path="notes/a.md", offset=1, limit=1, context=c)
    assert got["content"] == "two"
    assert got["returned_lines"] == 1

    assert (
        edit_file.__wrapped__(path="notes/a.md", old_string="two", new_string="2", context=c)[
            "replacements"
        ]
        == 1
    )
    assert read_file.__wrapped__(path="notes/a.md", context=c)["content"] == "one\n2\nthree"

    listing = ls.__wrapped__(path="/", context=c)
    assert [(e["name"], e["type"]) for e in listing["entries"]] == [("notes", "dir")]
    listing = ls.__wrapped__(path="notes", context=c)
    assert listing["entries"][0]["name"] == "a.md"
    assert listing["entries"][0]["size"] == 12


def test_edit_file_requires_a_unique_match(workspace):
    c = ctx()
    write_file.__wrapped__(path="x.txt", content="a b a", context=c)
    out = edit_file.__wrapped__(path="x.txt", old_string="a", new_string="z", context=c)
    assert out["replacements"] == 0 and "2 times" in out["error"]
    out = edit_file.__wrapped__(
        path="x.txt", old_string="a", new_string="z", replace_all=True, context=c
    )
    assert out["replacements"] == 2
    assert read_file.__wrapped__(path="x.txt", context=c)["content"] == "z b z"


def test_missing_file_is_reported_not_raised(workspace):
    c = ctx()
    assert read_file.__wrapped__(path="nope.txt", context=c)["error"] == "no such file"
    assert (
        edit_file.__wrapped__(path="nope.txt", old_string="a", new_string="b", context=c)["error"]
        == "no such file"
    )
    assert ls.__wrapped__(path="nope", context=c)["error"] == "no such directory"


def test_paths_cannot_escape_the_workspace(workspace):
    c = ctx()
    with pytest.raises(ValueError, match="outside"):
        write_file.__wrapped__(path="../escape.txt", content="x", context=c)
    with pytest.raises(ValueError, match="outside"):
        read_file.__wrapped__(path="/notes/../../escape.txt", context=c)
    assert not (workspace / "escape.txt").exists()


def test_runs_get_separate_directories(workspace):
    write_file.__wrapped__(path="r.md", content="one", context=ctx("exec-1"))
    write_file.__wrapped__(path="r.md", content="two", context=ctx("exec-2"))
    assert (workspace / "exec-1" / "r.md").read_text() == "one"
    assert (workspace / "exec-2" / "r.md").read_text() == "two"


def test_no_context_uses_a_local_directory(workspace):
    write_file.__wrapped__(path="r.md", content="x", context=None)
    assert (workspace / "local" / "r.md").exists()


def test_subagent_relative_paths_resolve_to_its_own_directory(workspace):
    sub = ctx(agent_name="analyst", execution_id="exec-1")
    out = write_file.__wrapped__(path="notes.md", content="x", context=sub)
    assert out["path"] == "/subagents/analyst-exec-1/notes.md"
    assert (workspace / "exec-1" / "subagents" / "analyst-exec-1" / "notes.md").exists()
    assert ls.__wrapped__(context=sub)["entries"][0]["name"] == "notes.md"


def test_subagent_reads_anywhere_but_writes_only_at_home(workspace):
    write_file.__wrapped__(path="/brief.md", content="brief", context=ctx())
    sub = ctx(agent_name="analyst")
    assert read_file.__wrapped__(path="/brief.md", context=sub)["content"] == "brief"
    with pytest.raises(ValueError, match="own directory"):
        write_file.__wrapped__(path="/report.md", content="x", context=sub)
    with pytest.raises(ValueError, match="own directory"):
        edit_file.__wrapped__(path="/brief.md", old_string="b", new_string="c", context=sub)


def test_top_level_agent_sees_subagent_files(workspace):
    sub = ctx(agent_name="analyst")
    write_file.__wrapped__(path="result.md", content="r", context=sub)
    parent = ctx()
    listing = ls.__wrapped__(path="/subagents", context=parent)
    assert listing["entries"] == [{"name": "analyst-exec-1", "type": "dir", "size": 0}]
    got = read_file.__wrapped__(path="/subagents/analyst-exec-1/result.md", context=parent)
    assert got["content"] == "r"


def test_top_level_agent_cannot_change_a_subagent_directory(workspace):
    sub = ctx(agent_name="analyst")
    path = write_file.__wrapped__(path="tests.py", content="assert True", context=sub)["path"]
    parent = ctx()
    with pytest.raises(ValueError, match="belongs to a sub-agent"):
        write_file.__wrapped__(path=path, content="", context=parent)
    with pytest.raises(ValueError, match="belongs to a sub-agent"):
        edit_file.__wrapped__(path=path, old_string="True", new_string="1", context=parent)
    assert read_file.__wrapped__(path=path, context=parent)["content"] == "assert True"


def test_export_files_copies_the_workspace_layout(workspace, tmp_path):
    from conductor.ai.agents import deep_files

    c = ctx()
    write_file.__wrapped__(path="/src/m.py", content="x = 1", context=c)
    write_file.__wrapped__(path="/notes.md", content="n", context=c)
    out = tmp_path / "export"
    assert deep_files.export_files(c, out, prefix="/src") == ["src/m.py"]
    assert (out / "src" / "m.py").read_text() == "x = 1"
    assert not (out / "notes.md").exists()


# ── root execution id ───────────────────────────────────────────────────


class FakeWorkflowClient:
    def __init__(self, parents):
        self.parents = parents
        self.calls = []

    def get_workflow(self, workflow_id, include_tasks=False):
        self.calls.append(workflow_id)
        if workflow_id not in self.parents:
            raise RuntimeError("not found")
        wf = type("WF", (), {})()
        wf.parent_workflow_id = self.parents[workflow_id]
        return wf


def test_root_execution_id_walks_the_parent_chain():
    client = FakeWorkflowClient({"child": "mid", "mid": "root", "root": None})
    assert resolve_root_execution_id("child", client) == "root"
    assert resolve_root_execution_id("root", client) == "root"


def test_root_execution_id_falls_back_on_lookup_failure():
    client = FakeWorkflowClient({"child": "gone"})
    # The parent exists as an id but cannot be fetched; keep the furthest id reached.
    assert resolve_root_execution_id("child", client) == "gone"
    assert resolve_root_execution_id("unknown", client) == "unknown"


def test_root_execution_id_stops_on_a_cycle():
    client = FakeWorkflowClient({"a": "b", "b": "a"})
    assert resolve_root_execution_id("a", client) in ("a", "b")
    assert len(client.calls) <= 3


# ── deep_agent ──────────────────────────────────────────────────────────


def names(agent):
    return [get_tool_def(t).name for t in agent.tools]


def test_deep_agent_assembles_tools_and_prompt(tmp_path, monkeypatch):
    from conductor.ai.agents import tool

    @tool
    def get_weather(city: str) -> dict:
        """Weather."""
        return {"city": city}

    analyst = Agent(
        name="weather_analyst", model="openai/gpt-4o-mini", instructions="Compare cities."
    )
    agent = deep_agent(
        name="planner",
        model="openai/gpt-4o-mini",
        instructions="You are a travel assistant.",
        tools=[get_weather],
        subagents=[analyst],
        workspace=tmp_path / "ws",
        approval=["write_file"],
    )

    assert isinstance(agent, Agent)
    assert names(agent) == [
        "write_todos",
        "ls",
        "read_file",
        "write_file",
        "edit_file",
        "get_weather",
        "weather_analyst",
    ]
    assert agent.max_turns == 50
    assert agent.instructions.startswith(DEFAULT_INSTRUCTIONS)
    assert "You are a travel assistant." in agent.instructions
    env = __import__("os").environ
    assert env[WORKSPACE_ENV] == str((tmp_path / "ws").resolve())
    assert env[STORAGE_ENV] == "conductor"
    assert "weather_analyst" in __import__("json").loads(env[SUBAGENTS_ENV])

    by_name = {get_tool_def(t).name: get_tool_def(t) for t in agent.tools}
    assert by_name["write_file"].approval_required is True
    assert by_name["write_file"].func is not None
    assert by_name["edit_file"].approval_required is False
    assert by_name["weather_analyst"].tool_type == "agent_tool"

    # The caller's sub-agent is left unchanged; the harness wires a copy.
    assert analyst.tools in (None, [])
    assert analyst.instructions == "Compare cities."
    wired = by_name["weather_analyst"].config["agent"]
    assert wired is not analyst
    assert wired.instructions.startswith("Compare cities.")
    assert wired.instructions.endswith(SUBAGENT_INSTRUCTIONS)
    # The copy shares the workspace but not the plan, and approval applies to it.
    sub_tools = {get_tool_def(t).name: get_tool_def(t) for t in wired.tools}
    assert "write_todos" not in sub_tools
    assert {"ls", "read_file", "write_file", "edit_file"} <= set(sub_tools)
    assert sub_tools["write_file"].approval_required is True


def test_deep_agent_rejects_unknown_storage():
    with pytest.raises(ValueError, match="storage"):
        deep_agent(name="a", model="m", storage="s3")


def test_deep_agent_applies_approval_to_user_tools():
    from conductor.ai.agents import tool

    @tool
    def send_email(to: str) -> dict:
        """Send."""
        return {"to": to}

    agent = deep_agent(name="a", model="m", tools=[send_email], approval=["send_email"])
    td = {get_tool_def(t).name: get_tool_def(t) for t in agent.tools}["send_email"]
    assert td.approval_required is True


def test_deep_agent_without_instructions_uses_the_default_prompt_and_date():
    agent = deep_agent(name="a", model="m")
    assert agent.instructions.startswith(DEFAULT_INSTRUCTIONS)
    assert "Today is" in agent.instructions
    assert "## Your task" not in agent.instructions
    assert names(agent) == ["write_todos", "ls", "read_file", "write_file", "edit_file"]
