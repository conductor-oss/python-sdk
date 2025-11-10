"""
Conductor event system for observability and metrics collection.

This module provides an event-driven architecture for monitoring task execution,
workflow operations, and other Conductor operations.
"""

from conductor.client.event.conductor_event import ConductorEvent
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
from conductor.client.event.event_dispatcher import EventDispatcher
from conductor.client.event.listeners import (
    TaskRunnerEventsListener,
    WorkflowEventsListener,
    TaskEventsListener,
    MetricsCollector as MetricsCollectorProtocol,
)
from conductor.client.event.listener_register import (
    register_task_runner_listener,
    register_workflow_listener,
    register_task_listener,
)

__all__ = [
    # Core event infrastructure
    'ConductorEvent',
    'EventDispatcher',

    # Task runner events
    'TaskRunnerEvent',
    'PollStarted',
    'PollCompleted',
    'PollFailure',
    'TaskExecutionStarted',
    'TaskExecutionCompleted',
    'TaskExecutionFailure',

    # Workflow events
    'WorkflowEvent',
    'WorkflowStarted',
    'WorkflowInputPayloadSize',
    'WorkflowPayloadUsed',

    # Task events
    'TaskEvent',
    'TaskResultPayloadSize',
    'TaskPayloadUsed',

    # Listener protocols
    'TaskRunnerEventsListener',
    'WorkflowEventsListener',
    'TaskEventsListener',
    'MetricsCollectorProtocol',

    # Registration utilities
    'register_task_runner_listener',
    'register_workflow_listener',
    'register_task_listener',
]
