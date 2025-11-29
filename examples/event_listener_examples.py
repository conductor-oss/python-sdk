"""
Reusable event listener examples for TaskRunnerEventsListener.

This module provides example event listener implementations that can be used
in any application to monitor and track task execution.

Available Listeners:
- TaskExecutionLogger: Simple logging of all task lifecycle events
- TaskTimingTracker: Statistical tracking of task execution times
- DistributedTracingListener: Simulated distributed tracing integration

Usage:
    from examples.event_listener_examples import TaskExecutionLogger, TaskTimingTracker

    with TaskHandler(
        configuration=config,
        event_listeners=[
            TaskExecutionLogger(),
            TaskTimingTracker()
        ]
    ) as handler:
        handler.start_processes()
        handler.join_processes()
"""

import logging
from datetime import datetime

from conductor.client.event.task_runner_events import (
    TaskExecutionStarted,
    TaskExecutionCompleted,
    TaskExecutionFailure,
    PollStarted,
    PollCompleted,
    PollFailure
)

logger = logging.getLogger(__name__)


class TaskExecutionLogger:
    """
    Simple listener that logs all task execution events.

    Demonstrates basic pre/post processing:
    - on_task_execution_started: Pre-processing before task executes
    - on_task_execution_completed: Post-processing after successful execution
    - on_task_execution_failure: Error handling after failed execution
    """

    def on_task_execution_started(self, event: TaskExecutionStarted) -> None:
        """
        Called before task execution begins (pre-processing).

        Use this for:
        - Setting up context (tracing, logging context)
        - Validating preconditions
        - Starting timers
        - Recording audit events
        """
        logger.info(
            f"[PRE] Starting task '{event.task_type}' "
            f"(task_id={event.task_id}, worker={event.worker_id})"
        )

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        """
        Called after task execution completes successfully (post-processing).

        Use this for:
        - Logging results
        - Sending notifications
        - Updating external systems
        - Recording metrics
        """
        logger.info(
            f"[POST] Completed task '{event.task_type}' "
            f"(task_id={event.task_id}, duration={event.duration_ms:.2f}ms, "
            f"output_size={event.output_size_bytes} bytes)"
        )

    def on_task_execution_failure(self, event: TaskExecutionFailure) -> None:
        """
        Called when task execution fails (error handling).

        Use this for:
        - Error logging
        - Alerting
        - Retry logic
        - Cleanup operations
        """
        logger.error(
            f"[ERROR] Failed task '{event.task_type}' "
            f"(task_id={event.task_id}, duration={event.duration_ms:.2f}ms, "
            f"error={event.cause})"
        )

    def on_poll_started(self, event: PollStarted) -> None:
        """Called when polling for tasks begins."""
        logger.debug(f"Polling for {event.poll_count} '{event.task_type}' tasks")

    def on_poll_completed(self, event: PollCompleted) -> None:
        """Called when polling completes successfully."""
        if event.tasks_received > 0:
            logger.debug(
                f"Received {event.tasks_received} '{event.task_type}' tasks "
                f"in {event.duration_ms:.2f}ms"
            )

    def on_poll_failure(self, event: PollFailure) -> None:
        """Called when polling fails."""
        logger.warning(f"Poll failed for '{event.task_type}': {event.cause}")


class TaskTimingTracker:
    """
    Advanced listener that tracks task execution times and provides statistics.

    Demonstrates:
    - Stateful event processing
    - Aggregating data across multiple events
    - Custom business logic in listeners
    """

    def __init__(self):
        self.task_times = {}  # task_type -> list of durations
        self.task_errors = {}  # task_type -> error count

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        """Track successful task execution times."""
        if event.task_type not in self.task_times:
            self.task_times[event.task_type] = []

        self.task_times[event.task_type].append(event.duration_ms)

        # Print stats every 10 completions
        count = len(self.task_times[event.task_type])
        if count % 10 == 0:
            durations = self.task_times[event.task_type]
            avg = sum(durations) / len(durations)
            min_time = min(durations)
            max_time = max(durations)

            logger.info(
                f"Stats for '{event.task_type}': "
                f"count={count}, avg={avg:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms"
            )

    def on_task_execution_failure(self, event: TaskExecutionFailure) -> None:
        """Track task failures."""
        self.task_errors[event.task_type] = self.task_errors.get(event.task_type, 0) + 1
        logger.warning(
            f"Task '{event.task_type}' has failed {self.task_errors[event.task_type]} times"
        )


class DistributedTracingListener:
    """
    Example listener for distributed tracing integration.

    Demonstrates how to:
    - Generate trace IDs
    - Propagate trace context
    - Create spans for task execution
    """

    def __init__(self):
        self.active_traces = {}  # task_id -> trace_info

    def on_task_execution_started(self, event: TaskExecutionStarted) -> None:
        """Start a trace span when task execution begins."""
        trace_id = f"trace-{event.task_id[:8]}"
        span_id = f"span-{event.task_id[:8]}"

        self.active_traces[event.task_id] = {
            'trace_id': trace_id,
            'span_id': span_id,
            'start_time': datetime.utcnow(),
            'task_type': event.task_type
        }

        logger.info(
            f"[TRACE] Started span: trace_id={trace_id}, span_id={span_id}, "
            f"task_type={event.task_type}"
        )

    def on_task_execution_completed(self, event: TaskExecutionCompleted) -> None:
        """End the trace span when task execution completes."""
        if event.task_id in self.active_traces:
            trace_info = self.active_traces.pop(event.task_id)
            duration = (datetime.utcnow() - trace_info['start_time']).total_seconds() * 1000

            logger.info(
                f"[TRACE] Completed span: trace_id={trace_info['trace_id']}, "
                f"span_id={trace_info['span_id']}, duration={duration:.2f}ms, status=SUCCESS"
            )

    def on_task_execution_failure(self, event: TaskExecutionFailure) -> None:
        """Mark the trace span as failed."""
        if event.task_id in self.active_traces:
            trace_info = self.active_traces.pop(event.task_id)
            duration = (datetime.utcnow() - trace_info['start_time']).total_seconds() * 1000

            logger.info(
                f"[TRACE] Failed span: trace_id={trace_info['trace_id']}, "
                f"span_id={trace_info['span_id']}, duration={duration:.2f}ms, "
                f"status=ERROR, error={event.cause}"
            )
