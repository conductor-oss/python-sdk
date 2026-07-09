# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""DEPRECATED compatibility shim — the schedule lifecycle lives on ``SchedulerClient``.

``AgentScheduleClient`` used to carry the agent schedule domain layer (payload
mapping, wire-name prefixing, declarative reconcile, typed errors). All of that
now lives on :class:`conductor.client.scheduler_client.SchedulerClient` itself —
build one via ``OrkesClients(configuration).get_scheduler_client()``.

Reads, writes, and lists use the native source-of-truth methods
(``get_schedule``/``save_schedule``/``get_all_schedules``); the old
``get``/``save``/``list_for_agent`` wrappers are gone. The lifecycle operations
(``pause``/``resume``/``delete``/``run_now``/``preview_next``/``reconcile``) are
inherited from ``SchedulerClient`` unchanged.

This class remains only so existing constructions
(``AgentScheduleClient(scheduler_client, workflow_client)``), imports, and
``isinstance`` checks keep working. It is a pure delegation wrapper with zero
logic of its own and is scheduled for removal in the next major release.
"""

from __future__ import annotations

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
from conductor.client.ai.schedule_errors import (  # noqa: F401 — re-exported for compat
    InvalidCronExpression,
    ScheduleNameConflict,
    ScheduleNotFound,
)
from conductor.client.scheduler_client import SchedulerClient


class AgentScheduleClient(SchedulerClient):
    """DEPRECATED — use ``OrkesClients(...).get_scheduler_client()`` instead.

    Pure delegation shim over a wrapped scheduler client: the endpoint methods
    forward to it, the schedule-lifecycle methods are inherited from
    :class:`SchedulerClient`, and ``run_now`` starts workflows through the
    wrapped workflow client. Scheduled for removal in the next major release.
    """

    def __init__(self, scheduler_client: Any, workflow_client: Any) -> None:
        self._sc = scheduler_client
        self._wc = workflow_client

    # ── endpoint delegation (satisfies the SchedulerClient ABC) ──────

    def save_schedule(self, save_schedule_request):
        return self._sc.save_schedule(save_schedule_request)

    def get_schedule(self, name: str):
        return self._sc.get_schedule(name)

    def get_all_schedules(self, workflow_name: Optional[str] = None):
        return self._sc.get_all_schedules(workflow_name=workflow_name)

    def get_next_few_schedule_execution_times(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[int]:
        return self._sc.get_next_few_schedule_execution_times(
            cron_expression=cron_expression,
            schedule_start_time=schedule_start_time,
            schedule_end_time=schedule_end_time,
            limit=limit,
        )

    def delete_schedule(self, name: str):
        return self._sc.delete_schedule(name)

    def pause_schedule(self, name: str, reason: Optional[str] = None):
        # Forward `reason` only when set — the wrapped client may predate the kwarg.
        if reason is None:
            return self._sc.pause_schedule(name)
        return self._sc.pause_schedule(name, reason=reason)

    def pause_all_schedules(self):
        return self._sc.pause_all_schedules()

    def resume_schedule(self, name: str):
        return self._sc.resume_schedule(name)

    def resume_all_schedules(self):
        return self._sc.resume_all_schedules()

    def search_schedule_executions(
        self,
        start: Optional[int] = None,
        size: Optional[int] = None,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
    ):
        return self._sc.search_schedule_executions(
            start=start, size=size, sort=sort, free_text=free_text, query=query
        )

    def requeue_all_execution_records(self):
        return self._sc.requeue_all_execution_records()

    def set_scheduler_tags(self, tags, name: str):
        return self._sc.set_scheduler_tags(tags, name)

    def get_scheduler_tags(self, name: str):
        return self._sc.get_scheduler_tags(name)

    def delete_scheduler_tags(self, tags, name: str):
        return self._sc.delete_scheduler_tags(tags, name)

    # ── run_now capability (inherited lifecycle uses this hook) ──────

    def _start_workflow(self, request) -> str:
        return self._wc.start_workflow(request)


# ``ScheduleClient`` is the pre-relocation name; both resolve to the same class.
ScheduleClient = AgentScheduleClient
