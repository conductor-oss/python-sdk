"""
Task Context for Conductor Workers

Provides access to the current task and task result during worker execution.
Similar to Java SDK's TaskContext but using Python's contextvars for proper
async/thread-safe context management.

Usage:
    from conductor.client.context.task_context import get_task_context

    @worker_task(task_definition_name='my_task')
    def my_worker(input_data: dict) -> dict:
        # Access current task context
        ctx = get_task_context()

        # Get task information
        task_id = ctx.get_task_id()
        workflow_id = ctx.get_workflow_instance_id()
        retry_count = ctx.get_retry_count()

        # Add logs
        ctx.add_log("Processing started")

        # Set callback after N seconds
        ctx.set_callback_after(60)

        return {"result": "done"}
"""

from __future__ import annotations
from contextvars import ContextVar
from typing import Optional, Union
from conductor.client.http.models import Task, TaskResult, TaskExecLog
from conductor.client.http.models.task_result_status import TaskResultStatus
import time


class TaskInProgress:
    """
    Represents a task that is still in progress and should be re-queued.

    This is NOT an error condition - it's a normal state for long-running tasks
    that need to be polled multiple times. Workers can return this to signal
    that work is ongoing and Conductor should callback after a specified delay.

    This approach uses Union types for clean, type-safe APIs:
        def worker(...) -> Union[dict, TaskInProgress]:
            if still_working():
                return TaskInProgress(callback_after=60, output={'progress': 50})
            return {'status': 'completed', 'result': 'success'}

    Advantages over exceptions:
    - Semantically correct (not an error condition)
    - Explicit in function signature
    - Better type checking and IDE support
    - More functional programming style
    - Easier to reason about control flow

    Usage:
        from conductor.client.context import TaskInProgress

        @worker_task(task_definition_name='long_task')
        def long_running_worker(job_id: str) -> Union[dict, TaskInProgress]:
            ctx = get_task_context()
            poll_count = ctx.get_poll_count()

            ctx.add_log(f"Processing job {job_id}")

            if poll_count < 3:
                # Still working - return TaskInProgress
                return TaskInProgress(
                    callback_after_seconds=60,
                    output={'status': 'processing', 'progress': poll_count * 33}
                )

            # Complete - return result
            return {'status': 'completed', 'job_id': job_id, 'result': 'success'}
    """

    def __init__(
        self,
        callback_after_seconds: int = 60,
        output: Optional[dict] = None
    ):
        """
        Initialize TaskInProgress.

        Args:
            callback_after_seconds: Seconds to wait before Conductor re-queues the task
            output: Optional intermediate output data to include in the result
        """
        self.callback_after_seconds = callback_after_seconds
        self.output = output or {}

    def __repr__(self) -> str:
        return f"TaskInProgress(callback_after={self.callback_after_seconds}s, output={self.output})"


# Context variable for storing TaskContext (thread-safe and async-safe)
_task_context_var: ContextVar[Optional['TaskContext']] = ContextVar('task_context', default=None)


class TaskContext:
    """
    Context object providing access to the current task and task result.

    This class should not be instantiated directly. Use get_task_context() instead.

    Attributes:
        task: The current Task being executed
        task_result: The TaskResult being built for this execution
    """

    def __init__(self, task: Task, task_result: TaskResult):
        """
        Initialize TaskContext.

        Args:
            task: The task being executed
            task_result: The task result being built
        """
        self._task = task
        self._task_result = task_result

    @property
    def task(self) -> Task:
        """Get the current task."""
        return self._task

    @property
    def task_result(self) -> TaskResult:
        """Get the current task result."""
        return self._task_result

    def get_task_id(self) -> str:
        """
        Get the task ID.

        Returns:
            Task ID string
        """
        return self._task.task_id

    def get_workflow_instance_id(self) -> str:
        """
        Get the workflow instance ID.

        Returns:
            Workflow instance ID string
        """
        return self._task.workflow_instance_id

    def get_retry_count(self) -> int:
        """
        Get the number of times this task has been retried.

        Returns:
            Retry count (0 for first attempt)
        """
        return getattr(self._task, 'retry_count', 0) or 0

    def get_poll_count(self) -> int:
        """
        Get the number of times this task has been polled.

        Returns:
            Poll count
        """
        return getattr(self._task, 'poll_count', 0) or 0

    def get_callback_after_seconds(self) -> int:
        """
        Get the callback delay in seconds.

        Returns:
            Callback delay in seconds (0 if not set)
        """
        return getattr(self._task_result, 'callback_after_seconds', 0) or 0

    def set_callback_after(self, seconds: int) -> None:
        """
        Set callback delay for this task.

        The task will be re-queued after the specified number of seconds.
        Useful for implementing polling or retry logic.

        Args:
            seconds: Number of seconds to wait before callback

        Example:
            # Poll external API every 60 seconds until ready
            ctx = get_task_context()

            if not is_ready():
                ctx.set_callback_after(60)
                ctx.set_output({'status': 'pending'})
                return {'status': 'IN_PROGRESS'}
        """
        self._task_result.callback_after_seconds = seconds

    def add_log(self, log_message: str) -> None:
        """
        Add a log message to the task result.

        These logs will be visible in the Conductor UI and stored with the task execution.

        Args:
            log_message: The log message to add

        Example:
            ctx = get_task_context()
            ctx.add_log("Started processing order")
            ctx.add_log(f"Processing item {i} of {total}")
        """
        if not hasattr(self._task_result, 'logs') or self._task_result.logs is None:
            self._task_result.logs = []

        log_entry = TaskExecLog(
            log=log_message,
            task_id=self._task.task_id,
            created_time=int(time.time() * 1000)  # Milliseconds
        )
        self._task_result.logs.append(log_entry)

    def set_output(self, output_data: dict) -> None:
        """
        Set the output data for this task result.

        This allows partial results to be set during execution.
        The final return value from the worker function will override this.

        Args:
            output_data: Dictionary of output data

        Example:
            ctx = get_task_context()
            ctx.set_output({'progress': 50, 'status': 'processing'})
        """
        if not isinstance(output_data, dict):
            raise ValueError("Output data must be a dictionary")

        self._task_result.output_data = output_data

    def get_input(self) -> dict:
        """
        Get the input parameters for this task.

        Returns:
            Dictionary of input parameters
        """
        return getattr(self._task, 'input_data', {}) or {}

    def get_task_def_name(self) -> str:
        """
        Get the task definition name.

        Returns:
            Task definition name
        """
        return self._task.task_def_name

    def get_workflow_task_type(self) -> str:
        """
        Get the workflow task type.

        Returns:
            Workflow task type
        """
        return getattr(self._task, 'workflow_task', {}).get('type', '') if hasattr(self._task, 'workflow_task') else ''

    def __repr__(self) -> str:
        return (
            f"TaskContext(task_id={self.get_task_id()}, "
            f"workflow_id={self.get_workflow_instance_id()}, "
            f"retry_count={self.get_retry_count()})"
        )


def get_task_context() -> TaskContext:
    """
    Get the current task context.

    This function retrieves the TaskContext for the currently executing task.
    It must be called from within a worker function decorated with @worker_task.

    Returns:
        TaskContext object for the current task

    Raises:
        RuntimeError: If called outside of a task execution context

    Example:
        from conductor.client.context.task_context import get_task_context
        from conductor.client.worker.worker_task import worker_task

        @worker_task(task_definition_name='process_order')
        def process_order(order_id: str) -> dict:
            ctx = get_task_context()

            ctx.add_log(f"Processing order {order_id}")
            ctx.add_log(f"Retry count: {ctx.get_retry_count()}")

            # Check if this is a retry
            if ctx.get_retry_count() > 0:
                ctx.add_log("This is a retry attempt")

            # Set callback for polling
            if not is_ready():
                ctx.set_callback_after(60)
                return {'status': 'pending'}

            return {'status': 'completed'}
    """
    context = _task_context_var.get()

    if context is None:
        raise RuntimeError(
            "No task context available. "
            "get_task_context() must be called from within a worker function "
            "decorated with @worker_task during task execution."
        )

    return context


def _set_task_context(task: Task, task_result: TaskResult) -> TaskContext:
    """
    Set the task context (internal use only).

    This is called by the task runner before executing a worker function.

    Args:
        task: The task being executed
        task_result: The task result being built

    Returns:
        The created TaskContext
    """
    context = TaskContext(task, task_result)
    _task_context_var.set(context)
    return context


def _clear_task_context() -> None:
    """
    Clear the task context (internal use only).

    This is called by the task runner after task execution completes.
    """
    _task_context_var.set(None)


# Convenience alias for backwards compatibility
TaskContext.get = staticmethod(get_task_context)
