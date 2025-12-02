from __future__ import annotations
import abc
import os
import socket
from typing import Union

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult

DEFAULT_POLLING_INTERVAL = 100  # ms


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    value = os.getenv(key, '').lower()
    if value in ('true', '1', 'yes'):
        return True
    elif value in ('false', '0', 'no'):
        return False
    return default


class WorkerInterface(abc.ABC):
    """
    Abstract base class for implementing Conductor workers.

    RECOMMENDED: Use @worker_task decorator instead of implementing this interface directly.
    The decorator provides automatic worker registration, configuration management, and
    cleaner syntax.

    Example using @worker_task (RECOMMENDED):
        from conductor.client.worker.worker_task import worker_task

        @worker_task(task_definition_name='my_task', thread_count=10)
        def my_worker(input_value: int) -> dict:
            return {'result': input_value * 2}

    Example implementing WorkerInterface (for advanced use cases):
        class MyWorker(WorkerInterface):
            def execute(self, task: Task) -> TaskResult:
                task_result = self.get_task_result_from_task(task)
                task_result.status = TaskResultStatus.COMPLETED
                return task_result
    """
    def __init__(self, task_definition_name: Union[str, list]):
        self.task_definition_name = task_definition_name
        self.next_task_index = 0
        self._task_definition_name_cache = None
        self._domain = None
        self._poll_interval = DEFAULT_POLLING_INTERVAL
        self.thread_count = 1
        self.register_task_def = False
        self.poll_timeout = 100  # milliseconds
        self.lease_extend_enabled = False
        self.overwrite_task_def = True  # Default: overwrite existing task definitions
        self.strict_schema = False  # Default: allow additional properties in schemas

    @abc.abstractmethod
    def execute(self, task: Task) -> TaskResult:
        """
        Executes a task and returns the updated task.

        Execution Mode (automatically detected):
        ----------------------------------------
        - Sync (def): Execute in thread pool, return TaskResult directly
        - Async (async def): Execute as non-blocking coroutine in BackgroundEventLoop

        Sync Example:
            def execute(self, task: Task) -> TaskResult:
                # Executes in ThreadPoolExecutor
                # Concurrency limited by self.thread_count
                result = process_task(task)
                task_result = self.get_task_result_from_task(task)
                task_result.status = TaskResultStatus.COMPLETED
                return task_result

        Async Example:
            async def execute(self, task: Task) -> TaskResult:
                # Executes as non-blocking coroutine
                # 10-100x better concurrency for I/O-bound workloads
                result = await async_api_call(task)
                task_result = self.get_task_result_from_task(task)
                task_result.status = TaskResultStatus.COMPLETED
                return task_result

        :param task: Task to execute (required)
        :return: TaskResult with status COMPLETED, FAILED, or IN_PROGRESS
        """
        ...

    def get_identity(self) -> str:
        """
        Retrieve the hostname of the instance that the worker is running.

        :return: str
        """
        return socket.gethostname()

    def get_polling_interval_in_seconds(self) -> float:
        """
        Retrieve interval in seconds at which the server should be polled for worker tasks.

        :return: float
                 Default: 100ms
        """
        return (self.poll_interval if self.poll_interval else DEFAULT_POLLING_INTERVAL) / 1000

    def get_task_definition_name(self) -> str:
        """
        Retrieve the name of the task definition the worker is currently working on.

        :return: TaskResult
        """
        return self.task_definition_name_cache

    @property
    def task_definition_names(self):
        if isinstance(self.task_definition_name, list):
            return self.task_definition_name
        else:
            return [self.task_definition_name]

    @property
    def task_definition_name_cache(self):
        if self._task_definition_name_cache is None:
            self._task_definition_name_cache = self.compute_task_definition_name()
        return self._task_definition_name_cache

    def clear_task_definition_name_cache(self):
        self._task_definition_name_cache = None

    def compute_task_definition_name(self):
        if isinstance(self.task_definition_name, list):
            task_definition_name = self.task_definition_name[self.next_task_index]
            self.next_task_index = (self.next_task_index + 1) % len(self.task_definition_name)
            return task_definition_name
        return self.task_definition_name

    def get_task_result_from_task(self, task: Task) -> TaskResult:
        """
        Retrieve the TaskResult object from given task.

        :param Task: (required)
        :return: TaskResult
        """
        return TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=self.get_identity()
        )

    def get_domain(self) -> str:
        """
        Retrieve the domain of the worker.

        :return: str
        """
        return self.domain

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, value):
        self._domain = value

    @property
    def poll_interval(self):
        return self._poll_interval

    @poll_interval.setter
    def poll_interval(self, value):
        self._poll_interval = value
