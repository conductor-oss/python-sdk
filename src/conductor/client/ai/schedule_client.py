# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Bridge between :class:`Schedule` and Conductor's ``SchedulerClient``.

Handles:
- payload mapping (Schedule -> SaveScheduleRequest, WorkflowSchedule -> ScheduleInfo)
- wire-name prefixing (``{agent}-{short_name}``)
- declarative reconciliation on deploy
- typed error translation
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from conductor.client.ai.schedule import (  # noqa: F401 — re-exported for compat
    Schedule,
    ScheduleInfo,
    _DICT_KEY_MAP,
    _check_unique_names,
    _from_workflow_schedule,
    _prefix,
    _read,
    _to_save_request,
    _translate,
    _unprefix,
)
from conductor.client.ai.schedule_errors import (
    InvalidCronExpression,
    ScheduleNameConflict,
    ScheduleNotFound,
)

# Logger name kept under the conductor.ai.agents hierarchy: AgentRuntime applies
# the user-configured log level to logging.getLogger("conductor.ai"), and this
# client must keep honoring it.
logger = logging.getLogger("conductor.ai.agents.schedule")


class AgentScheduleClient:
    """Thin wrapper around Conductor's ``OrkesSchedulerClient``.

    Pause and resume bypass the conductor-python client and issue raw PUT
    requests, because the bundled scheduler API spec is out of date —
    conductor-python sends ``GET /schedules/{name}/pause`` while modern
    Conductor servers (see ``SchedulerResource.java``) expect PUT.
    """

    def __init__(self, scheduler_client: Any, workflow_client: Any) -> None:
        self._sc = scheduler_client
        self._wc = workflow_client

    def _base_url(self) -> str:
        """Resolve the Conductor API base URL from the underlying client config."""
        # OrkesSchedulerClient -> OrkesBaseClient -> api_client.configuration.host
        # host is typically "http://localhost:8089/api"
        cfg = getattr(self._sc, "configuration", None) or getattr(
            getattr(self._sc, "api_client", None), "configuration", None
        )
        if cfg is None:
            raise RuntimeError("Cannot resolve Conductor base URL from scheduler client")
        host = getattr(cfg, "host", None) or getattr(cfg, "base_url", None)
        if not host:
            raise RuntimeError("Conductor configuration has no host/base_url")
        return host.rstrip("/")

    def _http_put(self, path: str, params: Optional[dict] = None) -> None:
        import requests as _req

        url = f"{self._base_url()}{path}"
        r = _req.put(url, params=params or {}, timeout=15)
        if not 200 <= r.status_code < 300:
            exc: Any = RuntimeError(f"PUT {url} -> {r.status_code}: {r.text}")
            exc.status = r.status_code
            exc.body = r.text
            raise _translate(exc)

    # ── individual operations (wire-name keyed) ──────────────────────

    def save(self, schedule: Schedule, agent_name: str) -> None:
        try:
            self._sc.save_schedule(_to_save_request(schedule, agent_name))
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def get(self, wire_name: str, agent_name: Optional[str] = None) -> ScheduleInfo:
        try:
            ws = self._sc.get_schedule(wire_name)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc
        if isinstance(ws, tuple):
            ws = ws[0] if ws else None
        if not ws:
            raise ScheduleNotFound(f"Schedule '{wire_name}' not found")
        # Conductor returns 200 + empty/null body for missing schedules; the
        # client deserializes that to {} or an empty model. Distinguish that
        # from a real schedule by checking for the required ``name`` field.
        if not _read(ws, "name"):
            raise ScheduleNotFound(f"Schedule '{wire_name}' not found")
        return _from_workflow_schedule(ws, agent_name)

    def list_for_agent(self, agent_name: str) -> List[ScheduleInfo]:
        try:
            results = self._sc.get_all_schedules(workflow_name=agent_name) or []
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc
        return [_from_workflow_schedule(ws, agent_name) for ws in results]

    def pause(self, wire_name: str, reason: Optional[str] = None) -> None:
        # See class docstring: raw PUT bypasses conductor-python's stale GET verb.
        self._http_put(
            f"/scheduler/schedules/{wire_name}/pause",
            params={"reason": reason} if reason else None,
        )

    def resume(self, wire_name: str) -> None:
        self._http_put(f"/scheduler/schedules/{wire_name}/resume")

    def delete(self, wire_name: str) -> None:
        try:
            self._sc.delete_schedule(wire_name)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def run_now(self, info: ScheduleInfo) -> str:
        """Fire the agent once with this schedule's stored input. Returns execution id."""
        from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

        req = StartWorkflowRequest(name=info.agent, input=dict(info.input))
        try:
            return self._wc.start_workflow(req)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def preview_next(
        self, cron: str, n: int = 5, start_at: Optional[int] = None, end_at: Optional[int] = None
    ) -> List[int]:
        try:
            times = self._sc.get_next_few_schedule_execution_times(
                cron_expression=cron,
                schedule_start_time=start_at,
                schedule_end_time=end_at,
                limit=n,
            )
            return list(times) if times else []
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    # ── declarative reconciliation ──────────────────────────────────

    def reconcile(self, agent_name: str, desired: Optional[List[Schedule]]) -> None:
        """Apply the tri-state semantics from spec §5.1:

        - ``desired is None``: no-op
        - ``desired == []``: delete every schedule whose workflow == agent_name
        - ``desired == [...]``: upsert listed, delete others scoped to this agent
        """
        if desired is None:
            return
        _check_unique_names(desired)
        existing = self.list_for_agent(agent_name)
        existing_wire_by_short = {info.short_name: info.name for info in existing}
        desired_short = {s.name for s in desired}

        for short, wire in existing_wire_by_short.items():
            if short not in desired_short:
                logger.info("Pruning schedule %s for agent %s", wire, agent_name)
                self.delete(wire)

        for s in desired:
            logger.info(
                "Upserting schedule %s for agent %s", _prefix(agent_name, s.name), agent_name
            )
            self.save(s, agent_name)


# ``ScheduleClient`` is the pre-relocation name; both resolve to the same class.
ScheduleClient = AgentScheduleClient
