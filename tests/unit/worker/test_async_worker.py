import asyncio
import dataclasses
import unittest
from typing import Any, Optional
from unittest.mock import Mock, patch

from conductor.client.automator.task_runner_asyncio import TaskRunnerAsyncIO
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.async_worker import AsyncWorker
from conductor.client.worker.exception import NonRetryableException


@dataclasses.dataclass
class UserInfo:
    """Test dataclass for complex type testing"""
    name: str
    age: int
    email: Optional[str] = None


@dataclasses.dataclass
class OrderInfo:
    """Test dataclass for nested object testing"""
    order_id: str
    user: UserInfo
    total: float


class NonSerializableClass:
    """A class that cannot be easily serialized"""
    def __init__(self, data):
        self.data = data
        self._internal = lambda x: x  # Lambda cannot be serialized

    def __str__(self):
        return f"NonSerializable({self.data})"


class TestAsyncWorkerInitialization(unittest.TestCase):
    """Test AsyncWorker initialization with various parameter combinations"""

    def test_worker_init_minimal_params(self):
        """Test AsyncWorker initialization with minimal parameters"""
        async def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        worker = AsyncWorker("test_task", simple_func)

        self.assertEqual(worker.task_definition_name, "test_task")
        self.assertEqual(worker.poll_interval, 100)
        self.assertIsNone(worker.domain)
        self.assertIsNotNone(worker.worker_id)

    def test_worker_init_with_all_params(self):
        """Test AsyncWorker initialization with all parameters"""
        async def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        worker = AsyncWorker(
            task_definition_name="test_task",
            execute_function=simple_func,
            poll_interval=2.5,
            domain="staging",
            worker_id="worker-456",
        )

        self.assertEqual(worker.task_definition_name, "test_task")
        self.assertEqual(worker.poll_interval, 2.5)
        self.assertEqual(worker.domain, "staging")
        self.assertEqual(worker.worker_id, "worker-456")


class TestAsyncWorkerExecute(unittest.IsolatedAsyncioTestCase):
    """Test AsyncWorker execute method"""

    async def test_execute_with_task_parameter_returns_dict(self):
        """Test execute with function that takes Task and returns dict"""
        async def task_func(task: Task) -> dict:
            return {"result": "success", "value": 42}

        worker = AsyncWorker("test_task", task_func)
        config = Configuration()
        runner = TaskRunnerAsyncIO(worker, config)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = await runner._execute_task(task)

        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.task_id, "task-123")
        self.assertEqual(result.workflow_instance_id, "workflow-456")
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"result": "success", "value": 42})

    async def test_execute_with_simple_parameters(self):
        """Test execute with function that takes simple parameters"""
        async def task_func(name: str, age: int) -> dict:
            return {"greeting": f"Hello {name}, you are {age} years old"}

        worker = AsyncWorker("test_task", task_func)
        config = Configuration()
        runner = TaskRunnerAsyncIO(worker, config)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {"name": "Alice", "age": 30}

        result = await runner._execute_task(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"greeting": "Hello Alice, you are 30 years old"})

    async def test_execute_with_non_retryable_exception(self):
        """Test execute with NonRetryableException"""
        async def task_func(task: Task) -> dict:
            raise NonRetryableException("This error should not be retried")

        worker = AsyncWorker("test_task", task_func)
        config = Configuration()
        runner = TaskRunnerAsyncIO(worker, config)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = await runner._execute_task(task)

        self.assertEqual(result.status, TaskResultStatus.FAILED_WITH_TERMINAL_ERROR)
        self.assertEqual(result.reason_for_incompletion, "This error should not be retried")

    @patch('conductor.client.automator.task_runner_asyncio.logger')
    async def test_execute_with_generic_exception(self, mock_logger):
        """Test execute with generic Exception"""
        async def task_func(task: Task) -> dict:
            raise ValueError("Something went wrong")

        worker = AsyncWorker("test_task", task_func)
        config = Configuration()
        runner = TaskRunnerAsyncIO(worker, config)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = await runner._execute_task(task)

        self.assertEqual(result.status, TaskResultStatus.FAILED)
        self.assertEqual(result.reason_for_incompletion, "Something went wrong")
        self.assertEqual(len(result.logs), 1)
        self.assertIn("Traceback", result.logs[0].log)
        mock_logger.error.assert_called()

    async def test_execute_with_async_function(self):
        """Test execute with async function"""
        async def async_task_func(task: Task) -> dict:
            await asyncio.sleep(0.01)
            return {"result": "async_success"}

        worker = AsyncWorker("test_task", async_task_func)
        config = Configuration()
        runner = TaskRunnerAsyncIO(worker, config)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = await runner._execute_task(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"result": "async_success"})


if __name__ == '__main__':
    unittest.main()
