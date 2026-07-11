"""Suite 24: AgentClient (transport) + runtime run/start + schedule surface.

``runtime.client`` is the transport :class:`AgentClient`
(``conductor.client.orkes.orkes_agent_client.OrkesAgentClient``) — the
``/agent/*`` control-plane endpoints built on the shared ``ApiClient``. The
run/start DX lives on the runtime; the schedule lifecycle is reachable from both
``runtime.schedules_client()`` and ``runtime.client.schedules``.

Verifies:
- ``runtime.run`` on an LLM-only agent (no local tools) reaches COMPLETED.
- ``runtime.start`` returns a handle that joins to COMPLETED.
- ``schedules.reconcile(agent, [Schedule(...)])`` upserts and lists; a
  counterfactual ``reconcile([])`` purges it.
- ``runtime.client`` is the runtime's own transport client, and both schedule
  accessors return working ``SchedulerClient``s.

The scheduled "agent" target is a bare no-op Conductor workflow so no LLM is
invoked for the schedule tests.

Targets the live Agentspan server (``AGENTSPAN_SERVER_URL``). The schedule
tests are skipped automatically if the server's Conductor lacks the scheduler
module.
"""

from __future__ import annotations

import os
import uuid

import pytest
import requests

from conductor.ai.agents import Agent
from conductor.ai.agents.result import Status
from conductor.ai.agents.schedule import Schedule

pytestmark = [pytest.mark.e2e]

MODEL = os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini")
_API = os.environ.get("AGENTSPAN_SERVER_URL", "http://localhost:8080/api").rstrip("/")


def _scheduler_available() -> bool:
    try:
        r = requests.get(f"{_API}/scheduler/schedules", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


_SCHED_SKIP = pytest.mark.skipif(
    not _scheduler_available(),
    reason=f"Conductor scheduler not reachable at {_API}/scheduler/schedules",
)


# ── run: LLM-only agent via the control-plane client ─────────────────────


class TestControlPlaneRun:
    def test_run_llm_only_agent_completes(self, runtime, model):
        """AgentClient.run on a tool-less agent reaches COMPLETED — no workers."""
        agent = Agent(
            name=f"e2e_client_run_{uuid.uuid4().hex[:8]}",
            model=model,
            instructions="You are a calculator. Reply with only the number.",
        )

        result = runtime.run(agent, "What is 2 + 2? Reply with only the number.")

        assert result.status == Status.COMPLETED, (
            f"expected COMPLETED, got {result.status} (error={result.error})"
        )
        assert result.execution_id

    def test_start_returns_handle_then_joins(self, runtime, model):
        """runtime.start returns a handle that joins to a COMPLETED result."""
        agent = Agent(
            name=f"e2e_client_start_{uuid.uuid4().hex[:8]}",
            model=model,
            instructions="Reply with the single word: ok",
        )

        handle = runtime.start(agent, "Say ok")
        assert handle.execution_id
        result = handle.join(timeout=120)
        assert result.status == Status.COMPLETED


# ── schedule: deploy + reconcile via the client's schedule surface ───────


@_SCHED_SKIP
class TestSchedule:
    @pytest.fixture()
    def noop_agent_name(self):
        """Register a no-op Conductor workflow to act as the schedule target."""
        name = f"e2e_client_sched_{uuid.uuid4().hex[:8]}"
        workflow_def = {
            "name": name,
            "version": 1,
            "description": "AgentClient schedule e2e no-op workflow",
            "ownerEmail": "e2e@agentspan.test",
            "schemaVersion": 2,
            "timeoutSeconds": 60,
            "timeoutPolicy": "TIME_OUT_WF",
            "tasks": [
                {
                    "name": "noop_terminate",
                    "taskReferenceName": "noop_terminate_ref",
                    "type": "TERMINATE",
                    "inputParameters": {
                        "terminationStatus": "COMPLETED",
                        "workflowOutput": {"ok": True},
                    },
                }
            ],
        }
        r = requests.post(f"{_API}/metadata/workflow", json=workflow_def, timeout=10)
        assert r.status_code in (200, 204), f"register wf failed: {r.status_code} {r.text}"
        yield name
        # teardown: purge schedules + unregister wf (best-effort)
        try:
            requests.delete(f"{_API}/metadata/workflow/{name}/1", timeout=5)
        except Exception:
            pass

    def test_schedule_then_list_then_purge(self, runtime, noop_agent_name):
        schedules = runtime.client.schedules

        # Clean slate.
        schedules.reconcile(noop_agent_name, [])
        assert not schedules.get_all_schedules(workflow_name=noop_agent_name)

        # Reconcile a single schedule via the client's schedule surface.
        schedules.reconcile(
            noop_agent_name,
            [Schedule(name="daily", cron="0 0 9 * * ?", input={"k": 1})],
        )
        by_wire = {s.name: s for s in schedules.get_all_schedules(workflow_name=noop_agent_name)}
        assert set(by_wire) == {f"{noop_agent_name}-daily"}
        assert by_wire[f"{noop_agent_name}-daily"].cron_expression == "0 0 9 * * ?"

        # Counterfactual: reconcile with an empty list purges it.
        schedules.reconcile(noop_agent_name, [])
        assert not schedules.get_all_schedules(workflow_name=noop_agent_name)


# ── structural consistency: transport client + schedule accessors ────────


class TestScheduleSurfaceConsistency:
    def test_both_schedule_accessors_are_scheduler_clients(self, runtime):
        """Both runtime.schedules_client() and runtime.client.schedules return a
        working SchedulerClient (the transport client builds its own from the same
        Configuration; they are no longer required to be the same instance)."""
        from conductor.client.scheduler_client import SchedulerClient

        assert isinstance(runtime.schedules_client(), SchedulerClient)
        assert isinstance(runtime.client.schedules, SchedulerClient)

    def test_client_is_the_runtime_agent_client(self, runtime):
        """runtime.client is the runtime's own transport AgentClient (not a copy)."""
        from conductor.client.agent_client import AgentClient

        assert runtime.client is runtime._agent_client
        assert isinstance(runtime.client, AgentClient)
