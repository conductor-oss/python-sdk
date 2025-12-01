"""
Task runner event definitions.

These events represent the lifecycle of task polling and execution in the task runner.
They match the Java SDK's TaskRunnerEvent hierarchy.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from conductor.client.event.conductor_event import ConductorEvent

if TYPE_CHECKING:
    from conductor.client.http.models.task_result import TaskResult


@dataclass(frozen=True)
class TaskRunnerEvent(ConductorEvent):
    """
    Base class for all task runner events.

    Attributes:
        task_type: The task definition name
        timestamp: UTC timestamp when the event was created
    """
    task_type: str


@dataclass(frozen=True)
class PollStarted(TaskRunnerEvent):
    """
    Event published when task polling begins.

    Attributes:
        task_type: The task definition name being polled
        worker_id: Identifier of the worker polling for tasks
        poll_count: Number of tasks requested in this poll
        timestamp: UTC timestamp when the event was created (inherited)
    """
    worker_id: str
    poll_count: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PollCompleted(TaskRunnerEvent):
    """
    Event published when task polling completes successfully.

    Attributes:
        task_type: The task definition name that was polled
        duration_ms: Time taken for the poll operation in milliseconds
        tasks_received: Number of tasks received from the poll
        timestamp: UTC timestamp when the event was created (inherited)
    """
    duration_ms: float
    tasks_received: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PollFailure(TaskRunnerEvent):
    """
    Event published when task polling fails.

    Attributes:
        task_type: The task definition name that was being polled
        duration_ms: Time taken before the poll failed in milliseconds
        cause: The exception that caused the failure
        timestamp: UTC timestamp when the event was created (inherited)
    """
    duration_ms: float
    cause: Exception
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TaskExecutionStarted(TaskRunnerEvent):
    """
    Event published when task execution begins.

    Attributes:
        task_type: The task definition name
        task_id: Unique identifier of the task instance
        worker_id: Identifier of the worker executing the task
        workflow_instance_id: ID of the workflow instance this task belongs to
        timestamp: UTC timestamp when the event was created (inherited)
    """
    task_id: str
    worker_id: str
    workflow_instance_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TaskExecutionCompleted(TaskRunnerEvent):
    """
    Event published when task execution completes successfully.

    Attributes:
        task_type: The task definition name
        task_id: Unique identifier of the task instance
        worker_id: Identifier of the worker that executed the task
        workflow_instance_id: ID of the workflow instance this task belongs to
        duration_ms: Time taken for task execution in milliseconds
        output_size_bytes: Size of the task output in bytes (if available)
        timestamp: UTC timestamp when the event was created (inherited)
    """
    task_id: str
    worker_id: str
    workflow_instance_id: Optional[str]
    duration_ms: float
    output_size_bytes: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TaskExecutionFailure(TaskRunnerEvent):
    """
    Event published when task execution fails.

    Attributes:
        task_type: The task definition name
        task_id: Unique identifier of the task instance
        worker_id: Identifier of the worker that attempted execution
        workflow_instance_id: ID of the workflow instance this task belongs to
        cause: The exception that caused the failure
        duration_ms: Time taken before failure in milliseconds
        timestamp: UTC timestamp when the event was created (inherited)
    """
    task_id: str
    worker_id: str
    workflow_instance_id: Optional[str]
    cause: Exception
    duration_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TaskUpdateFailure(TaskRunnerEvent):
    """
    Event published when task update fails after all retry attempts.

    This is a critical event indicating that the worker successfully executed a task
    but failed to communicate the result back to Conductor after multiple retries.

    The task result is lost from Conductor's perspective, and external intervention
    may be required to reconcile the state.

    Attributes:
        task_type: The task definition name
        task_id: Unique identifier of the task instance
        worker_id: Identifier of the worker that executed the task
        workflow_instance_id: ID of the workflow instance this task belongs to
        cause: The exception that caused the final update failure
        retry_count: Number of retry attempts made (typically 4)
        task_result: The TaskResult object that failed to update (for recovery/logging)
        timestamp: UTC timestamp when the event was created (inherited)

    Use Cases:
        - Alert operations team of critical update failures
        - Log failed task results to external storage for recovery
        - Implement custom retry logic with different backoff strategies
        - Track update reliability metrics
        - Trigger incident response workflows
    """
    task_id: str
    worker_id: str
    workflow_instance_id: Optional[str]
    cause: Exception
    retry_count: int
    task_result: 'TaskResult'  # Forward reference to avoid circular import
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
