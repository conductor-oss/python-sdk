# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Agent-facing clients and models for the Conductor SDK.

Canonical home of the ``/agent/*`` transport (:class:`AgentApiClient`), the
agent cron-schedule client (:class:`AgentScheduleClient`), their models, and
the agent exception hierarchy. Build the clients via
``OrkesClients.get_agent_client()`` / ``get_agent_schedule_client()``.

Everything here must stay importable without the ``[agents]`` extra and must
not import ``conductor.ai`` (the agents authoring layer composes these
clients, never the other way around).
"""

from conductor.client.ai.agent_api_client import AgentApiClient, SSEUnavailableError
from conductor.client.ai.agent_errors import (
    AgentAPIError,
    AgentNotFoundError,
    AgentspanError,
)
from conductor.client.ai.schedule import Schedule, ScheduleInfo
from conductor.client.ai.schedule_client import AgentScheduleClient, ScheduleClient
from conductor.client.ai.schedule_errors import (
    InvalidCronExpression,
    ScheduleError,
    ScheduleNameConflict,
    ScheduleNotFound,
)

__all__ = [
    "AgentApiClient",
    "AgentAPIError",
    "AgentNotFoundError",
    "AgentScheduleClient",
    "AgentspanError",
    "InvalidCronExpression",
    "Schedule",
    "ScheduleClient",
    "ScheduleError",
    "ScheduleInfo",
    "ScheduleNameConflict",
    "ScheduleNotFound",
    "SSEUnavailableError",
]
