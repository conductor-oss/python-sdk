# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Agent-facing models and exceptions for the Conductor SDK.

Home of the agent schedule models (:class:`Schedule`/:class:`ScheduleInfo`) and
the agent exception hierarchy. The ``/agent/*`` client is
:class:`conductor.client.agent_client.AgentClient` (interface) implemented by
:class:`conductor.client.orkes.orkes_agent_client.OrkesAgentClient`; build it via
``OrkesClients.get_agent_client()``. The schedule lifecycle lives on
``OrkesClients.get_scheduler_client()``.

Everything here must stay importable without the ``[agents]`` extra and must
not import ``conductor.ai`` (the agents authoring layer composes these
clients, never the other way around).
"""

from conductor.client.agent_client import AgentClient, SSEUnavailableError
from conductor.client.ai.agent_errors import (
    AgentAPIError,
    AgentNotFoundError,
    ConductorAgentError,
    AgentspanError,
)
from conductor.client.ai.schedule import Schedule, ScheduleInfo
from conductor.client.ai.schedule_errors import (
    InvalidCronExpression,
    ScheduleError,
    ScheduleNameConflict,
    ScheduleNotFound,
)

__all__ = [
    "AgentClient",
    "AgentAPIError",
    "AgentNotFoundError",
    "ConductorAgentError",
    "AgentspanError",
    "InvalidCronExpression",
    "Schedule",
    "ScheduleError",
    "ScheduleInfo",
    "ScheduleNameConflict",
    "ScheduleNotFound",
    "SSEUnavailableError",
]
