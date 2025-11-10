"""
Listener protocols for Conductor events.

These protocols define the interfaces for event listeners, matching the
Java SDK's listener interfaces. Using Protocol allows for duck typing
while providing type hints and IDE support.
"""

from typing import Protocol, runtime_checkable

from conductor.client.event.task_runner_events import (
    PollStarted,
    PollCompleted,
    PollFailure,
    TaskExecutionStarted,
    TaskExecutionCompleted,
    TaskExecutionFailure,
)
from conductor.client.event.workflow_events import (
    WorkflowStarted,
    WorkflowInputPayloadSize,
    WorkflowPayloadUsed,
)
from conductor.client.event.task_events import (
    TaskResultPayloadSize,
    TaskPayloadUsed,
)


@runtime_checkable
class TaskRunnerEventsListener(Protocol):
    """
    Protocol for listening to task runner lifecycle events.

    Implementing classes should provide handlers for task polling and execution events.
    All methods are optional - implement only the events you need to handle.

    Example:
        >>> class MyListener:
        ...     def on_poll_started(self, event: PollStarted) -> None:
        ...         print(f"Polling {event.task_type}")
        ...
        ...     def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        ...         print(f"Task {event.task_id} completed in {event.duration_ms}ms")
    """

    def on_poll_started(self, event: PollStarted) -> None:
        """Handle poll started event."""
        ...

    def on_poll_completed(self, event: PollCompleted) -> None:
        """Handle poll completed event."""
        ...

    def on_poll_failure(self, event: PollFailure) -> None:
        """Handle poll failure event."""
        ...

    def on_task_execution_started(self, event: TaskExecutionStarted) -> None:
        """Handle task execution started event."""
        ...

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        """Handle task execution completed event."""
        ...

    def on_task_execution_failure(self, event: TaskExecutionFailure) -> None:
        """Handle task execution failure event."""
        ...


@runtime_checkable
class WorkflowEventsListener(Protocol):
    """
    Protocol for listening to workflow client events.

    Implementing classes should provide handlers for workflow operations.
    All methods are optional - implement only the events you need to handle.

    Example:
        >>> class WorkflowMonitor:
        ...     def on_workflow_started(self, event: WorkflowStarted) -> None:
        ...         if event.success:
        ...             print(f"Workflow {event.name} started: {event.workflow_id}")
    """

    def on_workflow_started(self, event: WorkflowStarted) -> None:
        """Handle workflow started event."""
        ...

    def on_workflow_input_payload_size(self, event: WorkflowInputPayloadSize) -> None:
        """Handle workflow input payload size event."""
        ...

    def on_workflow_payload_used(self, event: WorkflowPayloadUsed) -> None:
        """Handle workflow external payload usage event."""
        ...


@runtime_checkable
class TaskEventsListener(Protocol):
    """
    Protocol for listening to task client events.

    Implementing classes should provide handlers for task payload operations.
    All methods are optional - implement only the events you need to handle.

    Example:
        >>> class TaskPayloadMonitor:
        ...     def on_task_result_payload_size(self, event: TaskResultPayloadSize) -> None:
        ...         if event.size_bytes > 1_000_000:
        ...             print(f"Large task result: {event.size_bytes} bytes")
    """

    def on_task_result_payload_size(self, event: TaskResultPayloadSize) -> None:
        """Handle task result payload size event."""
        ...

    def on_task_payload_used(self, event: TaskPayloadUsed) -> None:
        """Handle task external payload usage event."""
        ...


@runtime_checkable
class MetricsCollector(
    TaskRunnerEventsListener,
    WorkflowEventsListener,
    TaskEventsListener,
    Protocol
):
    """
    Combined protocol for comprehensive metrics collection.

    This protocol combines all event listener protocols, matching the Java SDK's
    MetricsCollector interface. It provides a single interface for collecting
    metrics across all Conductor operations.

    This is a marker protocol - implementing classes inherit all methods from
    the parent protocols.

    Example:
        >>> class PrometheusMetrics:
        ...     def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        ...         self.task_duration.labels(event.task_type).observe(event.duration_ms / 1000)
        ...
        ...     def on_workflow_started(self, event: WorkflowStarted) -> None:
        ...         self.workflow_starts.labels(event.name).inc()
        ...
        ...     # ... implement other methods as needed
    """
    pass
