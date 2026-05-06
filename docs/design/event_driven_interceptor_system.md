# Event-Driven Interceptor System - Design Document

> Historical design note: this document describes the event-driven interceptor
> design and includes some pre-harmonization metrics examples. The current
> Python SDK metrics setup, complete legacy and canonical catalogs,
> `WORKER_CANONICAL_METRICS` behavior, and migration guidance are maintained in
> [`../../METRICS.md`](../../METRICS.md).

## Table of Contents
- [Overview](#overview)
- [Current State Analysis](#current-state-analysis)
- [Proposed Architecture](#proposed-architecture)
- [Core Components](#core-components)
- [Event Hierarchy](#event-hierarchy)
- [Metrics Collection Flow](#metrics-collection-flow)
- [Migration Strategy](#migration-strategy)
- [Implementation Plan](#implementation-plan)
- [Examples](#examples)
- [Performance Considerations](#performance-considerations)
- [Open Questions](#open-questions)

---

## Overview

### Problem Statement

The current Python SDK metrics collection system has several limitations:

1. **Tight Coupling**: Metrics collection is tightly coupled to task runner code
2. **Single Backend**: Only supports file-based Prometheus metrics
3. **No Extensibility**: Can't add custom metrics logic without modifying SDK
4. **Synchronous**: Metrics calls could potentially block worker execution
5. **Limited Context**: Only basic metrics, no access to full event data
6. **No Flexibility**: Can't filter events or listen selectively

### Goals

Design and implement an event-driven interceptor system that:

1. ✅ **Decouples** observability from business logic
2. ✅ **Enables** multiple metrics backends simultaneously
3. ✅ **Provides** async, non-blocking event publishing
4. ✅ **Allows** custom event listeners and filtering
5. ✅ **Maintains** backward compatibility with existing metrics
6. ✅ **Matches** Java SDK capabilities for feature parity
7. ✅ **Enables** advanced use cases (SLA monitoring, audit logs, cost tracking)

### Non-Goals

- ❌ Built-in implementations for all metrics backends (only Prometheus reference implementation)
- ❌ Distributed tracing (OpenTelemetry integration is separate concern)
- ❌ Real-time streaming infrastructure (users provide their own)
- ❌ Built-in dashboards or visualization

---

## Current State Analysis

### Existing Metrics System

The original design coupled task runner code directly to a metrics collector.
The current implementation now routes metrics through telemetry collector
classes and worker/client events. See [`../../METRICS.md`](../../METRICS.md) for
current setup and metric names.

### Problems with Current Approach

| Issue | Impact | Severity |
|-------|--------|----------|
| Direct coupling | Hard to extend | High |
| Single backend | Can't use multiple backends | High |
| Synchronous calls | Could block execution | Medium |
| Limited data | Can't access full context | Medium |
| No filtering | All-or-nothing | Low |

### Current Metrics Reference

The current Prometheus metric names, labels, and legacy/canonical mode behavior
are maintained in [`../../METRICS.md`](../../METRICS.md).

---

## Proposed Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Task Execution Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │TaskRunnerAsync│ │WorkflowClient│  │  TaskClient  │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │ publish()       │ publish()       │ publish()         │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          └─────────────────▼─────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                  Event Dispatch Layer                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         EventDispatcher[T] (Generic)                     │ │
│  │  • Async event publishing (asyncio.create_task)          │ │
│  │  • Type-safe event routing (Protocol/ABC)                │ │
│  │  • Multiple listener support (CopyOnWriteList)           │ │
│  │  • Event filtering by type                               │ │
│  └─────────────────────┬────────────────────────────────────┘ │
│                        │ dispatch_async()                     │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         │                         
┌────────────────────────▼─────────────────────────────────────┐
│                 Listener/Consumer Layer                      │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │PrometheusMetrics│ │DatadogMetrics  │  │CustomListener   │ │
│  │   Collector     │ │   Collector    │  │  (SLA Monitor)  │ │
│  └────────────────┘  └────────────────┘  └─────────────────┘ │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │  Audit Logger  │  │  Cost Tracker  │  │ Dashboard Feed  │ │
│  │  (Compliance)  │  │  (FinOps)      │  │  (WebSocket)    │ │
│  └────────────────┘  └────────────────┘  └─────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Observer Pattern**: Core pattern for event publishing/consumption
2. **Async by Default**: All event publishing is non-blocking
3. **Type Safety**: Use `typing.Protocol` and `dataclasses` for type safety
4. **Thread Safety**: Use `asyncio`-safe primitives for AsyncIO mode
5. **Backward Compatible**: Existing metrics API continues to work
6. **Pythonic**: Leverage Python's duck typing and async/await

---

## Core Components

### 1. Event Base Class

**Location**: `src/conductor/client/events/conductor_event.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class ConductorEvent:
    """
    Base class for all Conductor events.

    Attributes:
        timestamp: When the event occurred (UTC)
    """
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.utcnow())
```

**Why `frozen=True`?**
- Immutable events prevent race conditions
- Safe to pass between async tasks
- Clear that events are snapshots, not mutable state

### 2. EventDispatcher (Generic)

**Location**: `src/conductor/client/events/event_dispatcher.py`

```python
from typing import TypeVar, Generic, Callable, Dict, List, Type, Optional
import asyncio
import logging
from collections import defaultdict
from copy import copy

T = TypeVar('T', bound='ConductorEvent')

logger = logging.getLogger(__name__)


class EventDispatcher(Generic[T]):
    """
    Thread-safe, async event dispatcher with type-safe event routing.

    Features:
    - Generic type parameter for type safety
    - Async event publishing (non-blocking)
    - Multiple listeners per event type
    - Listener registration/unregistration
    - Error isolation (listener failures don't affect task execution)

    Example:
        dispatcher = EventDispatcher[TaskRunnerEvent]()

        # Register listener
        dispatcher.register(
            TaskExecutionCompleted,
            lambda event: print(f"Task {event.task_id} completed")
        )

        # Publish event (async, non-blocking)
        dispatcher.publish(TaskExecutionCompleted(...))
    """

    def __init__(self):
        # Map event type to list of listeners
        # Using lists because we need to maintain registration order
        self._listeners: Dict[Type[T], List[Callable[[T], None]]] = defaultdict(list)

        # Lock for thread-safe registration/unregistration
        self._lock = asyncio.Lock()

    async def register(
        self,
        event_type: Type[T],
        listener: Callable[[T], None]
    ) -> None:
        """
        Register a listener for a specific event type.

        Args:
            event_type: The event class to listen for
            listener: Callback function (sync or async)
        """
        async with self._lock:
            if listener not in self._listeners[event_type]:
                self._listeners[event_type].append(listener)
                logger.debug(
                    f"Registered listener for {event_type.__name__}: {listener}"
                )

    def register_sync(
        self,
        event_type: Type[T],
        listener: Callable[[T], None]
    ) -> None:
        """
        Synchronous version of register() for non-async contexts.
        """
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self.register(event_type, listener))

    async def unregister(
        self,
        event_type: Type[T],
        listener: Callable[[T], None]
    ) -> None:
        """
        Unregister a listener.

        Args:
            event_type: The event class
            listener: The callback to remove
        """
        async with self._lock:
            if listener in self._listeners[event_type]:
                self._listeners[event_type].remove(listener)
                logger.debug(
                    f"Unregistered listener for {event_type.__name__}"
                )

    def publish(self, event: T) -> None:
        """
        Publish an event to all registered listeners (async, non-blocking).

        Args:
            event: The event instance to publish

        Note:
            This method returns immediately. Event processing happens
            asynchronously in background tasks.
        """
        # Get listeners for this specific event type
        listeners = copy(self._listeners.get(type(event), []))

        if not listeners:
            return

        # Publish asynchronously (don't block caller)
        asyncio.create_task(
            self._dispatch_to_listeners(event, listeners)
        )

    async def _dispatch_to_listeners(
        self,
        event: T,
        listeners: List[Callable[[T], None]]
    ) -> None:
        """
        Dispatch event to all listeners (internal method).

        Error Isolation: If a listener fails, it doesn't affect:
        - Other listeners
        - Task execution
        - The event dispatch system
        """
        for listener in listeners:
            try:
                # Check if listener is async or sync
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    # Run sync listener in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, listener, event)

            except Exception as e:
                # Log but don't propagate - listener failures are isolated
                logger.error(
                    f"Error in event listener for {type(event).__name__}: {e}",
                    exc_info=True
                )

    def clear(self) -> None:
        """Clear all registered listeners (useful for testing)."""
        self._listeners.clear()
```

**Key Design Decisions:**

1. **Generic Type Parameter**: `EventDispatcher[T]` provides type hints
2. **Async Publishing**: Uses `asyncio.create_task()` for non-blocking dispatch
3. **Error Isolation**: Listener exceptions are caught and logged
4. **Thread Safety**: Uses `asyncio.Lock()` for registration/unregistration
5. **Executor for Sync Listeners**: Sync callbacks run in executor to avoid blocking

### 3. Listener Protocols

**Location**: `src/conductor/client/events/listeners.py`

```python
from typing import Protocol, runtime_checkable
from conductor.client.events.task_runner_events import *
from conductor.client.events.workflow_events import *
from conductor.client.events.task_client_events import *


@runtime_checkable
class TaskRunnerEventsListener(Protocol):
    """
    Protocol for task runner event listeners.

    Implement this protocol to receive task execution lifecycle events.
    All methods are optional - implement only what you need.
    """

    def on_poll_started(self, event: 'PollStarted') -> None:
        """Called when polling starts for a task type."""
        ...

    def on_poll_completed(self, event: 'PollCompleted') -> None:
        """Called when polling completes successfully."""
        ...

    def on_poll_failure(self, event: 'PollFailure') -> None:
        """Called when polling fails."""
        ...

    def on_task_execution_started(self, event: 'TaskExecutionStarted') -> None:
        """Called when task execution begins."""
        ...

    def on_task_execution_completed(self, event: 'TaskExecutionCompleted') -> None:
        """Called when task execution completes successfully."""
        ...

    def on_task_execution_failure(self, event: 'TaskExecutionFailure') -> None:
        """Called when task execution fails."""
        ...


@runtime_checkable
class WorkflowEventsListener(Protocol):
    """
    Protocol for workflow client event listeners.
    """

    def on_workflow_started(self, event: 'WorkflowStarted') -> None:
        """Called when workflow starts (success or failure)."""
        ...

    def on_workflow_input_size(self, event: 'WorkflowInputSize') -> None:
        """Called when workflow input size is measured."""
        ...

    def on_workflow_payload_used(self, event: 'WorkflowPayloadUsed') -> None:
        """Called when external payload storage is used."""
        ...


@runtime_checkable
class TaskClientEventsListener(Protocol):
    """
    Protocol for task client event listeners.
    """

    def on_task_payload_used(self, event: 'TaskPayloadUsed') -> None:
        """Called when external payload storage is used for tasks."""
        ...

    def on_task_result_size(self, event: 'TaskResultSize') -> None:
        """Called when task result size is measured."""
        ...


class MetricsCollector(
    TaskRunnerEventsListener,
    WorkflowEventsListener,
    TaskClientEventsListener,
    Protocol
):
    """
    Unified protocol combining all listener interfaces.

    This is the primary interface for comprehensive metrics collection.
    Implement this to receive all Conductor events.
    """
    pass
```

**Why `Protocol` instead of `ABC`?**
- Duck typing: Users can implement any subset of methods
- No need to inherit from base class
- More Pythonic and flexible
- `@runtime_checkable` allows `isinstance()` checks

### 4. ListenerRegistry

**Location**: `src/conductor/client/events/listener_registry.py`

```python
"""
Utility for bulk registration of listener protocols with event dispatchers.
"""

from typing import Any
from conductor.client.events.event_dispatcher import EventDispatcher
from conductor.client.events.listeners import (
    TaskRunnerEventsListener,
    WorkflowEventsListener,
    TaskClientEventsListener
)
from conductor.client.events.task_runner_events import *
from conductor.client.events.workflow_events import *
from conductor.client.events.task_client_events import *


class ListenerRegistry:
    """
    Helper class for registering protocol-based listeners with dispatchers.

    Automatically inspects listener objects and registers all implemented
    event handler methods.
    """

    @staticmethod
    def register_task_runner_listener(
        listener: Any,
        dispatcher: EventDispatcher
    ) -> None:
        """
        Register all task runner event handlers from a listener.

        Args:
            listener: Object implementing TaskRunnerEventsListener methods
            dispatcher: EventDispatcher for TaskRunnerEvent
        """
        # Check which methods are implemented and register them
        if hasattr(listener, 'on_poll_started'):
            dispatcher.register_sync(PollStarted, listener.on_poll_started)

        if hasattr(listener, 'on_poll_completed'):
            dispatcher.register_sync(PollCompleted, listener.on_poll_completed)

        if hasattr(listener, 'on_poll_failure'):
            dispatcher.register_sync(PollFailure, listener.on_poll_failure)

        if hasattr(listener, 'on_task_execution_started'):
            dispatcher.register_sync(
                TaskExecutionStarted,
                listener.on_task_execution_started
            )

        if hasattr(listener, 'on_task_execution_completed'):
            dispatcher.register_sync(
                TaskExecutionCompleted,
                listener.on_task_execution_completed
            )

        if hasattr(listener, 'on_task_execution_failure'):
            dispatcher.register_sync(
                TaskExecutionFailure,
                listener.on_task_execution_failure
            )

    @staticmethod
    def register_workflow_listener(
        listener: Any,
        dispatcher: EventDispatcher
    ) -> None:
        """Register all workflow event handlers from a listener."""
        if hasattr(listener, 'on_workflow_started'):
            dispatcher.register_sync(WorkflowStarted, listener.on_workflow_started)

        if hasattr(listener, 'on_workflow_input_size'):
            dispatcher.register_sync(WorkflowInputSize, listener.on_workflow_input_size)

        if hasattr(listener, 'on_workflow_payload_used'):
            dispatcher.register_sync(
                WorkflowPayloadUsed,
                listener.on_workflow_payload_used
            )

    @staticmethod
    def register_task_client_listener(
        listener: Any,
        dispatcher: EventDispatcher
    ) -> None:
        """Register all task client event handlers from a listener."""
        if hasattr(listener, 'on_task_payload_used'):
            dispatcher.register_sync(TaskPayloadUsed, listener.on_task_payload_used)

        if hasattr(listener, 'on_task_result_size'):
            dispatcher.register_sync(TaskResultSize, listener.on_task_result_size)

    @staticmethod
    def register_metrics_collector(
        collector: Any,
        task_dispatcher: EventDispatcher,
        workflow_dispatcher: EventDispatcher,
        task_client_dispatcher: EventDispatcher
    ) -> None:
        """
        Register a MetricsCollector with all three dispatchers.

        This is a convenience method for comprehensive metrics collection.
        """
        ListenerRegistry.register_task_runner_listener(collector, task_dispatcher)
        ListenerRegistry.register_workflow_listener(collector, workflow_dispatcher)
        ListenerRegistry.register_task_client_listener(collector, task_client_dispatcher)
```

---

## Event Hierarchy

### Task Runner Events

**Location**: `src/conductor/client/events/task_runner_events.py`

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from conductor.client.events.conductor_event import ConductorEvent


@dataclass(frozen=True)
class TaskRunnerEvent(ConductorEvent):
    """Base class for all task runner events."""
    task_type: str


@dataclass(frozen=True)
class PollStarted(TaskRunnerEvent):
    """
    Published when polling starts for a task type.

    Use Case: Track polling frequency, detect polling issues
    """
    worker_id: str
    poll_count: int  # Batch size requested


@dataclass(frozen=True)
class PollCompleted(TaskRunnerEvent):
    """
    Published when polling completes successfully.

    Use Case: Track polling latency, measure server response time
    """
    worker_id: str
    duration_ms: float
    tasks_received: int


@dataclass(frozen=True)
class PollFailure(TaskRunnerEvent):
    """
    Published when polling fails.

    Use Case: Alert on polling issues, track error rates
    """
    worker_id: str
    duration_ms: float
    error_type: str
    error_message: str


@dataclass(frozen=True)
class TaskExecutionStarted(TaskRunnerEvent):
    """
    Published when task execution begins.

    Use Case: Track active task count, monitor worker utilization
    """
    task_id: str
    workflow_instance_id: str
    worker_id: str


@dataclass(frozen=True)
class TaskExecutionCompleted(TaskRunnerEvent):
    """
    Published when task execution completes successfully.

    Use Case: Track execution time, SLA monitoring, cost calculation
    """
    task_id: str
    workflow_instance_id: str
    worker_id: str
    duration_ms: float
    output_size_bytes: Optional[int] = None


@dataclass(frozen=True)
class TaskExecutionFailure(TaskRunnerEvent):
    """
    Published when task execution fails.

    Use Case: Alert on failures, error tracking, retry analysis
    """
    task_id: str
    workflow_instance_id: str
    worker_id: str
    duration_ms: float
    error_type: str
    error_message: str
    is_retryable: bool = True
```

### Workflow Events

**Location**: `src/conductor/client/events/workflow_events.py`

```python
from dataclasses import dataclass
from typing import Optional
from conductor.client.events.conductor_event import ConductorEvent


@dataclass(frozen=True)
class WorkflowEvent(ConductorEvent):
    """Base class for workflow-related events."""
    workflow_name: str
    workflow_version: Optional[int] = None


@dataclass(frozen=True)
class WorkflowStarted(WorkflowEvent):
    """
    Published when workflow start attempt completes.

    Use Case: Track workflow start success rate, monitor failures
    """
    workflow_id: Optional[str] = None
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class WorkflowInputSize(WorkflowEvent):
    """
    Published when workflow input size is measured.

    Use Case: Track payload sizes, identify large workflows
    """
    size_bytes: int


@dataclass(frozen=True)
class WorkflowPayloadUsed(WorkflowEvent):
    """
    Published when external payload storage is used.

    Use Case: Track external storage usage, cost analysis
    """
    operation: str  # "READ" or "WRITE"
    payload_type: str  # "WORKFLOW_INPUT", "WORKFLOW_OUTPUT"
```

### Task Client Events

**Location**: `src/conductor/client/events/task_client_events.py`

```python
from dataclasses import dataclass
from conductor.client.events.conductor_event import ConductorEvent


@dataclass(frozen=True)
class TaskClientEvent(ConductorEvent):
    """Base class for task client events."""
    task_type: str


@dataclass(frozen=True)
class TaskPayloadUsed(TaskClientEvent):
    """
    Published when external payload storage is used for task.

    Use Case: Track external storage usage
    """
    operation: str  # "READ" or "WRITE"
    payload_type: str  # "TASK_INPUT", "TASK_OUTPUT"


@dataclass(frozen=True)
class TaskResultSize(TaskClientEvent):
    """
    Published when task result size is measured.

    Use Case: Track task output sizes, identify large results
    """
    task_id: str
    size_bytes: int
```

---

## Metrics Collection Flow

### Earlier Direct Flow

```
TaskRunner.poll_tasks()
    └─> direct metrics collector call
        └─> Prometheus registry
```

**Problems:**
- Direct coupling
- Synchronous call
- Can't add custom logic without modifying SDK

### Event-Driven Flow

```
TaskRunner.poll_tasks()
    └─> event_dispatcher.publish(PollStarted(...))
        └─> asyncio.create_task(dispatch_to_listeners())
            ├─> Metrics listener
            ├─> DatadogCollector.on_poll_started()
            │   └─> datadog.increment('poll.started')
            └─> CustomListener.on_poll_started()
                └─> my_custom_logic()
```

**Benefits:**
- Decoupled
- Async/non-blocking
- Multiple backends
- Custom logic supported

### Integration with TaskRunnerAsyncIO

**Event publishing:**

```python
# NEW - Event publishing
self.event_dispatcher.publish(PollStarted(
    task_type=task_definition_name,
    worker_id=self.worker.get_identity(),
    poll_count=poll_count
))
```

### Current Metrics Implementation

The implemented SDK metrics collector is selected by `MetricsSettings` and, for
canonical mode, `WORKER_CANONICAL_METRICS`. It listens to worker and client
events through the current telemetry collector classes. See
[`../../METRICS.md`](../../METRICS.md) for current setup and metric names.

---

## Migration Strategy

### Phase 1: Foundation (Week 1)

**Goal**: Core event system without breaking existing code

**Tasks:**
1. Create event base classes and hierarchy
2. Implement EventDispatcher
3. Define listener protocols
4. Create ListenerRegistry
5. Unit tests for event system

**No Breaking Changes**: Existing metrics API continues to work

### Phase 2: Integration (Week 2)

**Goal**: Integrate event system into task runners

**Tasks:**
1. Add event_dispatcher to TaskRunnerAsyncIO
2. Add event_dispatcher to TaskRunner (multiprocessing)
3. Publish events for worker lifecycle changes
4. Register metrics collectors as event listeners
5. Integration tests

**Backward Compatible**: Existing metrics setup continues to work while event
publishing is introduced.

### Phase 3: Reference Implementation (Week 3)

**Goal**: New Prometheus collector using events

**Tasks:**
1. Implement the built-in metrics collector
2. Create example collectors (Datadog, CloudWatch)
3. Documentation and examples
4. Performance benchmarks

**Backward Compatible**: Users can select legacy or canonical metrics through
the documented metrics factory behavior.

### Phase 4: Deprecation (Future Release)

**Goal**: Deprecate pre-harmonization metric shapes when canonical metrics
become the default.

**Tasks:**
1. Announce canonical metrics as the default
2. Update examples to use documented metrics setup
3. Maintain migration guidance in `METRICS.md`

**Timeline**: 6 months deprecation period

### Phase 5: Removal (Future Major Version)

**Goal**: Remove legacy metric shapes in a future major version.

**Tasks:**
1. Remove legacy collector implementation
2. Keep `METRICS.md` aligned with the released surface
3. Update major version

**Timeline**: Next major version (2.0.0)

---

## Implementation Plan

### Week 1: Core Event System

**Day 1-2: Event Classes**
- [ ] Create `conductor_event.py` with base class
- [ ] Create `task_runner_events.py` with all event types
- [ ] Create `workflow_events.py`
- [ ] Create `task_client_events.py`
- [ ] Unit tests for event creation and immutability

**Day 3-4: EventDispatcher**
- [ ] Implement `EventDispatcher[T]` with async publishing
- [ ] Thread safety with asyncio.Lock
- [ ] Error isolation and logging
- [ ] Unit tests for registration/publishing

**Day 5: Listener Protocols**
- [ ] Define TaskRunnerEventsListener protocol
- [ ] Define WorkflowEventsListener protocol
- [ ] Define TaskClientEventsListener protocol
- [ ] Define unified MetricsCollector protocol
- [ ] Create ListenerRegistry utility

### Week 2: Integration

**Day 1-2: TaskRunnerAsyncIO Integration**
- [ ] Add event_dispatcher field
- [ ] Publish events in poll cycle
- [ ] Publish events in task execution
- [ ] Keep old metrics calls for compatibility

**Day 3: TaskRunner (Multiprocessing) Integration**
- [ ] Add event_dispatcher field
- [ ] Publish events (same as AsyncIO)
- [ ] Handle multiprocess event publishing

**Day 4: Compatibility**
- [ ] Verify existing metrics setup continues to work
- [ ] Tests for compatibility behavior

**Day 5: Integration Tests**
- [ ] End-to-end tests with events
- [ ] Verify both old and new APIs work
- [ ] Performance tests

### Week 3: Reference Implementation & Examples

**Day 1-2: Built-in Metrics Collector**
- [ ] Implement metrics collection using events
- [ ] HTTP server for metrics endpoint
- [ ] Tests

**Day 3: Example Collectors**
- [ ] Datadog example collector
- [ ] CloudWatch example collector
- [ ] Console logger example

**Day 4-5: Documentation**
- [ ] Architecture documentation
- [ ] Migration guide
- [ ] API reference
- [ ] Examples and tutorials

---

## Examples

### Example 1: Current Metrics Usage

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.settings.metrics_settings import MetricsSettings

config = Configuration()
metrics_settings = MetricsSettings(directory="/tmp/conductor-metrics", http_port=8000)

# Create task handler with metrics
with TaskHandler(
    configuration=config,
    metrics_settings=metrics_settings,
) as handler:
    handler.start_processes()
    handler.join_processes()
```

For the current Prometheus metrics catalog and canonical mode selection, see
[`../../METRICS.md`](../../METRICS.md).

### Example 2: Custom Event Listener

```python
from conductor.client.events.listeners import TaskRunnerEventsListener
from conductor.client.events.task_runner_events import *

class SlowTaskAlert(TaskRunnerEventsListener):
    """Alert when tasks exceed SLA."""

    def __init__(self, threshold_seconds: float):
        self.threshold_seconds = threshold_seconds

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        duration_seconds = event.duration_ms / 1000.0

        if duration_seconds > self.threshold_seconds:
            self.send_alert(
                title=f"Slow Task: {event.task_id}",
                message=f"Task {event.task_type} took {duration_seconds:.2f}s",
                severity="warning"
            )

    def send_alert(self, title: str, message: str, severity: str):
        # Send to PagerDuty, Slack, etc.
        print(f"[{severity.upper()}] {title}: {message}")

# Usage
handler = TaskHandler(
    configuration=config,
    event_listeners=[SlowTaskAlert(threshold_seconds=30.0)]
)
```

### Example 3: Selective Listening (Lambda)

```python
from conductor.client.events.event_dispatcher import EventDispatcher
from conductor.client.events.task_runner_events import TaskExecutionCompleted

# Create handler
handler = TaskHandler(configuration=config)

# Get dispatcher (exposed by handler)
dispatcher = handler.get_task_runner_event_dispatcher()

# Register inline listener
dispatcher.register_sync(
    TaskExecutionCompleted,
    lambda event: print(f"Task {event.task_id} completed in {event.duration_ms}ms")
)
```

### Example 4: Cost Tracking

```python
from decimal import Decimal
from conductor.client.events.listeners import TaskRunnerEventsListener
from conductor.client.events.task_runner_events import TaskExecutionCompleted

class CostTracker(TaskRunnerEventsListener):
    """Track compute costs per task."""

    def __init__(self, cost_per_second: dict[str, Decimal]):
        self.cost_per_second = cost_per_second
        self.total_cost = Decimal(0)

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        cost_rate = self.cost_per_second.get(event.task_type)
        if cost_rate:
            duration_seconds = Decimal(event.duration_ms) / 1000
            cost = cost_rate * duration_seconds
            self.total_cost += cost

            print(f"Task {event.task_id} cost: ${cost:.4f} "
                  f"(Total: ${self.total_cost:.2f})")

# Usage
cost_tracker = CostTracker({
    'expensive_ml_task': Decimal('0.05'),  # $0.05 per second
    'simple_task': Decimal('0.001')         # $0.001 per second
})

handler = TaskHandler(
    configuration=config,
    event_listeners=[cost_tracker]
)
```

---

## Performance Considerations

### Async Event Publishing

**Design Decision**: All events published via `asyncio.create_task()`

**Benefits:**
- ✅ Non-blocking: Task execution never waits for metrics
- ✅ Parallel processing: Listeners process events concurrently
- ✅ Error isolation: Listener failures don't affect tasks

**Trade-offs:**
- ⚠️ Event processing is not guaranteed to complete
- ⚠️ Need proper shutdown to flush pending events

**Mitigation**:
```python
# In TaskHandler.stop()
await asyncio.gather(*pending_tasks, return_exceptions=True)
```

### Memory Overhead

**Event Object Cost:**
- Each event: ~200-400 bytes (dataclass with 5-10 fields)
- Short-lived: Garbage collected immediately after dispatch
- No accumulation: Events don't stay in memory

**Listener Registration Cost:**
- List of callbacks: ~50 bytes per listener
- Dictionary overhead: ~200 bytes per event type
- Total: < 10 KB for typical setup

### CPU Overhead

**Benchmark Target:**
- Event creation: < 1 microsecond
- Event dispatch: < 5 microseconds
- Total overhead: < 0.1% of task execution time

**Measurement Plan:**
```python
import time

start = time.perf_counter()
event = TaskExecutionCompleted(...)
dispatcher.publish(event)
overhead = time.perf_counter() - start

assert overhead < 0.000005  # < 5 microseconds
```

### Thread Safety

**AsyncIO Mode:**
- Use `asyncio.Lock()` for registration
- Events published via `asyncio.create_task()`
- No threading issues

**Multiprocessing Mode:**
- Each process has own EventDispatcher
- No shared state between processes
- Events published per-process

---

## Open Questions

### 1. Should we support synchronous event listeners?

**Options:**
- **A**: Only async listeners (`async def on_event(...)`)
- **B**: Both sync and async (`def` runs in executor)

**Recommendation**: **B** - Support both for flexibility

### 2. Should events be serializable for multiprocessing?

**Options:**
- **A**: Events stay in-process (separate dispatchers per process)
- **B**: Serialize events and send to parent process

**Recommendation**: **A** - Keep it simple, each process publishes its own metrics

### 3. Should we provide HTTP endpoint for Prometheus scraping?

**Options:**
- **A**: Users implement their own HTTP server
- **B**: Provide built-in HTTP server like Java SDK

**Recommendation**: **B** - Provide convenience method:
```python
prometheus.start_http_server(port=9991, path='/metrics')
```

### 4. Should event timestamps be UTC or local time?

**Options:**
- **A**: UTC (recommended for distributed systems)
- **B**: Local time
- **C**: Configurable

**Recommendation**: **A** - Always UTC for consistency

### 5. Should we buffer events for batch processing?

**Options:**
- **A**: Publish immediately (current design)
- **B**: Buffer and flush periodically

**Recommendation**: **A** - Publish immediately, let listeners batch if needed

### 6. Backward compatibility timeline?

**Options:**
- **A**: Deprecate old API immediately
- **B**: Keep both APIs for 6 months
- **C**: Keep both APIs indefinitely

**Recommendation**: **B** - 6 month deprecation period

---

## Success Criteria

### Functional Requirements

✅ Event system works in both AsyncIO and multiprocessing modes
✅ Multiple listeners can be registered simultaneously
✅ Events are published asynchronously without blocking
✅ Listener failures are isolated (don't affect task execution)
✅ Backward compatible with existing metrics API
✅ Prometheus collector works with new event system

### Non-Functional Requirements

✅ Event publishing overhead < 5 microseconds
✅ Memory overhead < 10 KB for typical setup
✅ Zero impact on task execution latency
✅ Thread-safe for AsyncIO mode
✅ Process-safe for multiprocessing mode

### Documentation Requirements

✅ Architecture documentation (this document)
✅ Migration guide (old API → new API)
✅ API reference documentation
✅ 5+ example implementations
✅ Performance benchmarks

---

## Next Steps

1. **Review this design document** ✋ (YOU ARE HERE)
2. Get approval on architecture and approach
3. Create GitHub issue for tracking
4. Begin Week 1 implementation (Core Event System)
5. Weekly progress updates

---

## Appendix A: API Comparison

### Earlier Direct Metrics API

The earlier design coupled task runner code directly to metric recording calls.
Current user-facing metrics setup is documented in
[`../../METRICS.md`](../../METRICS.md).

### Event-Driven API

```python
# Event-driven, decoupled
self.event_dispatcher.publish(PollCompleted(
    task_type=task_type,
    worker_id=worker_id,
    duration_ms=duration,
    tasks_received=len(tasks)
))
```

---

## Appendix B: File Structure

```
src/conductor/client/
├── events/
│   ├── __init__.py
│   ├── conductor_event.py          # Base event class
│   ├── event_dispatcher.py         # Generic dispatcher
│   ├── listener_registry.py        # Bulk registration utility
│   ├── listeners.py                # Protocol definitions
│   ├── task_runner_events.py       # Task runner event types
│   ├── workflow_events.py          # Workflow event types
│   └── task_client_events.py       # Task client event types
│
├── telemetry/
│   ├── metrics_collector.py        # Compatibility shim
│   └── metrics_collector_base.py   # Shared collector infrastructure
│
└── automator/
    ├── task_handler_asyncio.py     # Modified to publish events
    └── task_runner_asyncio.py      # Modified to publish events
```

---

## Appendix C: Performance Benchmark Plan

```python
import time
import asyncio
from conductor.client.events.event_dispatcher import EventDispatcher
from conductor.client.events.task_runner_events import TaskExecutionCompleted

async def benchmark_event_publishing():
    dispatcher = EventDispatcher()

    # Register 10 listeners
    for i in range(10):
        dispatcher.register_sync(
            TaskExecutionCompleted,
            lambda e: None  # No-op listener
        )

    # Measure 10,000 events
    start = time.perf_counter()

    for i in range(10000):
        dispatcher.publish(TaskExecutionCompleted(
            task_type='test',
            task_id=f'task-{i}',
            workflow_instance_id='workflow-1',
            worker_id='worker-1',
            duration_ms=100.0
        ))

    # Wait for all events to process
    await asyncio.sleep(0.1)

    end = time.perf_counter()
    duration = end - start
    events_per_second = 10000 / duration
    microseconds_per_event = (duration / 10000) * 1_000_000

    print(f"Events per second: {events_per_second:,.0f}")
    print(f"Microseconds per event: {microseconds_per_event:.2f}")
    print(f"Total time: {duration:.3f}s")

    assert microseconds_per_event < 5.0, "Event overhead too high!"

asyncio.run(benchmark_event_publishing())
```

**Expected Results:**
- Events per second: > 200,000
- Microseconds per event: < 5.0
- Total time: < 0.05s

---

**Document Version**: 1.0
**Last Updated**: 2025-01-09
**Status**: DRAFT - AWAITING REVIEW
**Author**: Claude Code
**Reviewers**: TBD
