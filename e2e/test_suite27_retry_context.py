"""Suite 27: Retry preserves agent conversation context.

Feature NOT covered by Suites 1-26: what an agent's LLM turn receives as input when the
workflow is RETRIED, as opposed to freshly scheduled.

Conversation history is not carried by ${...} references between tasks — the server's
LLM_CHAT_COMPLETE task mapper reconstructs it at scheduling time by walking the workflow's
completed tasks. Retry is a different code path that re-resolves the task definition's
inputParameters instead, so it can silently hand the model a bare [system, user] template
with none of the tool calls that already succeeded. The model, seeing what looks like a new
request, re-issues a tool call it has already made — a duplicate execution of a potentially
side-effecting tool, not just a display quirk.

Tracked as orkes-io/orkes-conductor#3876. The same shape exists in conductor-oss's
WorkflowExecutorUtils.taskToBeRescheduled, so this suite is meaningful against either server.

Assertions are algorithmic — no LLM output parsing. The check is on the retried task's
inputData.messages, read from the Conductor workflow API.

Skipped by default: the LLM-retry assertion fails against current servers, which is the
point of the suite. Opt in to check whether the server-side fix has landed:

    SUITE27_RUN=1 pytest e2e/test_suite27_retry_context.py -v

No mocks. Real server, real LLM.
"""

import json
import os
import time

import pytest
import requests
from conductor.ai.agents import Agent, tool

from conftest import BASE_URL, get_workflow

# Gated off in CI: test_retried_llm_turn_keeps_conversation_history asserts the FIXED
# behaviour and therefore fails until the server changes. The control test shares the same
# gate so the suite is enabled or disabled as one unit — running the control alone proves
# nothing about the bug.
_RUN = os.environ.get("SUITE27_RUN", "").strip().lower() in ("1", "true", "yes")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not _RUN,
        reason=(
            "Suite 27 reproduces an open server bug (orkes-io/orkes-conductor#3876): a "
            "retried LLM_CHAT_COMPLETE task is dispatched without its conversation history. "
            "Set SUITE27_RUN=1 to run it."
        ),
    ),
]

MODEL = os.environ.get("CONDUCTOR_AGENT_LLM_MODEL", "openai/gpt-4o-mini")

LLM_TASK_TYPE = "LLM_CHAT_COMPLETE"
CUSTOMER_TOOL = "get_customer_info"

# Distinctive token from get_customer_info's result. Asserting on it proves the ACTUAL prior
# exchange was reconstructed — a merely tool-shaped message would say nothing about which call
# it describes.
TOOL_RESULT_MARKER = "Seattle"

# Seconds the second tool stalls. The condition under test is "retry an LLM turn that was
# interrupted", and with a fast model the whole agent finishes in a few seconds. Holding the
# second tool open keeps the workflow RUNNING long enough to interrupt it deterministically.
# It does not affect what is asserted — the retry happens on an LLM task, not on this one.
TOOL_DELAY_S = float(os.environ.get("SUITE27_TOOL_DELAY_S", "8"))

ARM_TIMEOUT_S = 120
POLL_S = 0.1


# ═══════════════════════════════════════════════════════════════════════════
# Deterministic tools
# ═══════════════════════════════════════════════════════════════════════════

@tool
def get_customer_info(customer_id: str) -> dict:
    """Look up a customer's account information, including their home city, by customer ID."""
    return {"customer_id": customer_id, "name": "Jane Doe", "city": "Seattle"}


@tool
def get_weather(city: str) -> str:
    """Get the current temperature, wind speed, and humidity for a city."""
    time.sleep(TOOL_DELAY_S)
    return f"{city}: 17.7C, wind 6.4 km/h, humidity 73%"


# ═══════════════════════════════════════════════════════════════════════════
# Server helpers
# ═══════════════════════════════════════════════════════════════════════════

def _terminate(execution_id: str, reason: str) -> None:
    resp = requests.delete(
        f"{BASE_URL}/api/workflow/{execution_id}", params={"reason": reason}, timeout=15
    )
    if resp.status_code >= 400:
        resp = requests.post(
            f"{BASE_URL}/api/workflow/{execution_id}/terminate",
            params={"reason": reason},
            timeout=15,
        )
    resp.raise_for_status()


def _retry(execution_id: str) -> None:
    resp = requests.post(
        f"{BASE_URL}/api/workflow/{execution_id}/retry",
        params={"resumeSubworkflowTasks": "false"},
        timeout=15,
    )
    resp.raise_for_status()


def _llm_tasks(wf: dict) -> list:
    return [t for t in wf.get("tasks", []) if t.get("taskType") == LLM_TASK_TYPE]


def _roles(messages) -> list:
    return [str(m.get("role")) for m in (messages or []) if isinstance(m, dict)]


def _wait_for_interruptible_llm_turn(execution_id: str):
    """
    Block until the first tool has COMPLETED and a LATER LLM turn is non-terminal.

    Interrupting before that reproduces a different (working) case from the issue — retrying a
    plain tool task, which needs no history. Returns the in-flight LLM task, or None on timeout.

    The tool is matched by taskType: agentspan names tool task refs call_<id>_0__<iter>, so
    matching on referenceTaskName never fires.
    """
    deadline = time.time() + ARM_TIMEOUT_S
    while time.time() < deadline:
        wf = get_workflow(execution_id)
        if wf.get("status") in ("COMPLETED", "FAILED", "TERMINATED", "TIMED_OUT"):
            return None

        tool_done = any(
            t.get("status") == "COMPLETED"
            and CUSTOMER_TOOL in (t.get("taskType") or "", t.get("taskDefName") or "")
            for t in wf.get("tasks", [])
        )
        if tool_done:
            inflight = [
                t for t in _llm_tasks(wf) if t.get("status") in ("IN_PROGRESS", "SCHEDULED")
            ]
            if inflight:
                return inflight[-1]
        time.sleep(POLL_S)
    return None


def _find_retried_llm_task(execution_id: str, before_task_ids: set):
    """
    The LLM task the retry produced: a taskId not present before the retry.

    Identity must come from taskId, never from the input. The interrupted original still holds
    full history in its inputData, so selecting "the task whose messages have history" would
    find it every time and pass against a broken server.
    """
    deadline = time.time() + 30
    while time.time() < deadline:
        wf = get_workflow(execution_id)
        fresh = [t for t in _llm_tasks(wf) if t.get("taskId") not in before_task_ids]
        with_input = [t for t in fresh if (t.get("inputData") or {}).get("messages")]
        if with_input:
            return with_input[-1]
        time.sleep(POLL_S)
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def context_agent():
    return Agent(
        name="s27_retry_context",
        model=MODEL,
        tools=[get_customer_info, get_weather],
        instructions=(
            "First call get_customer_info to find the customer's city, then "
            "call get_weather for that city, then summarize both."
        ),
    )


def test_retried_llm_turn_keeps_conversation_history(runtime, context_agent):
    """A retried LLM turn must receive the same reconstructed history as a fresh dispatch."""
    handle = runtime.start(
        context_agent, "What's the weather like where customer 4471 lives?"
    )
    execution_id = handle.execution_id

    target = _wait_for_interruptible_llm_turn(execution_id)
    if target is None:
        pytest.skip(
            "agent never reached an interruptible second LLM turn "
            "(finished too fast, or the model did not call the tool)"
        )

    # Sanity: the fresh dispatch of this turn DID get history. That is the behaviour the
    # retried task has to match, and it also proves the fixture reached the intended state.
    assert _roles((target.get("inputData") or {}).get("messages")) != ["system", "user"], (
        "fixture problem: the in-flight LLM turn had no history to begin with"
    )

    _terminate(execution_id, "suite27-retry-context")

    before = {t.get("taskId") for t in get_workflow(execution_id).get("tasks", [])}
    _retry(execution_id)

    retried = _find_retried_llm_task(execution_id, before)
    assert retried is not None, "retry produced no new LLM_CHAT_COMPLETE task"

    messages = (retried.get("inputData") or {}).get("messages")
    roles = _roles(messages)
    blob = json.dumps(messages or [], default=str)

    # Structural: some tool exchange survived.
    has_tool_exchange = any(
        isinstance(m, dict)
        and (m.get("toolCalls") or m.get("tool_calls") or str(m.get("role", "")).lower() == "tool")
        for m in (messages or [])
    )
    assert has_tool_exchange, (
        f"retried LLM task lost the conversation history — roles={roles}. "
        f"Only [system, user] means the retry path skipped the history assembly the task "
        f"mapper performs at scheduling time (orkes-io/orkes-conductor#3876)."
    )

    # Content: it is the ACTUAL prior exchange, not merely something tool-shaped.
    assert CUSTOMER_TOOL in blob, (
        f"retried history has a tool exchange but not the '{CUSTOMER_TOOL}' call that ran; "
        f"roles={roles}"
    )
    assert TOOL_RESULT_MARKER in blob, (
        f"retried history references '{CUSTOMER_TOOL}' but not its result "
        f"('{TOOL_RESULT_MARKER}'); roles={roles}"
    )


def test_retried_tool_task_is_unaffected(runtime, context_agent):
    """
    Control from the issue: retrying an interrupted TOOL task behaves correctly.

    A tool task's input is genuinely static, so re-resolving the definition reproduces it
    exactly. This must keep passing — a fix for the LLM case must not disturb it.
    """
    handle = runtime.start(
        context_agent, "What's the weather like where customer 4471 lives?"
    )
    execution_id = handle.execution_id

    # Wait for the slow tool to be in flight, then interrupt it.
    deadline = time.time() + ARM_TIMEOUT_S
    target = None
    while time.time() < deadline:
        wf = get_workflow(execution_id)
        if wf.get("status") in ("COMPLETED", "FAILED", "TERMINATED", "TIMED_OUT"):
            break
        inflight = [
            t
            for t in wf.get("tasks", [])
            if "get_weather" in (t.get("taskType") or "", t.get("taskDefName") or "")
            and t.get("status") in ("IN_PROGRESS", "SCHEDULED")
        ]
        if inflight:
            target = inflight[-1]
            break
        time.sleep(POLL_S)

    if target is None:
        pytest.skip("agent never reached an interruptible get_weather task")

    original_input = dict(target.get("inputData") or {})

    _terminate(execution_id, "suite27-retry-tool-control")

    before = {t.get("taskId") for t in get_workflow(execution_id).get("tasks", [])}
    _retry(execution_id)

    deadline = time.time() + 30
    retried = None
    while time.time() < deadline:
        wf = get_workflow(execution_id)
        fresh = [
            t
            for t in wf.get("tasks", [])
            if t.get("taskId") not in before
            and "get_weather" in (t.get("taskType") or "", t.get("taskDefName") or "")
        ]
        if fresh:
            retried = fresh[-1]
            break
        time.sleep(POLL_S)

    assert retried is not None, "retry produced no new get_weather task"

    retried_input = retried.get("inputData") or {}
    assert retried_input.get("city") == original_input.get("city"), (
        f"retried tool task should re-run with the same arguments: "
        f"before={original_input.get('city')!r} after={retried_input.get('city')!r}"
    )
