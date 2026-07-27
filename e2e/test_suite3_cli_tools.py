"""Suite 3: CLI Tools — command whitelist and credential lifecycle.

Tests CLI tool execution with credential isolation:
  1. ls and mktemp succeed without credentials
  2. gh fails without server credential (env vars NOT used)
  3. gh succeeds after credential added to server
  4. Commands outside whitelist are rejected (cd)

Single sequential test with try/finally cleanup.
No mocks. Real server, real CLI, real LLM.
"""

import os
import re
import subprocess

import pytest
import requests

from conductor.ai.agents import Agent, tool
from conductor.ai.agents.cli_config import _validate_cli_command

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.xdist_group("credentials"),
]

CRED_NAME = "GITHUB_TOKEN"
TIMEOUT = 120


# ── Tools ───────────────────────────────────────────────────────────────


@tool
def cli_ls(path: str = ".") -> str:
    """List directory contents using the ls command."""
    result = subprocess.run(["ls", path], capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        return f"ls_error:{result.stderr.strip()[:200]}"
    return f"ls_ok:{result.stdout.strip()[:200]}"


@tool
def cli_mktemp() -> str:
    """Create a temporary file and return its path."""
    result = subprocess.run(["mktemp"], capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        return f"mktemp_error:{result.stderr.strip()[:200]}"
    return f"mktemp_ok:{result.stdout.strip()}"


@tool(credentials=[CRED_NAME])
def cli_gh(subcommand: str, args: str = "") -> str:
    """Run a gh CLI command. Requires GITHUB_TOKEN credential.
    Example: subcommand="repo list", args="--limit 3"
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN not found in environment. "
            "The server should have injected it via credential resolution."
        )
    cmd = ["gh"] + subcommand.split()
    if args:
        cmd += args.split()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return f"gh_error:{result.stderr.strip()[:200]}"
    return f"gh_ok:{result.stdout.strip()[:200]}"


# ── Helpers ─────────────────────────────────────────────────────────────


AGENT_INSTRUCTIONS = """\
You have three tools: cli_ls, cli_mktemp, and cli_gh.
You MUST call each tool exactly once as directed and report the output verbatim.
Do not skip any tool. Do not add commentary beyond the results.
"""

PROMPT_ALL_THREE = """\
Call all three tools:
1. cli_ls with path="/tmp"
2. cli_mktemp (no arguments)
3. cli_gh with subcommand="repo list" and args="--limit 3"
Report each result in this format:
  cli_ls: <output>
  cli_mktemp: <output>
  cli_gh: <output>
"""

PROMPT_CD = """\
You MUST call the run_command tool with command="cd" and args=["/etc"].
Report the exact output or error message verbatim.
"""


def _make_agent(model: str) -> Agent:
    """Agent with custom CLI tools for credential testing."""
    return Agent(
        name="e2e_cli_tools",
        model=model,
        instructions=AGENT_INSTRUCTIONS,
        tools=[cli_ls, cli_mktemp, cli_gh],
    )


def _make_whitelist_agent(model: str) -> Agent:
    """Agent with CLI whitelist for command filtering testing."""
    return Agent(
        name="e2e_cli_whitelist",
        model=model,
        instructions=(
            "You have a run_command tool that executes CLI commands. "
            "Always call the tool as instructed and report the exact output."
        ),
        cli_commands=True,
        cli_allowed_commands=["ls", "mktemp", "gh"],
    )


def _get_output_text(result) -> str:
    """Extract the text output from a run result.

    The result.output is typically a dict with a 'result' key containing
    a list of streaming tokens/chunks.
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


def _run_diagnostic(result) -> str:
    """Build a diagnostic string from a run result for error messages."""
    parts = [
        f"status={result.status}",
        f"execution_id={result.execution_id}",
    ]
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


def _get_workflow(execution_id: str) -> dict:
    """Fetch workflow from server API."""
    base = os.environ.get("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    base_url = base.rstrip("/").replace("/api", "")
    resp = requests.get(f"{base_url}/api/workflow/{execution_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def _tool_diagnostics(execution_id: str, tool_names: set[str]) -> str:
    """Fetch workflow tasks and report tool-related task statuses."""
    try:
        wf = _get_workflow(execution_id)
    except Exception as e:
        return f"(could not fetch workflow: {e})"

    tool_tasks = []
    for task in wf.get("tasks", []):
        ref = task.get("referenceTaskName", "")
        status = task.get("status", "")
        reason = task.get("reasonForIncompletion", "")
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
        wf_status = wf.get("status", "unknown")
        wf_reason = wf.get("reasonForIncompletion", "")
        summary = f"No tool tasks found in workflow. workflow_status={wf_status}"
        if wf_reason:
            summary += f" reason={wf_reason}"
        return summary

    return "\n  ".join(["Tool tasks:"] + tool_tasks)


def _assert_run_completed(result, step_name: str):
    """Assert a run completed successfully with actionable diagnostics."""
    diag = _run_diagnostic(result)

    assert result.execution_id, f"[{step_name}] No execution_id returned. {diag}"

    output = result.output
    if isinstance(output, dict) and output.get("finishReason") == "TOOL_CALLS":
        tool_diag = _tool_diagnostics(
            result.execution_id, {"cli_ls", "cli_mktemp", "cli_gh"}
        )
        pytest.fail(
            f"[{step_name}] Run stalled at tool-calling stage — tools were "
            f"requested but did not return results.\n"
            f"  {diag}\n"
            f"  {tool_diag}"
        )

    assert result.status == "COMPLETED", (
        f"[{step_name}] Run did not complete. {diag}\n"
        f"  {_tool_diagnostics(result.execution_id, {'cli_ls', 'cli_mktemp', 'cli_gh'})}"
    )
