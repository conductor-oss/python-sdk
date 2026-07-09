# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""User-facing dataclasses: ``Schedule`` (input) and ``ScheduleInfo`` (output),
plus the mapping layer between them and Conductor's ``SchedulerClient`` models.

``Schedule`` is what users construct and pass to ``deploy(..., schedules=[...])``.
``ScheduleInfo`` is what ``schedules.list/get`` returns — it carries the
prefixed wire name plus server-computed fields like ``next_run``.

The private helpers below (payload mapping, wire-name prefixing, typed error
translation) are shared by ``OrkesSchedulerClient``'s schedule-lifecycle
methods and the module-level ``schedules.*`` API. The native
``get_schedule``/``save_schedule``/``get_all_schedules`` endpoint methods are
the source of truth for reads/writes/lists; the ``ScheduleInfo`` view exists
for the module-level API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from conductor.client.ai.schedule_errors import (
    InvalidCronExpression,
    ScheduleNameConflict,
    ScheduleNotFound,
)


def _prefix(agent_name: str, short_name: str) -> str:
    return f"{agent_name}-{short_name}"


def _unprefix(agent_name: str, wire_name: str) -> str:
    prefix = f"{agent_name}-"
    return wire_name[len(prefix) :] if wire_name.startswith(prefix) else wire_name


@dataclass(frozen=True)
class Schedule:
    """One cron trigger for an agent.

    Attributes:
        name: Short identifier, unique per agent. Required.
        cron: Cron expression (5- or 6-field; server validates).
        timezone: IANA timezone id; maps to Conductor ``zoneId``.
        input: Workflow input passed when the cron fires.
        catchup: Replay missed fires on resume.
        paused: Start in paused state.
        start_at: Window start (epoch ms or ISO 8601 string).
        end_at: Window end.
        description: Human-readable note.
    """

    name: str
    cron: str
    timezone: str = "UTC"
    input: Dict[str, Any] = field(default_factory=dict)
    catchup: bool = False
    paused: bool = False
    start_at: Optional[int] = None
    end_at: Optional[int] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Schedule.name is required and must be non-empty")
        if not self.cron or not self.cron.strip():
            raise ValueError("Schedule.cron is required and must be non-empty")
        if self.start_at is not None and self.end_at is not None:
            if self.start_at >= self.end_at:
                raise ValueError("Schedule.start_at must be < end_at")


@dataclass(frozen=True)
class ScheduleInfo:
    """Server view of a schedule, as returned by ``schedules.list/get``."""

    name: str
    """Wire name (prefixed with ``{agent}-``)."""

    short_name: str
    """User-supplied name (the part after the ``{agent}-`` prefix)."""

    agent: str
    """Agent / workflow name this schedule fires."""

    cron: str
    timezone: str
    input: Dict[str, Any]
    paused: bool
    paused_reason: Optional[str]
    catchup: bool
    start_at: Optional[int]
    end_at: Optional[int]
    description: Optional[str]
    next_run: Optional[int]
    create_time: Optional[int]
    update_time: Optional[int]
    created_by: Optional[str]
    updated_by: Optional[str]


# ── mapping layer (private) ─────────────────────────────────────────


def _to_save_request(schedule: Schedule, agent_name: str) -> Any:
    """Build a conductor-python ``SaveScheduleRequest`` from a Schedule."""
    from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
    from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

    swr = StartWorkflowRequest(
        name=agent_name,
        input=dict(schedule.input) if schedule.input else {},
    )
    return SaveScheduleRequest(
        name=_prefix(agent_name, schedule.name),
        cron_expression=schedule.cron,
        zone_id=schedule.timezone,
        run_catchup_schedule_instances=schedule.catchup,
        paused=schedule.paused,
        schedule_start_time=schedule.start_at,
        schedule_end_time=schedule.end_at,
        description=schedule.description,
        start_workflow_request=swr,
    )


_DICT_KEY_MAP = {
    "name": ("name",),
    "cron_expression": ("cron_expression", "cronExpression"),
    "zone_id": ("zone_id", "zoneId"),
    "paused": ("paused",),
    "paused_reason": ("paused_reason", "pausedReason"),
    "run_catchup_schedule_instances": (
        "run_catchup_schedule_instances",
        "runCatchupScheduleInstances",
    ),
    "schedule_start_time": ("schedule_start_time", "scheduleStartTime"),
    "schedule_end_time": ("schedule_end_time", "scheduleEndTime"),
    "description": ("description",),
    "next_run_time": ("next_run_time", "nextRunTime"),
    "create_time": ("create_time", "createTime"),
    "updated_time": ("updated_time", "updatedTime"),
    "created_by": ("created_by", "createdBy"),
    "updated_by": ("updated_by", "updatedBy"),
    "start_workflow_request": ("start_workflow_request", "startWorkflowRequest"),
}


def _read(ws: Any, key: str) -> Any:
    """Read a field from either a WorkflowSchedule object (snake_case attrs)
    or a raw camelCase dict — duck-typed ``SchedulerClient`` implementations
    may return either shape."""
    aliases = _DICT_KEY_MAP.get(key, (key,))
    if isinstance(ws, dict):
        for k in aliases:
            if k in ws:
                return ws[k]
        return None
    for k in aliases:
        if hasattr(ws, k):
            return getattr(ws, k)
    return None


def _from_workflow_schedule(ws: Any, agent_name: Optional[str] = None) -> ScheduleInfo:
    """Convert conductor-python ``WorkflowSchedule`` (or raw dict) -> ``ScheduleInfo``.

    ``agent_name`` is optional; if omitted, it's derived from
    ``startWorkflowRequest.name``.
    """
    swr = _read(ws, "start_workflow_request") or {}
    wire_name = _read(ws, "name") or ""
    swr_name = swr.get("name") if isinstance(swr, dict) else getattr(swr, "name", "")
    swr_input = swr.get("input") if isinstance(swr, dict) else getattr(swr, "input", None)
    agent = agent_name or swr_name or ""

    return ScheduleInfo(
        name=wire_name,
        short_name=_unprefix(agent, wire_name),
        agent=swr_name or "",
        cron=_read(ws, "cron_expression") or "",
        timezone=_read(ws, "zone_id") or "UTC",
        input=dict(swr_input) if swr_input else {},
        paused=bool(_read(ws, "paused")),
        paused_reason=_read(ws, "paused_reason"),
        catchup=bool(_read(ws, "run_catchup_schedule_instances")),
        start_at=_read(ws, "schedule_start_time"),
        end_at=_read(ws, "schedule_end_time"),
        description=_read(ws, "description"),
        next_run=_read(ws, "next_run_time"),
        create_time=_read(ws, "create_time"),
        update_time=_read(ws, "updated_time"),
        created_by=_read(ws, "created_by"),
        updated_by=_read(ws, "updated_by"),
    )


def _check_unique_names(schedules: Iterable[Schedule]) -> None:
    seen: set = set()
    for s in schedules:
        if s.name in seen:
            raise ScheduleNameConflict(
                f"Duplicate schedule name '{s.name}' — names must be unique per agent"
            )
        seen.add(s.name)


def _translate(exc: Exception) -> Exception:
    """Best-effort: map conductor-python HTTP errors to typed schedule errors."""
    status = getattr(exc, "status", None) or getattr(exc, "code", None)
    body = getattr(exc, "body", "") or str(exc)
    if status == 404:
        return ScheduleNotFound(body)
    if status == 400 and "cron" in body.lower():
        return InvalidCronExpression(body)
    return exc


def _get_info(raw_client: Any, wire_name: str, agent_name: Optional[str] = None) -> ScheduleInfo:
    """Fetch one schedule via a raw ``SchedulerClient`` and map it to ``ScheduleInfo``.

    Raises :class:`ScheduleNotFound` for missing schedules — including Conductor's
    200-with-empty-body responses, which older/duck-typed clients surface as ``{}``
    or an empty model rather than ``None``.
    """
    try:
        ws = raw_client.get_schedule(wire_name)
    except Exception as exc:  # noqa: BLE001
        raise _translate(exc) from exc
    if isinstance(ws, tuple):
        ws = ws[0] if ws else None
    if not ws:
        raise ScheduleNotFound(f"Schedule '{wire_name}' not found")
    if not _read(ws, "name"):
        raise ScheduleNotFound(f"Schedule '{wire_name}' not found")
    return _from_workflow_schedule(ws, agent_name)


def _list_infos(raw_client: Any, agent_name: str) -> List[ScheduleInfo]:
    """List an agent's schedules via a raw ``SchedulerClient`` as ``ScheduleInfo``s."""
    try:
        results = raw_client.get_all_schedules(workflow_name=agent_name) or []
    except Exception as exc:  # noqa: BLE001
        raise _translate(exc) from exc
    return [_from_workflow_schedule(ws, agent_name) for ws in results]
