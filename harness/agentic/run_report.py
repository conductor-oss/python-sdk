"""Summarize a finished storyteller run from its execution record.

Reads the execution itself rather than streamed events: some servers (Orkes 5.6.0-rc4) don't
stream tool-call events, so a report built from events misses every critic call.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from agentic.stop_wiring import find_stop_when, stop_when_reads_same_turn
from agentic.story_agents import CRITIC_NAME, CRITIC_TOOL_NAME, STORYTELLER_NAME, find_verdict

# The storyteller sometimes labels the story it sends the critic ("COMPLETE STORY SO FAR:").
_LABEL = re.compile(r"^\s*(?:the\s+)?(?:complete\s+)?story(?:\s+so\s+far)?\s*:\s*", re.IGNORECASE)


@dataclass
class Turn:
    number: int
    finish_reason: str
    story: Optional[str]        # the full story sent to the critic; None if the critic wasn't called
    added: str                  # what this turn added to the story
    verdict: Optional[dict]


@dataclass
class RunSummary:
    status: str
    reason: str                 # why the run failed or was terminated; empty if it didn't
    turns: List[Turn]
    approved_on: Optional[int]
    story: str
    story_source: str
    storyteller_tokens: Tuple[int, int]
    critic_execution_ids: List[str]
    stop_when_same_turn: Optional[bool]


def summarize(execution: dict) -> RunSummary:
    tasks = execution.get("tasks") or []
    llm_calls = {t.get("iteration"): t for t in tasks if t.get("taskType") == "LLM_CHAT_COMPLETE"}
    critic_calls = {t.get("iteration"): t for t in tasks
                    if t.get("taskType") == "SUB_WORKFLOW"
                    and (t.get("inputData") or {}).get("subWorkflowName") == CRITIC_NAME}

    turns: List[Turn] = []
    previous = ""
    for number in sorted(n for n in llm_calls if n is not None):
        output = llm_calls[number].get("outputData") or {}
        story = _story_sent_to_critic(output)
        added = ""
        if story is not None:
            added = story[len(previous):].strip() if story.startswith(previous) else story
            previous = story
        critic = critic_calls.get(number)
        verdict = find_verdict((critic.get("outputData") or {}).get("result")) if critic else None
        turns.append(Turn(number, output.get("finishReason") or "", story, added, verdict))

    approved = next((t for t in turns if t.verdict is not None and t.verdict.get("done") is True), None)
    drafts = [t for t in turns if t.story]
    if approved is not None and approved.story:
        story, source = approved.story, f"approved by the critic on turn {approved.number}"
    elif drafts:
        story, source = drafts[-1].story, "latest draft; the critic never approved it"
    else:
        story, source = _workflow_result(execution), "workflow output; the critic was never called"

    return RunSummary(
        status=str(execution.get("status") or "UNKNOWN"),
        reason=str(execution.get("reasonForIncompletion") or ""),
        turns=turns,
        approved_on=approved.number if approved is not None else None,
        story=story,
        story_source=source,
        storyteller_tokens=llm_tokens(execution),
        critic_execution_ids=[critic_calls[n]["subWorkflowId"] for n in sorted(critic_calls)
                              if critic_calls[n].get("subWorkflowId")],
        stop_when_same_turn=_reads_same_turn(execution.get("workflowDefinition") or {}),
    )


def fetch_execution(api_client: Any, execution_id: str) -> dict:
    """The execution with its tasks, as the server's raw JSON (not the SDK's typed model)."""
    return api_client.call_api(
        "/workflow/{workflowId}", "GET",
        path_params={"workflowId": execution_id},
        query_params=[("includeTasks", "true")],
        header_params={"Accept": "application/json"},
        response_type="object",
        auth_settings=[],
        _return_http_data_only=True,
    )


def execution_url(base: str, execution_id: str) -> str:
    """UI link for an execution. Agent runs use the normal execution page, which switches
    to its agent view by itself when the workflow definition carries agent metadata.
    Printed as a plain URL, which VS Code's terminal and iTerm2 make Cmd-clickable and
    which survives logs and copy-paste."""
    base = base.rstrip("/")
    if base.endswith("/api"):
        base = base[: -len("/api")]
    return f"{base}/execution/{execution_id}"


def llm_tokens(execution: dict) -> Tuple[int, int]:
    """Prompt and completion tokens over every LLM call in one execution (not its sub-workflows)."""
    outputs = [t.get("outputData") or {} for t in execution.get("tasks") or []
               if t.get("taskType") == "LLM_CHAT_COMPLETE"]
    return (sum(int(o.get("promptTokens") or 0) for o in outputs),
            sum(int(o.get("completionTokens") or 0) for o in outputs))


def _story_sent_to_critic(llm_output: dict) -> Optional[str]:
    for call in llm_output.get("toolCalls") or []:
        if call.get("name") == CRITIC_TOOL_NAME:
            request = (call.get("inputParameters") or {}).get("request")
            if isinstance(request, str):
                return _LABEL.sub("", request, count=1).strip()
    return None


def _workflow_result(execution: dict) -> str:
    result = (execution.get("output") or {}).get("result")
    return result.strip() if isinstance(result, str) else ""


def _reads_same_turn(definition: dict) -> Optional[bool]:
    try:
        find_stop_when(definition, STORYTELLER_NAME)
    except RuntimeError:
        return None
    return stop_when_reads_same_turn(definition, STORYTELLER_NAME)
