# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Regeneration guards for the HAND-FIXes in scheduler_resource_api.py, plus the
OrkesSchedulerClient contract they enable.

The scheduler API spec used for code generation is out of date; these tests pin the
hand-applied fixes so a future regeneration that reverts them fails loudly:

- per-schedule pause/resume send PUT (OSS Conductor dialect; Orkes servers get a
  GET fallback on 405 — see the verb-split analysis in the SDK docs)
- pause accepts an optional ``reason`` query param
- ``get_schedule`` deserializes to ``WorkflowSchedule`` (not a raw camelCase dict)

No network calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.scheduler_resource_api import SchedulerResourceApi
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.http.rest import ApiException
from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient


def _client_with_mocks() -> OrkesSchedulerClient:
    client = OrkesSchedulerClient(Configuration(server_api_url="http://localhost:8080/api"))
    client.schedulerResourceApi = MagicMock()
    client.api_client = MagicMock()
    client.api_client.select_header_accept.return_value = "application/json"
    return client


# ── HAND-FIX guards on the generated resource API ───────────────────


class TestSchedulerResourceHandFixes:
    def setup_method(self):
        self.api_client = MagicMock()
        self.api = SchedulerResourceApi(api_client=self.api_client)

    def _call_args(self):
        assert self.api_client.call_api.call_count == 1
        return self.api_client.call_api.call_args

    def test_pause_sends_put(self):
        self.api.pause_schedule("sched-1")
        args, kwargs = self._call_args()
        assert args[0] == "/scheduler/schedules/{name}/pause"
        assert args[1] == "PUT"
        assert args[3] == []  # no reason -> no query params

    def test_pause_forwards_reason_query_param(self):
        self.api.pause_schedule("sched-1", reason="maintenance window")
        args, _ = self._call_args()
        assert args[1] == "PUT"
        assert ("reason", "maintenance window") in args[3]

    def test_resume_sends_put(self):
        self.api.resume_schedule("sched-1")
        args, _ = self._call_args()
        assert args[0] == "/scheduler/schedules/{name}/resume"
        assert args[1] == "PUT"

    def test_get_schedule_deserializes_to_workflow_schedule(self):
        self.api.get_schedule("sched-1")
        args, kwargs = self._call_args()
        assert args[0] == "/scheduler/schedules/{name}"
        assert args[1] == "GET"
        assert kwargs["response_type"] == "WorkflowSchedule"


# ── OrkesSchedulerClient contract over the fixed transport ─────────


class TestOrkesSchedulerClientContract:
    def test_get_schedule_returns_model_when_name_present(self):
        client = _client_with_mocks()
        ws = WorkflowSchedule(name="sched-1", cron_expression="0 9 * * *")
        client.schedulerResourceApi.get_schedule.return_value = ws
        assert client.get_schedule("sched-1") is ws

    def test_get_schedule_normalizes_empty_model_to_none(self):
        client = _client_with_mocks()
        client.schedulerResourceApi.get_schedule.return_value = WorkflowSchedule()
        assert client.get_schedule("missing") is None

    def test_get_schedule_normalizes_falsy_to_none(self):
        client = _client_with_mocks()
        client.schedulerResourceApi.get_schedule.return_value = None
        assert client.get_schedule("missing") is None

    def test_pause_bare_call_omits_reason(self):
        client = _client_with_mocks()
        client.pause_schedule("sched-1")
        client.schedulerResourceApi.pause_schedule.assert_called_once_with("sched-1")

    def test_pause_forwards_reason(self):
        client = _client_with_mocks()
        client.pause_schedule("sched-1", reason="maintenance")
        client.schedulerResourceApi.pause_schedule.assert_called_once_with(
            "sched-1", reason="maintenance"
        )


# ── Verb fallback for Orkes servers (GET-only dialect) ─────────────


class TestVerbFallback:
    def test_405_falls_back_to_get(self):
        client = _client_with_mocks()
        client.schedulerResourceApi.pause_schedule.side_effect = ApiException(
            status=405, reason="Method Not Allowed"
        )
        client.pause_schedule("sched-1", reason="maintenance")
        args, _ = client.api_client.call_api.call_args
        assert args[0] == "/scheduler/schedules/{name}/pause"
        assert args[1] == "GET"
        assert args[2] == {"name": "sched-1"}
        assert ("reason", "maintenance") in args[3]

    def test_405_result_is_cached_for_subsequent_calls(self):
        client = _client_with_mocks()
        client.schedulerResourceApi.pause_schedule.side_effect = ApiException(
            status=405, reason="Method Not Allowed"
        )
        client.pause_schedule("sched-1")
        client.pause_schedule("sched-2")
        client.resume_schedule("sched-1")
        # PUT attempted exactly once; everything after the 405 goes straight to GET.
        assert client.schedulerResourceApi.pause_schedule.call_count == 1
        client.schedulerResourceApi.resume_schedule.assert_not_called()
        assert client.api_client.call_api.call_count == 3

    def test_404_propagates_without_fallback(self):
        client = _client_with_mocks()
        client.schedulerResourceApi.pause_schedule.side_effect = ApiException(
            status=404, reason="Not Found"
        )
        with pytest.raises(ApiException):
            client.pause_schedule("missing")
        client.api_client.call_api.assert_not_called()
        assert client._legacy_scheduler_verbs is False

    def test_resume_405_falls_back_to_get(self):
        client = _client_with_mocks()
        client.schedulerResourceApi.resume_schedule.side_effect = ApiException(
            status=405, reason="Method Not Allowed"
        )
        client.resume_schedule("sched-1")
        args, _ = client.api_client.call_api.call_args
        assert args[0] == "/scheduler/schedules/{name}/resume"
        assert args[1] == "GET"
        assert args[3] == []
