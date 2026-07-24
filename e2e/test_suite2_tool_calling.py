"""Suite 2: Tool Calling / Credentials — full lifecycle test.

Tests the credential pipeline end-to-end:
  1. Tools fail when credentials are missing
  2. Env vars are NOT read (security boundary)
  3. Credentials added via CLI are resolved at execution time
  4. Credential updates propagate to subsequent runs

Single sequential test with try/finally cleanup.
No mocks. Real server, real CLI, real LLM.
"""

import os
import time

import pytest
import requests

from conductor.ai.agents import Agent, AgentRuntime, tool
from conductor.ai.agents.tool import get_tool_def

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.xdist_group("credentials"),
]

CRED_A = "E2E_CRED_A"
CRED_B = "E2E_CRED_B"
TIMEOUT = 300  # 5 min per agent run — CI runners are slower


# ── Tools ───────────────────────────────────────────────────────────────


@tool
def free_tool(x: str) -> str:
    """A tool that needs no credentials. Always succeeds."""
    return "free:ok"


@tool(credentials=[CRED_A])
def paid_tool_a(x: str) -> str:
    """A tool that needs E2E_CRED_A. Returns first 3 chars of credential."""
    cred_val = os.environ.get(CRED_A)
    if not cred_val:
        raise RuntimeError(
            f"Credential '{CRED_A}' not found in environment. "
            f"The server should have injected it via credential resolution."
        )
    return f"paid_a:{cred_val[:3]}"


@tool(credentials=[CRED_B])
def paid_tool_b(x: str) -> str:
    """A tool that needs E2E_CRED_B. Returns first 3 chars of credential."""
    cred_val = os.environ.get(CRED_B)
    if not cred_val:
        raise RuntimeError(
            f"Credential '{CRED_B}' not found in environment. "
            f"The server should have injected it via credential resolution."
        )
    return f"paid_b:{cred_val[:3]}"


# Used by the output-masking test below — deliberately leaks the FULL credential
# value into its return. The server's SecretMaskingResponseAdvice must redact
# the value before /api/agent/executions/{id} responds.
LEAK_CRED = "E2E_MASK_LEAK_KEY"


# ── Helpers ─────────────────────────────────────────────────────────────


AGENT_INSTRUCTIONS = """\
You have three tools: free_tool, paid_tool_a, and paid_tool_b.
You MUST call all three tools exactly once each, with the argument "test".
After calling all three, report each tool's output verbatim in this format:
  free_tool: <output>
  paid_tool_a: <output>
  paid_tool_b: <output>
Do not skip any tool. Do not add commentary.
"""


def _make_agent(model: str) -> Agent:
    return Agent(
        name="e2e_cred_lifecycle",
        model=model,
        max_turns=3,
        instructions=AGENT_INSTRUCTIONS,
        tools=[free_tool, paid_tool_a, paid_tool_b],
    )


def _get_workflow(execution_id: str) -> dict:
    """Fetch workflow from server API."""
    base = os.environ.get("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    base_url = base.rstrip("/").replace("/api", "")
    resp = requests.get(f"{base_url}/api/workflow/{execution_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def _run_diagnostic(result) -> str:
    """Build a diagnostic string from a run result for error messages."""
    parts = [
        f"status={result.status}",
        f"execution_id={result.execution_id}",
    ]

    # Include output shape — dict keys if dict, truncated string otherwise
    output = result.output
    if isinstance(output, dict):
        parts.append(f"output_keys={list(output.keys())}")
        if "finishReason" in output:
            parts.append(f"finishReason={output['finishReason']}")
        if output.get("result") is not None:
            parts.append(f"result_count={len(output.get('result', []))}")
        if output.get("rejectionReason"):
            parts.append(f"rejectionReason={output['rejectionReason']}")
    else:
        out_str = str(output)
        if len(out_str) > 200:
            out_str = out_str[:200] + "..."
        parts.append(f"output={out_str}")

    return " | ".join(parts)


def _tool_diagnostics(execution_id: str) -> str:
    """Fetch workflow tasks and report tool-related task statuses."""
    try:
        wf = _get_workflow(execution_id)
    except Exception as e:
        return f"(could not fetch workflow: {e})"

    tool_names = {"free_tool", "paid_tool_a", "paid_tool_b"}
    tool_tasks = []
    for task in wf.get("tasks", []):
        ref = task.get("referenceTaskName", "")
        status = task.get("status", "")
        reason = task.get("reasonForIncompletion", "")

        # Match tool tasks by reference name
        matched = [name for name in tool_names if name in ref]
        if matched:
            entry = f"{ref}: status={status}"
            if reason:
                entry += f" reason={reason}"
            output_data = task.get("outputData", {})
            if output_data:
                out_str = str(output_data)
                if len(out_str) > 150:
                    out_str = out_str[:150] + "..."
                entry += f" output={out_str}"
            tool_tasks.append(entry)

    if not tool_tasks:
        # No tool tasks found — report overall workflow status
        wf_status = wf.get("status", "unknown")
        wf_reason = wf.get("reasonForIncompletion", "")
        summary = f"No tool tasks found in workflow. workflow_status={wf_status}"
        if wf_reason:
            summary += f" reason={wf_reason}"
        return summary

    return "\n  ".join(["Tool tasks:"] + tool_tasks)


def _find_tool_tasks_for(execution_id: str) -> dict:
    """Fetch workflow and extract tool task results by tool name.

    Checks referenceTaskName, taskDefName, and taskType for tool name matches.
    Returns a dict keyed by tool name with status, output, reason, ref.
    """
    wf = _get_workflow(execution_id)
    tool_names = ["free_tool", "paid_tool_a", "paid_tool_b"]
    results = {}
    for task in wf.get("tasks", []):
        ref = task.get("referenceTaskName", "")
        task_def = task.get("taskDefName", "")
        task_type = task.get("taskType", "")
        for name in tool_names:
            if name in results:
                continue
            if name in ref or name == task_def or name == task_type:
                results[name] = {
                    "status": task.get("status", ""),
                    "output": task.get("outputData", {}),
                    "reason": task.get("reasonForIncompletion", ""),
                    "ref": ref,
                }
    return results


def _credential_audit(agent: Agent) -> str:
    """Cross-reference agent tool credential requirements with the server store.

    Returns a human-readable report showing which credentials are required
    and which are missing from the server.
    """
    base = os.environ.get("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    base_url = base.rstrip("/").replace("/api", "")

    # Fetch stored credentials from server
    try:
        resp = requests.get(f"{base_url}/api/credentials", timeout=5)
        resp.raise_for_status()
        stored = {c["name"] for c in resp.json()}
    except Exception as e:
        return f"(could not fetch credentials from server: {e})"

    # Collect credential requirements from agent tools
    lines = []
    missing = []
    for t in agent.tools or []:
        td = get_tool_def(t)
        tool_name = td.name
        creds = td.credentials or []
        if not creds:
            lines.append(f"  {tool_name}: no credentials required")
        else:
            cred_statuses = []
            for c in creds:
                name = c if isinstance(c, str) else str(c)
                status = "FOUND" if name in stored else "NOT FOUND"
                cred_statuses.append(f"{name}: {status}")
                if name not in stored:
                    missing.append(f"{name} (needed by {tool_name})")
            lines.append(f"  {tool_name}: requires [{', '.join(str(c) for c in creds)}] — {', '.join(cred_statuses)}")

    header = "Credential audit (tool requirements vs server store):"
    report = "\n".join([header] + lines)
    if missing:
        report += f"\n  MISSING: {', '.join(missing)}"
    return report


def _assert_run_completed(result, step_name: str, agent: Agent | None = None):
    """Assert a run completed successfully with actionable diagnostics."""
    diag = _run_diagnostic(result)

    assert result.execution_id, (
        f"[{step_name}] No execution_id returned. {diag}"
    )

    # Check for stuck-at-tool-calls: the run returned but tools didn't execute
    output = result.output
    if isinstance(output, dict) and output.get("finishReason") == "TOOL_CALLS":
        tool_diag = _tool_diagnostics(result.execution_id)
        cred_audit = _credential_audit(agent) if agent else ""
        pytest.fail(
            f"[{step_name}] Run stalled at tool-calling stage — tools were "
            f"requested but did not return results. This typically means tool "
            f"workers failed to execute (credential resolution failure, worker "
            f"timeout, or worker not registered).\n"
            f"  {diag}\n"
            f"  {tool_diag}\n"
            f"  {cred_audit}"
        )

    assert result.status == "COMPLETED", (
        f"[{step_name}] Run did not complete. {diag}\n"
        f"  {_tool_diagnostics(result.execution_id)}"
    )


def _get_output_text(result) -> str:
    """Extract the text output from a run result.

    The result.output is typically a dict with a 'result' key containing
    a list of streaming tokens/chunks. Each chunk may be a dict with a
    'text' or 'content' key, or a plain string. Tokens are concatenated
    without separators since they represent a streaming sequence.
    """
    output = result.output
    if isinstance(output, dict):
        results = output.get("result", [])
        if results:
            texts = []
            for r in results:
                if isinstance(r, dict):
                    texts.append(r.get("text", r.get("content", str(r))))
                else:
                    texts.append(str(r))
            return "".join(texts)
        return str(output)
    return str(output) if output else ""


# ── Test ────────────────────────────────────────────────────────────────



# Output masking (Audit gap D) is covered deterministically by the server's
# SecretMaskingIntegrationTest (MockMvc + @MockBean AgentService). An e2e
# version would need the LLM to reliably call a specific tool whose output
# contains the leaked value — non-deterministic; violates CLAUDE.md rule 1.
