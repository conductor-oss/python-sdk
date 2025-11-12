"""
Workflow event definitions.

These events represent workflow client operations like starting workflows
and handling external payload storage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from conductor.client.event.conductor_event import ConductorEvent


@dataclass(frozen=True)
class WorkflowEvent(ConductorEvent):
    """
    Base class for all workflow events.

    Attributes:
        name: The workflow name
        version: The workflow version (optional)
    """
    name: str
    version: Optional[int] = None


@dataclass(frozen=True)
class WorkflowStarted(WorkflowEvent):
    """
    Event published when a workflow is started.

    Attributes:
        name: The workflow name
        version: The workflow version
        success: Whether the workflow started successfully
        workflow_id: The ID of the started workflow (if successful)
        cause: The exception if workflow start failed
        timestamp: UTC timestamp when the event was created
    """
    success: bool = True
    workflow_id: Optional[str] = None
    cause: Optional[Exception] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class WorkflowInputPayloadSize(WorkflowEvent):
    """
    Event published when workflow input payload size is measured.

    Attributes:
        name: The workflow name
        version: The workflow version
        size_bytes: Size of the workflow input payload in bytes
        timestamp: UTC timestamp when the event was created
    """
    size_bytes: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class WorkflowPayloadUsed(WorkflowEvent):
    """
    Event published when external storage is used for workflow payload.

    Attributes:
        name: The workflow name
        version: The workflow version
        operation: The operation type (e.g., 'READ' or 'WRITE')
        payload_type: The type of payload (e.g., 'WORKFLOW_INPUT', 'WORKFLOW_OUTPUT')
        timestamp: UTC timestamp when the event was created
    """
    operation: str = ""
    payload_type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
