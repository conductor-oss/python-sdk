"""E2E test infrastructure. No mocks. Real server, real CLI, real services."""

import os
import subprocess

import pytest
import requests

# ── Configuration from env (set by orchestrator) ────────────────────────

SERVER_URL = os.environ.get("AGENTSPAN_SERVER_URL", "http://localhost:8080/api")
BASE_URL = SERVER_URL.rstrip("/").replace("/api", "")
CLI_PATH = os.environ.get("AGENTSPAN_CLI_PATH", "agentspan")
MCP_TESTKIT_URL = os.environ.get("MCP_TESTKIT_URL", "http://localhost:3001")
MODEL = os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini")


# ── Markers ─────────────────────────────────────────────────────────────


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring live server")
    config.addinivalue_line(
        "markers", "xdist_group(name): assign test to named xdist group for serial execution"
    )
    config.addinivalue_line(
        "markers", "timeout(seconds): per-test timeout (requires pytest-timeout)"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-retry transient e2e flakes.

    These suites drive a real server + real LLM, so individual tests flake
    nondeterministically on transient conditions — the workflow still
    RUNNING at the client timeout, a tool-call batch not returning, LLM
    phrasing variance. Retrying up to twice lets a one-off flake recover
    while a genuinely broken test still fails all three attempts (no real
    regression is masked).

    Configured here rather than in the CI command so it also applies to
    local e2e runs. Honoured only when pytest-rerunfailures is installed
    (the dev extra); without it the ``flaky`` marker is a harmless no-op.
    """
    rerun = pytest.mark.flaky(reruns=2, reruns_delay=5)
    for item in items:
        if item.get_closest_marker("e2e"):
            item.add_marker(rerun)


# ── Session-scoped health check ─────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def verify_server():
    """Fail fast if server is not running."""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.json().get("healthy"), "Server reports unhealthy"
    except Exception as e:
        pytest.skip(f"Server not available at {BASE_URL}: {e}")


# ── Runtime fixture ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def runtime():
    """Module-scoped AgentRuntime — shared across tests in a module."""
    from conductor.ai.agents import AgentRuntime

    with AgentRuntime() as rt:
        yield rt


# ── Model fixture ───────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def model():
    return MODEL


@pytest.fixture(scope="session")
def mcp_url():
    return MCP_TESTKIT_URL


# ── CLI credential helper ──────────────────────────────────────────────


class CredentialsCLI:
    """Wraps the agentspan CLI for credential operations.

    The CLI expects AGENTSPAN_SERVER_URL without the /api suffix
    (e.g., http://localhost:8080). It appends /api internally.
    """

    def __init__(self, cli_path: str, server_url: str):
        self._cli = cli_path
        # CLI expects base URL without /api — strip it if present
        self._server_url = server_url.rstrip("/").removesuffix("/api")

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [self._cli] + list(args)
        env = {**os.environ, "AGENTSPAN_SERVER_URL": self._server_url}
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=15, env=env
        )

    def set(self, name: str, value: str) -> None:
        result = self._run("credentials", "set", name, value)
        assert result.returncode == 0, (
            f"credentials set {name} failed: {result.stderr}"
        )

    def delete(self, name: str) -> None:
        result = self._run("credentials", "delete", name)
        # Ignore "not found" errors during cleanup
        if result.returncode != 0 and "not found" not in result.stderr.lower():
            raise AssertionError(
                f"credentials delete {name} failed: {result.stderr}"
            )

    def list(self) -> str:
        result = self._run("credentials", "list")
        assert result.returncode == 0, f"credentials list failed: {result.stderr}"
        return result.stdout


@pytest.fixture(scope="session")
def cli_credentials():
    return CredentialsCLI(CLI_PATH, SERVER_URL)


# ── Server API helpers ──────────────────────────────────────────────────


def get_workflow(execution_id: str) -> dict:
    """Fetch full workflow execution from server."""
    resp = requests.get(f"{BASE_URL}/api/workflow/{execution_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_task_by_name(execution_id: str, task_ref_prefix: str) -> list:
    """Find tasks in a workflow whose referenceTaskName contains prefix."""
    wf = get_workflow(execution_id)
    return [
        t
        for t in wf.get("tasks", [])
        if task_ref_prefix in t.get("referenceTaskName", "")
    ]


# ── Server capability: TaskDef.runtimeMetadata (conductor-oss PR #1255) ──
#
# Worker credential delivery relies on the server persisting a worker's declared
# TaskDef.runtimeMetadata and delivering the resolved values on Task.runtimeMetadata
# at poll time. Released servers (through v0.4.2) do NOT implement this yet — they
# drop the field — so the credential-delivery e2e tests would fail there for a
# reason unrelated to the SDK. Probe the running server once and skip those tests
# when unsupported.
#
# conductor-oss implements this from 3.32.0-rc.8 onward (see
# .github/workflows/agent-e2e.yml's CONDUCTOR_SERVER_VERSION) — this guard lets the
# credential tests run automatically against any server that has it, no test
# change needed.

_RUNTIME_METADATA_SUPPORT = None


def _probe_runtime_metadata_support() -> bool:
    import uuid

    name = f"_rtmd_cap_probe_{uuid.uuid4().hex[:8]}"
    try:
        r = requests.post(
            f"{BASE_URL}/api/metadata/taskdefs",
            json=[{"name": name, "runtimeMetadata": ["PROBE"],
                   "retryCount": 0, "timeoutSeconds": 0}],
            timeout=8,
        )
        if r.status_code not in (200, 204):
            return False
        g = requests.get(f"{BASE_URL}/api/metadata/taskdefs/{name}", timeout=8)
        return g.status_code == 200 and g.json().get("runtimeMetadata") == ["PROBE"]
    except Exception:
        return False
    finally:
        try:
            requests.delete(f"{BASE_URL}/api/metadata/taskdefs/{name}", timeout=5)
        except Exception:
            pass


def _server_supports_runtime_metadata() -> bool:
    global _RUNTIME_METADATA_SUPPORT
    if _RUNTIME_METADATA_SUPPORT is None:
        _RUNTIME_METADATA_SUPPORT = _probe_runtime_metadata_support()
    return _RUNTIME_METADATA_SUPPORT


@pytest.fixture
def requires_runtime_metadata():
    """Skip a test unless the server implements the TaskDef.runtimeMetadata
    credential-delivery contract (conductor-oss PR #1255)."""
    if not _server_supports_runtime_metadata():
        pytest.skip(
            "server does not persist/deliver TaskDef.runtimeMetadata "
            "(conductor-oss PR #1255) — worker credential injection requires it. "
            "Needs conductor-oss >= 3.32.0-rc.8 (see CONDUCTOR_SERVER_VERSION in "
            ".github/workflows/agent-e2e.yml)."
        )
