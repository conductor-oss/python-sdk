"""Schedule-specific exceptions."""

from __future__ import annotations

from conductor.client.ai.agent_errors import ConductorAgentError


class ScheduleError(ConductorAgentError):
    """Base class for schedule errors."""


class ScheduleNameConflict(ScheduleError):
    """Two schedules in the same agent share a name."""


class ScheduleNotFound(ScheduleError):
    """No schedule matches the given name."""


class InvalidCronExpression(ScheduleError):
    """Server rejected the cron expression as malformed."""
