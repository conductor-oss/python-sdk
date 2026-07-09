# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Unit tests for SchedulerClient's concrete schedule-lifecycle surface.

The six domain methods (pause/resume/delete/run_now/preview_next/reconcile) are
concrete on the ABC, implemented over the abstract endpoint methods — any
implementation gets them for free. Reads/writes/lists deliberately have NO
domain twins: get_schedule/save_schedule/get_all_schedules are the source of
truth (the mapped ScheduleInfo view lives in the module-level ``schedules.*``
API via the private ``_get_info`` helper, covered here too).

No network calls.
"""

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from conductor.client.ai.schedule import Schedule, _get_info, _to_save_request
from conductor.client.ai.schedule_errors import InvalidCronExpression, ScheduleNotFound
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.http.rest import ApiException
from conductor.client.scheduler_client import SchedulerClient


class MockScheduler(SchedulerClient):
    """Minimal concrete SchedulerClient: endpoint methods delegate to a MagicMock."""

    def __init__(self, sc: MagicMock, wc: MagicMock) -> None:
        self._sc, self._wc = sc, wc

    def save_schedule(self, save_schedule_request):
        return self._sc.save_schedule(save_schedule_request)

    def get_schedule(self, name: str):
        return self._sc.get_schedule(name)

    def get_all_schedules(self, workflow_name: Optional[str] = None):
        return self._sc.get_all_schedules(workflow_name=workflow_name)

    def get_next_few_schedule_execution_times(self, cron_expression, schedule_start_time=None,
                                              schedule_end_time=None, limit=None) -> List[int]:
        return self._sc.get_next_few_schedule_execution_times(
            cron_expression=cron_expression,
            schedule_start_time=schedule_start_time,
            schedule_end_time=schedule_end_time,
            limit=limit,
        )

    def delete_schedule(self, name: str):
        return self._sc.delete_schedule(name)

    def pause_schedule(self, name: str, reason: Optional[str] = None):
        if reason is None:
            return self._sc.pause_schedule(name)
        return self._sc.pause_schedule(name, reason=reason)

    def pause_all_schedules(self):
        return self._sc.pause_all_schedules()

    def resume_schedule(self, name: str):
        return self._sc.resume_schedule(name)

    def resume_all_schedules(self):
        return self._sc.resume_all_schedules()

    def search_schedule_executions(self, start=None, size=None, sort=None, free_text=None,
                                   query=None):
        return self._sc.search_schedule_executions()

    def requeue_all_execution_records(self):
        return self._sc.requeue_all_execution_records()

    def set_scheduler_tags(self, tags, name: str):
        return self._sc.set_scheduler_tags(tags, name)

    def get_scheduler_tags(self, name: str):
        return self._sc.get_scheduler_tags(name)

    def delete_scheduler_tags(self, tags, name: str):
        return self._sc.delete_scheduler_tags(tags, name)

    def _start_workflow(self, request) -> str:
        return self._wc.start_workflow(request)


def _make() -> tuple:
    sc, wc = MagicMock(), MagicMock()
    return MockScheduler(sc, wc), sc, wc


# ── the six preserved lifecycle methods ─────────────────────────────


class TestLifecycleDelegation:
    def test_pause_bare(self):
        client, sc, _ = _make()
        client.pause("digest-daily")
        sc.pause_schedule.assert_called_once_with("digest-daily")

    def test_pause_with_reason(self):
        client, sc, _ = _make()
        client.pause("digest-daily", reason="maintenance")
        sc.pause_schedule.assert_called_once_with("digest-daily", reason="maintenance")

    def test_resume(self):
        client, sc, _ = _make()
        client.resume("digest-daily")
        sc.resume_schedule.assert_called_once_with("digest-daily")

    def test_delete(self):
        client, sc, _ = _make()
        client.delete("digest-daily")
        sc.delete_schedule.assert_called_once_with("digest-daily")

    def test_preview_next_maps_args_and_returns_list(self):
        client, sc, _ = _make()
        sc.get_next_few_schedule_execution_times.return_value = (1000, 2000)
        out = client.preview_next("0 9 * * *", n=2, start_at=500, end_at=5000)
        assert out == [1000, 2000]
        sc.get_next_few_schedule_execution_times.assert_called_once_with(
            cron_expression="0 9 * * *",
            schedule_start_time=500,
            schedule_end_time=5000,
            limit=2,
        )

    def test_preview_next_empty(self):
        client, sc, _ = _make()
        sc.get_next_few_schedule_execution_times.return_value = None
        assert client.preview_next("0 9 * * *") == []

    def test_run_now_starts_workflow_from_info(self):
        client, sc, wc = _make()
        wc.start_workflow.return_value = "exec-123"
        info = _get_info_stub()
        assert client.run_now(info) == "exec-123"
        req = wc.start_workflow.call_args[0][0]
        assert req.name == "digest"
        assert req.input == {"channel": "#eng"}

    def test_run_now_without_start_capability_raises(self):
        class Bare(MockScheduler):
            def _start_workflow(self, request) -> str:
                return SchedulerClient._start_workflow(self, request)

        client = Bare(MagicMock(), MagicMock())
        with pytest.raises(NotImplementedError):
            client.run_now(_get_info_stub())


def _get_info_stub():
    from conductor.client.ai.schedule import ScheduleInfo

    return ScheduleInfo(
        name="digest-daily", short_name="daily", agent="digest",
        cron="0 9 * * *", timezone="UTC", input={"channel": "#eng"},
        paused=False, paused_reason=None, catchup=False, start_at=None,
        end_at=None, description=None, next_run=None, create_time=None,
        update_time=None, created_by=None, updated_by=None,
    )


# ── typed error translation on the lifecycle surface ───────────────


class TestTypedErrors:
    def test_404_becomes_schedule_not_found(self):
        client, sc, _ = _make()
        sc.pause_schedule.side_effect = ApiException(status=404, reason="Not Found")
        with pytest.raises(ScheduleNotFound):
            client.pause("missing")

    def test_400_cron_becomes_invalid_cron(self):
        client, sc, _ = _make()
        sc.get_all_schedules.return_value = []
        exc = ApiException(status=400, reason="Bad Request")
        exc.body = "Invalid cron expression"
        sc.save_schedule.side_effect = exc
        with pytest.raises(InvalidCronExpression):
            client.reconcile("digest", [Schedule(name="bad", cron="not-a-cron")])


# ── reconcile tri-state (full matrix lives in tests/unit/ai/test_schedule.py) ──


class TestReconcileTriState:
    def _store_backed(self):
        client, sc, _ = _make()
        store: dict = {}
        sc.save_schedule.side_effect = lambda req: store.__setitem__(req.name, req)
        sc.delete_schedule.side_effect = lambda name: store.pop(name, None)

        def get_all(workflow_name=None):
            return [
                WorkflowSchedule(
                    name=req.name,
                    cron_expression=req.cron_expression,
                    start_workflow_request=req.start_workflow_request,
                )
                for req in store.values()
                if not workflow_name or req.start_workflow_request.name == workflow_name
            ]

        sc.get_all_schedules.side_effect = get_all
        return client, sc, store

    def test_none_is_noop(self):
        client, sc, _ = self._store_backed()
        client.reconcile("digest", None)
        sc.save_schedule.assert_not_called()
        sc.delete_schedule.assert_not_called()

    def test_empty_list_purges(self):
        client, sc, store = self._store_backed()
        sc.save_schedule(_to_save_request(Schedule(name="a", cron="* * * * *"), "digest"))
        assert len(store) == 1
        client.reconcile("digest", [])
        assert store == {}

    def test_upsert_and_prune(self):
        client, sc, store = self._store_backed()
        sc.save_schedule(_to_save_request(Schedule(name="old", cron="0 1 * * *"), "digest"))
        client.reconcile("digest", [Schedule(name="new", cron="0 2 * * *")])
        assert set(store) == {"digest-new"}


# ── _get_info: the mapped read used by the module-level schedules API ──


class TestGetInfoHelper:
    def test_maps_typed_model(self):
        from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

        sc = MagicMock()
        sc.get_schedule.return_value = WorkflowSchedule(
            name="digest-daily",
            cron_expression="0 9 * * *",
            paused=True,
            start_workflow_request=StartWorkflowRequest(name="digest", input={"k": 1}),
        )
        info = _get_info(sc, "digest-daily")
        assert info.short_name == "daily"
        assert info.agent == "digest"
        assert info.paused is True
        assert info.input == {"k": 1}

    def test_none_raises_not_found(self):
        sc = MagicMock()
        sc.get_schedule.return_value = None
        with pytest.raises(ScheduleNotFound):
            _get_info(sc, "missing")

    def test_empty_model_raises_not_found(self):
        sc = MagicMock()
        sc.get_schedule.return_value = WorkflowSchedule()
        with pytest.raises(ScheduleNotFound):
            _get_info(sc, "missing")


# ── source-of-truth guard (user decision: no domain twins for get/save/list) ──


class TestSourceOfTruth:
    def test_no_domain_twins_for_reads_writes_lists(self):
        # get_schedule/save_schedule/get_all_schedules ARE the API — the old
        # mapped wrappers (get/save/list_for_agent) must not creep back onto
        # any schedule client.
        from conductor.client.ai.schedule_client import AgentScheduleClient

        for cls in (SchedulerClient, AgentScheduleClient):
            for method in ("get", "save", "list_for_agent"):
                assert not hasattr(cls, method), f"{cls.__name__}.{method} must not exist"


# ── import-weight guard ─────────────────────────────────────────────


class TestImportWeight:
    def test_scheduler_client_does_not_import_agent_surface(self):
        # scheduler_client.py is on virtually every SDK program's import path;
        # its conductor.client.ai imports must stay lazy (call-time only).
        code = (
            "import sys\n"
            "import conductor.client.scheduler_client\n"
            "leaked = [m for m in sys.modules if m.startswith('conductor.client.ai')]\n"
            "assert not leaked, f'agent surface leaked at import time: {leaked}'\n"
        )
        subprocess.run([sys.executable, "-c", code], check=True)
