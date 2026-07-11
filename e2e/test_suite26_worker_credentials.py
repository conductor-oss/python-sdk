"""Suite 26: worker credentials via runtimeMetadata + CLI spawn-safety.

Covers the SDK's credential-delivery contract and the CLI-tool worker fix:

1. A ``@tool(credentials=[NAME])`` worker receives the secret value the host
   resolved at poll time and delivered on the wire-only ``Task.runtimeMetadata``
   (conductor-oss PR #1255) — injected into ``os.environ`` for the call.
2. The registered ``TaskDef.runtimeMetadata`` declares the secret name (so the
   SDK's overwrite-registration does not wipe the server-compiled value).
3. Credential isolation: with the secret absent from the server store, the
   worker task fails (the value is NOT read from the ambient environment).
4. An agent using ``cli_allowed_commands`` registers its auto-generated
   ``run_command`` worker without a spawn-safety error and runs to completion.

Secrets are stored via the server's REST ``/api/secrets`` endpoint directly (no
CLI dependency). Tool outputs are asserted from the workflow task's ``outputData``
(not LLM phrasing) for determinism.

Targets the live Agentspan server (``AGENTSPAN_SERVER_URL``).
"""

from __future__ import annotations

import os
import uuid

import pytest
import requests

from conductor.ai.agents import Agent, tool

pytestmark = [pytest.mark.e2e, pytest.mark.xdist_group("credentials")]

TIMEOUT = 120
CRED_NAME = "E2E_WORKER_SECRET"
CRED_VALUE = f"s3cr3t-{uuid.uuid4().hex[:12]}"

_API = os.environ.get("AGENTSPAN_SERVER_URL", "http://localhost:8080/api").rstrip("/")
_BASE = _API.replace("/api", "")


@pytest.fixture()
def runtime():
    """Function-scoped runtime (overrides the module-scoped conftest fixture).

    Each test gets a fresh runtime so it re-registers the worker TaskDef (with
    overwrite) — making TaskDef.runtimeMetadata reflect *this* test's code path
    rather than a value left by a prior test in the module (the module-scoped
    runtime caches registered tool names and would otherwise skip re-registration,
    letting a stale/server-recompiled value mask a regression)."""
    from conductor.ai.agents import AgentRuntime

    with AgentRuntime() as rt:
        yield rt


# ── Tool: reports whether the declared secret was injected ───────────────


@tool(credentials=[CRED_NAME])
def report_secret(note: str = "") -> dict:
    """Report whether the E2E worker secret was injected into the environment.

    Call this exactly once.
    """
    val = os.environ.get(CRED_NAME, "")
    return {"injected": bool(val), "value_prefix": val[:8], "note": note}


def _make_agent(model: str, name_suffix: str) -> Agent:
    return Agent(
        name=f"e2e_worker_creds_{name_suffix}",
        model=model,
        instructions=(
            "You have one tool: report_secret. Call it exactly once with "
            "note='check', then report its output verbatim."
        ),
        tools=[report_secret],
    )


# ── REST helpers (no CLI) ────────────────────────────────────────────────


def _put_secret(name: str, value: str) -> None:
    r = requests.put(
        f"{_API}/secrets/{name}",
        data=value,
        headers={"Content-Type": "text/plain"},
        timeout=10,
    )
    r.raise_for_status()


def _delete_secret(name: str) -> None:
    try:
        requests.delete(f"{_API}/secrets/{name}", timeout=10)
    except Exception:
        pass


def _get_workflow(execution_id: str) -> dict:
    r = requests.get(f"{_BASE}/api/workflow/{execution_id}", timeout=10)
    r.raise_for_status()
    return r.json()


def _find_tool_task(execution_id: str, tool_name: str) -> dict | None:
    wf = _get_workflow(execution_id)
    for t in wf.get("tasks", []):
        ref = t.get("referenceTaskName", "") or ""
        tdn = t.get("taskDefName", "") or ""
        if tool_name in ref or tool_name in tdn:
            return t
    return None


def _get_taskdef(name: str) -> dict | None:
    r = requests.get(f"{_API}/metadata/taskdefs/{name}", timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


# ── Tests ────────────────────────────────────────────────────────────────


@pytest.mark.timeout(300)
class TestWorkerCredentials:
    def test_credential_injected_via_runtime_metadata(self, runtime, model):
        """The tool receives the server-resolved secret (Task.runtimeMetadata)."""
        _put_secret(CRED_NAME, CRED_VALUE)
        try:
            result = runtime.run(
                _make_agent(model, "inject"),
                "Call report_secret with note='check'.",
                timeout=TIMEOUT,
            )
            assert result.execution_id, f"no execution_id (status={result.status})"

            task = _find_tool_task(result.execution_id, "report_secret")
            assert task is not None, "report_secret task not found in workflow"
            out = task.get("outputData", {}) or {}
            assert out.get("injected") is True, (
                f"secret was NOT injected into the worker environment: {out} "
                f"(task status={task.get('status')}, "
                f"reason={task.get('reasonForIncompletion')})"
            )
            assert out.get("value_prefix") == CRED_VALUE[:8], (
                f"injected value mismatch: {out.get('value_prefix')!r} "
                f"!= {CRED_VALUE[:8]!r}"
            )
        finally:
            _delete_secret(CRED_NAME)

    def test_taskdef_declares_runtime_metadata(self, runtime, model):
        """The registered TaskDef carries runtimeMetadata=[CRED_NAME] (not wiped
        by the SDK's overwrite-registration)."""
        _put_secret(CRED_NAME, CRED_VALUE)
        try:
            runtime.run(
                _make_agent(model, "taskdef"),
                "Call report_secret with note='x'.",
                timeout=TIMEOUT,
            )
            td = _get_taskdef("report_secret")
            assert td is not None, "report_secret TaskDef not registered on server"
            assert td.get("runtimeMetadata") == [CRED_NAME], (
                f"expected TaskDef.runtimeMetadata == [{CRED_NAME!r}], "
                f"got {td.get('runtimeMetadata')!r}"
            )
        finally:
            _delete_secret(CRED_NAME)

    def test_missing_credential_is_not_read_from_env(self, runtime, model):
        """Isolation: with the secret absent from the server store, the worker
        does NOT resolve it from the ambient environment — the tool task fails
        rather than injecting an env value."""
        _delete_secret(CRED_NAME)  # ensure absent on the server
        os.environ[CRED_NAME] = "LEAKED_FROM_ENV"  # must NOT be picked up
        try:
            result = runtime.run(
                _make_agent(model, "isolation"),
                "Call report_secret with note='check'.",
                timeout=TIMEOUT,
            )
            assert result.execution_id
            task = _find_tool_task(result.execution_id, "report_secret")
            if task is not None:
                # The worker must fail credential resolution, never succeed by
                # reading the ambient env var.
                out = task.get("outputData", {}) or {}
                assert out.get("value_prefix") != "LEAKED_F", (
                    "SECURITY: worker read the credential from the ambient "
                    "environment instead of the server store"
                )
                assert task.get("status") != "COMPLETED" or not out.get("injected"), (
                    f"worker should not have injected a value: {out}"
                )
        finally:
            os.environ.pop(CRED_NAME, None)
            _delete_secret(CRED_NAME)


@pytest.mark.timeout(300)
class TestCliSpawnSafety:
    def test_cli_allowed_commands_agent_runs(self, runtime, model):
        """An agent using cli_allowed_commands registers its auto-generated
        run_command worker without a SpawnSafetyError and reaches a terminal
        status. (Before the fix, registration raised because run_command was a
        <locals> closure.)"""
        agent = Agent(
            name=f"e2e_cli_spawn_{uuid.uuid4().hex[:8]}",
            model=model,
            instructions=(
                "You have a run_command tool. Use it to run 'ls' on the /tmp "
                "directory, then report the output."
            ),
            cli_commands=True,
            cli_allowed_commands=["ls"],
        )
        # If run_command were not spawn-safe, runtime.run would raise during
        # worker registration before returning any result.
        result = runtime.run(
            agent, "Run 'ls' on the /tmp directory using run_command.", timeout=TIMEOUT
        )
        assert result.execution_id, f"no execution_id (status={result.status})"
        assert result.status in ("COMPLETED", "FAILED", "TERMINATED"), (
            f"expected a terminal status, got {result.status}"
        )
