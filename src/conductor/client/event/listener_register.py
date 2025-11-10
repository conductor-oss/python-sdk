"""
Utility for bulk registration of event listeners.

This module provides convenience functions for registering listeners with
event dispatchers, matching the Java SDK's ListenerRegister utility.
"""

from conductor.client.event.event_dispatcher import EventDispatcher
from conductor.client.event.listeners import (
    TaskRunnerEventsListener,
    WorkflowEventsListener,
    TaskEventsListener,
)
from conductor.client.event.task_runner_events import (
    TaskRunnerEvent,
    PollStarted,
    PollCompleted,
    PollFailure,
    TaskExecutionStarted,
    TaskExecutionCompleted,
    TaskExecutionFailure,
)
from conductor.client.event.workflow_events import (
    WorkflowEvent,
    WorkflowStarted,
    WorkflowInputPayloadSize,
    WorkflowPayloadUsed,
)
from conductor.client.event.task_events import (
    TaskEvent,
    TaskResultPayloadSize,
    TaskPayloadUsed,
)


async def register_task_runner_listener(
    listener: TaskRunnerEventsListener,
    dispatcher: EventDispatcher[TaskRunnerEvent]
) -> None:
    """
    Register all TaskRunnerEventsListener methods with a dispatcher.

    This convenience function registers all event handler methods from a
    TaskRunnerEventsListener with the provided dispatcher.

    Args:
        listener: The listener implementing TaskRunnerEventsListener protocol
        dispatcher: The event dispatcher to register with

    Example:
        >>> prometheus = PrometheusMetricsCollector()
        >>> dispatcher = EventDispatcher[TaskRunnerEvent]()
        >>> await register_task_runner_listener(prometheus, dispatcher)
    """
    if hasattr(listener, 'on_poll_started'):
        await dispatcher.register(PollStarted, listener.on_poll_started)
    if hasattr(listener, 'on_poll_completed'):
        await dispatcher.register(PollCompleted, listener.on_poll_completed)
    if hasattr(listener, 'on_poll_failure'):
        await dispatcher.register(PollFailure, listener.on_poll_failure)
    if hasattr(listener, 'on_task_execution_started'):
        await dispatcher.register(TaskExecutionStarted, listener.on_task_execution_started)
    if hasattr(listener, 'on_task_execution_completed'):
        await dispatcher.register(TaskExecutionCompleted, listener.on_task_execution_completed)
    if hasattr(listener, 'on_task_execution_failure'):
        await dispatcher.register(TaskExecutionFailure, listener.on_task_execution_failure)


async def register_workflow_listener(
    listener: WorkflowEventsListener,
    dispatcher: EventDispatcher[WorkflowEvent]
) -> None:
    """
    Register all WorkflowEventsListener methods with a dispatcher.

    This convenience function registers all event handler methods from a
    WorkflowEventsListener with the provided dispatcher.

    Args:
        listener: The listener implementing WorkflowEventsListener protocol
        dispatcher: The event dispatcher to register with

    Example:
        >>> monitor = WorkflowMonitor()
        >>> dispatcher = EventDispatcher[WorkflowEvent]()
        >>> await register_workflow_listener(monitor, dispatcher)
    """
    if hasattr(listener, 'on_workflow_started'):
        await dispatcher.register(WorkflowStarted, listener.on_workflow_started)
    if hasattr(listener, 'on_workflow_input_payload_size'):
        await dispatcher.register(WorkflowInputPayloadSize, listener.on_workflow_input_payload_size)
    if hasattr(listener, 'on_workflow_payload_used'):
        await dispatcher.register(WorkflowPayloadUsed, listener.on_workflow_payload_used)


async def register_task_listener(
    listener: TaskEventsListener,
    dispatcher: EventDispatcher[TaskEvent]
) -> None:
    """
    Register all TaskEventsListener methods with a dispatcher.

    This convenience function registers all event handler methods from a
    TaskEventsListener with the provided dispatcher.

    Args:
        listener: The listener implementing TaskEventsListener protocol
        dispatcher: The event dispatcher to register with

    Example:
        >>> monitor = TaskPayloadMonitor()
        >>> dispatcher = EventDispatcher[TaskEvent]()
        >>> await register_task_listener(monitor, dispatcher)
    """
    if hasattr(listener, 'on_task_result_payload_size'):
        await dispatcher.register(TaskResultPayloadSize, listener.on_task_result_payload_size)
    if hasattr(listener, 'on_task_payload_used'):
        await dispatcher.register(TaskPayloadUsed, listener.on_task_payload_used)
