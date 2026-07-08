# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Backward-compat shim — the schedule client moved to ``conductor.client.ai``.

Import :class:`AgentScheduleClient` from :mod:`conductor.client.ai` (or build one
via ``OrkesClients.get_agent_schedule_client()``) going forward. ``ScheduleClient``
is the same class object, so existing constructions and ``isinstance`` checks are
unaffected.
"""

from __future__ import annotations

from conductor.client.ai.schedule_client import (  # noqa: F401
    AgentScheduleClient,
    ScheduleClient,
    _check_unique_names,
    _from_workflow_schedule,
    _read,
    _to_save_request,
    _translate,
)
