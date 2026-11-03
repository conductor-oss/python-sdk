"""Let the storyteller's stop_when see the critic's verdict on the turn the critic gives it.

Why this hack exists: stop_when's decision depends on the result of a tool call, the critic's
verdict, but as compiled it can't see that result on the turn the tool call happens. We edit
the workflow so that it can.

As compiled, stop_when's ``messages`` input is the storyteller LLM call's *input* messages, a
snapshot taken before that turn's critic call runs. The critic's verdict only reaches that
snapshot when the next turn's LLM input is assembled, so stop_when sees each verdict one turn
late and the loop runs one extra storyteller turn after the critic approves.
``_last_tool_results`` is a workflow variable the compiler already keeps: every tool result so
far, newest last, written after the critic and before stop_when. Pointing ``messages`` at it
lets stop_when see the verdict on the same turn and stop the loop on the approving turn.

This edits the compiler's output, so it has to be re-applied after every deploy. It reuses
the ``messages`` input because the Python SDK's stop_when worker passes only ``result``,
``messages`` and ``iteration`` to the function and drops any other input.

The proper fix: single-agent stop_when can't see this turn's tool results; add a
``tool_results`` input in the server's compiler and expose it in each SDK's stop_when context.
SWARM handoff checks already receive ``${workflow.variables._last_tool_results}`` under that
name, so the server has precedent for this wiring.
"""
from __future__ import annotations

from typing import Any, Iterator

SAME_TURN_MESSAGES = "${workflow.variables._last_tool_results}"
_TOOL_RESULTS_VARIABLE = "_last_tool_results"


def rewire_stop_when(api: Any, workflow_name: str, version: int = 1) -> bool:
    """Point the stored definition's stop_when at this turn's tool results.

    ``api`` is a MetadataResourceApi. Works on the raw JSON, so fields the SDK's models don't
    know about survive. Refuses to write a definition that lacks its agent markers, because
    writing it back without them would make the server treat it as a plain workflow. Re-reads
    the definition after writing to confirm. Returns True if it changed the definition, False
    if it was already rewired.
    """
    definition = _get(api, workflow_name, version)
    _check_rewirable(definition, workflow_name, version)
    stop = find_stop_when(definition, workflow_name)
    if stop["inputParameters"].get("messages") == SAME_TURN_MESSAGES:
        return False
    stop["inputParameters"]["messages"] = SAME_TURN_MESSAGES
    api.update1([definition], overwrite=True)

    stored = _get(api, workflow_name, version)
    _check_rewirable(stored, workflow_name, version)
    if find_stop_when(stored, workflow_name)["inputParameters"].get("messages") != SAME_TURN_MESSAGES:
        raise RuntimeError(f"{workflow_name} v{version}: the rewired stop_when input did not persist")
    return True


def stop_when_reads_same_turn(definition: dict, workflow_name: str) -> bool:
    """True if this definition's stop_when has been rewired."""
    return find_stop_when(definition, workflow_name)["inputParameters"].get("messages") == SAME_TURN_MESSAGES


def find_stop_when(definition: dict, workflow_name: str) -> dict:
    ref = f"{workflow_name}_stop_when"
    for task in walk_tasks(definition.get("tasks") or []):
        if task.get("taskReferenceName") == ref:
            task.setdefault("inputParameters", {})
            return task
    raise RuntimeError(f"{workflow_name} has no {ref} task")


def walk_tasks(tasks: list) -> Iterator[dict]:
    """Every task in a definition, including those nested in loops, switches and forks."""
    for task in tasks:
        yield task
        yield from walk_tasks(task.get("loopOver") or [])
        yield from walk_tasks(task.get("defaultCase") or [])
        for branch in (task.get("decisionCases") or {}).values():
            yield from walk_tasks(branch)
        for branch in task.get("forkTasks") or []:
            yield from walk_tasks(branch)


def _get(api: Any, workflow_name: str, version: int) -> dict:
    # Not api.get(): that parses into the SDK's WorkflowDef model, which can drop fields the
    # model doesn't know about, and its raw mode (_preload_content=False) crashes on the
    # SDK's httpx transport. response_type="object" returns the parsed JSON untouched.
    return api.api_client.call_api(
        "/metadata/workflow/{name}", "GET",
        path_params={"name": workflow_name},
        query_params=[("version", version)],
        header_params={"Accept": "application/json"},
        response_type="object",
        auth_settings=[],
        _return_http_data_only=True,
    )


def _check_rewirable(definition: dict, workflow_name: str, version: int) -> None:
    metadata = definition.get("metadata") or {}
    if not (metadata.get("agent_sdk") or metadata.get("agentDef")):
        raise RuntimeError(
            f"{workflow_name} v{version} has no agent markers in its metadata; not writing it back, "
            "since the server would then treat it as a plain workflow")
    find_stop_when(definition, workflow_name)
    sets_variable = any(
        task.get("type") == "SET_VARIABLE" and _TOOL_RESULTS_VARIABLE in (task.get("inputParameters") or {})
        for task in walk_tasks(definition.get("tasks") or []))
    if not sets_variable:
        raise RuntimeError(f"{workflow_name} v{version} never sets {_TOOL_RESULTS_VARIABLE}")
