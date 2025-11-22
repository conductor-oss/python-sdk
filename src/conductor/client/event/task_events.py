"""
Task client event definitions.

These events represent task client operations related to task payloads
and external storage usage.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from conductor.client.event.conductor_event import ConductorEvent


@dataclass(frozen=True)
class TaskEvent(ConductorEvent):
    """
    Base class for all task client events.

    Attributes:
        task_type: The task definition name
    """
    task_type: str


@dataclass(frozen=True)
class TaskResultPayloadSize(TaskEvent):
    """
    Event published when task result payload size is measured.

    Attributes:
        task_type: The task definition name
        size_bytes: Size of the task result payload in bytes
        timestamp: UTC timestamp when the event was created
    """
    size_bytes: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TaskPayloadUsed(TaskEvent):
    """
    Event published when external storage is used for task payload.

    Attributes:
        task_type: The task definition name
        operation: The operation type (e.g., 'READ' or 'WRITE')
        payload_type: The type of payload (e.g., 'TASK_INPUT', 'TASK_OUTPUT')
        timestamp: UTC timestamp when the event was created
    """
    operation: str
    payload_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
