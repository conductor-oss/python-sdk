"""
Comprehensive tests for Worker class to achieve 95%+ coverage.

Tests cover:
- Worker initialization with various parameter combinations
- Execute method with different input types
- Task result creation and output data handling
- Error handling (exceptions, NonRetryableException)
- Helper functions (is_callable_input_parameter_a_task, is_callable_return_value_of_type)
- Dataclass conversion
- Output data serialization (dict, dataclass, non-serializable objects)
- Complex type handling and parameter validation
"""

import dataclasses
import unittest
from typing import Any, Optional
from unittest.mock import Mock, patch

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker import Worker
from conductor.client.worker.base_worker import (
    is_callable_input_parameter_a_task,
    is_callable_return_value_of_type,
)
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


class TestWorkerHelperFunctions(unittest.TestCase):
    """Test helper functions used by Worker"""

    def test_is_callable_input_parameter_a_task_with_task_annotation(self):
        """Test function that takes Task as parameter"""
        def func(task: Task) -> dict:
            return {}

        result = is_callable_input_parameter_a_task(func, Task)
        self.assertTrue(result)

    def test_is_callable_input_parameter_a_task_with_object_annotation(self):
        """Test function that takes object as parameter"""
        def func(task: object) -> dict:
            return {}

        result = is_callable_input_parameter_a_task(func, Task)
        self.assertTrue(result)

    def test_is_callable_input_parameter_a_task_with_no_annotation(self):
        """Test function with no type annotation"""
        def func(task):
            return {}

        result = is_callable_input_parameter_a_task(func, Task)
        self.assertTrue(result)

    def test_is_callable_input_parameter_a_task_with_different_type(self):
        """Test function with different type annotation"""
        def func(data: dict) -> dict:
            return {}

        result = is_callable_input_parameter_a_task(func, Task)
        self.assertFalse(result)

    def test_is_callable_input_parameter_a_task_with_multiple_params(self):
        """Test function with multiple parameters returns False"""
        def func(task: Task, other: str) -> dict:
            return {}

        result = is_callable_input_parameter_a_task(func, Task)
        self.assertFalse(result)

    def test_is_callable_input_parameter_a_task_with_no_params(self):
        """Test function with no parameters returns False"""
        def func() -> dict:
            return {}

        result = is_callable_input_parameter_a_task(func, Task)
        self.assertFalse(result)

    def test_is_callable_return_value_of_type_with_matching_type(self):
        """Test function that returns TaskResult"""
        def func(task: Task) -> TaskResult:
            return TaskResult()

        result = is_callable_return_value_of_type(func, TaskResult)
        self.assertTrue(result)

    def test_is_callable_return_value_of_type_with_different_type(self):
        """Test function that returns different type"""
        def func(task: Task) -> dict:
            return {}

        result = is_callable_return_value_of_type(func, TaskResult)
        self.assertFalse(result)

    def test_is_callable_return_value_of_type_with_no_annotation(self):
        """Test function with no return annotation"""
        def func(task: Task):
            return {}

        result = is_callable_return_value_of_type(func, TaskResult)
        self.assertFalse(result)


class TestWorkerInitialization(unittest.TestCase):
    """Test Worker initialization with various parameter combinations"""

    def test_worker_init_minimal_params(self):
        """Test Worker initialization with minimal parameters"""
        def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        worker = Worker("test_task", simple_func)

        self.assertEqual(worker.task_definition_name, "test_task")
        self.assertEqual(worker.poll_interval, 100)
        self.assertIsNone(worker.domain)
        self.assertIsNotNone(worker.worker_id)

    def test_worker_init_with_all_params(self):
        """Test Worker initialization with all parameters"""
        def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        worker = Worker(
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

    def test_worker_get_identity(self):
        """Test get_identity returns worker_id"""
        def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        worker = Worker("test_task", simple_func, worker_id="test-worker-id")

        self.assertEqual(worker.get_identity(), "test-worker-id")


class TestWorkerExecuteWithTask(unittest.TestCase):
    """Test Worker execute method when function takes Task object"""

    def test_execute_with_task_parameter_returns_dict(self):
        """Test execute with function that takes Task and returns dict"""
        def task_func(task: Task) -> dict:
            return {"result": "success", "value": 42}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.task_id, "task-123")
        self.assertEqual(result.workflow_instance_id, "workflow-456")
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"result": "success", "value": 42})

    def test_execute_with_task_parameter_returns_task_result(self):
        """Test execute with function that takes Task and returns TaskResult"""
        def task_func(task: Task) -> TaskResult:
            result = TaskResult()
            result.status = TaskResultStatus.COMPLETED
            result.output_data = {"custom": "result"}
            return result

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-789"
        task.workflow_instance_id = "workflow-101"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.task_id, "task-789")
        self.assertEqual(result.workflow_instance_id, "workflow-101")
        self.assertEqual(result.output_data, {"custom": "result"})


class TestWorkerExecuteWithParameters(unittest.TestCase):
    """Test Worker execute method when function takes named parameters"""

    def test_execute_with_simple_parameters(self):
        """Test execute with function that takes simple parameters"""
        def task_func(name: str, age: int) -> dict:
            return {"greeting": f"Hello {name}, you are {age} years old"}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {"name": "Alice", "age": 30}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"greeting": "Hello Alice, you are 30 years old"})

    def test_execute_with_dataclass_parameter(self):
        """Test execute with function that takes dataclass parameter"""
        def task_func(user: UserInfo) -> dict:
            return {"message": f"User {user.name} is {user.age} years old"}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {
            "user": {"name": "Bob", "age": 25, "email": "bob@example.com"}
        }

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIn("Bob", result.output_data["message"])

    def test_execute_with_missing_parameter_no_default(self):
        """Test execute when required parameter is missing (no default value)"""
        def task_func(required_param: str) -> dict:
            return {"param": required_param}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}  # Missing required_param

        result = worker.execute(task)

        # Should pass None for missing parameter
        self.assertEqual(result.output_data, {"param": None})

    def test_execute_with_missing_parameter_has_default(self):
        """Test execute when parameter has default value"""
        def task_func(name: str = "Default Name", age: int = 18) -> dict:
            return {"name": name, "age": age}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {"name": "Charlie"}  # age is missing

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"name": "Charlie", "age": 18})

    def test_execute_with_all_parameters_missing_with_defaults(self):
        """Test execute when all parameters missing but have defaults"""
        def task_func(name: str = "Default", value: int = 100) -> dict:
            return {"name": name, "value": value}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"name": "Default", "value": 100})


class TestWorkerExecuteOutputSerialization(unittest.TestCase):
    """Test output data serialization in various formats"""

    def test_execute_output_as_dataclass(self):
        """Test execute when output is a dataclass"""
        def task_func(name: str, age: int) -> UserInfo:
            return UserInfo(name=name, age=age, email=f"{name}@example.com")

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {"name": "Diana", "age": 28}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIsInstance(result.output_data, dict)
        self.assertEqual(result.output_data["name"], "Diana")
        self.assertEqual(result.output_data["age"], 28)
        self.assertEqual(result.output_data["email"], "Diana@example.com")

    def test_execute_output_as_primitive_type(self):
        """Test execute when output is a primitive type (not dict)"""
        def task_func() -> str:
            return "simple string result"

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIsInstance(result.output_data, dict)
        self.assertEqual(result.output_data["result"], "simple string result")

    def test_execute_output_as_list(self):
        """Test execute when output is a list"""
        def task_func() -> list:
            return [1, 2, 3, 4, 5]

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        # List should be wrapped in dict
        self.assertIsInstance(result.output_data, dict)
        self.assertEqual(result.output_data["result"], [1, 2, 3, 4, 5])

    def test_execute_output_as_number(self):
        """Test execute when output is a number"""
        def task_func(a: int, b: int) -> int:
            return a + b

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {"a": 10, "b": 20}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIsInstance(result.output_data, dict)
        self.assertEqual(result.output_data["result"], 30)

    @patch('conductor.client.worker.worker.logger')
    def test_execute_output_non_serializable_recursion_error(self, mock_logger):
        """Test execute when output causes RecursionError during serialization"""
        def task_func() -> str:
            # Return a string to avoid dict being returned as-is
            return "test_string"

        worker = Worker("test_task", task_func)

        # Mock the api_client's sanitize_for_serialization to raise RecursionError
        worker.api_client.sanitize_for_serialization = Mock(side_effect=RecursionError("max recursion"))

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIn("error", result.output_data)
        self.assertIn("type", result.output_data)
        mock_logger.warning.assert_called()

    @patch('conductor.client.worker.worker.logger')
    def test_execute_output_non_serializable_type_error(self, mock_logger):
        """Test execute when output causes TypeError during serialization"""
        def task_func() -> NonSerializableClass:
            return NonSerializableClass("test data")

        worker = Worker("test_task", task_func)

        # Mock the api_client's sanitize_for_serialization to raise TypeError
        worker.api_client.sanitize_for_serialization = Mock(side_effect=TypeError("cannot serialize"))

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIn("error", result.output_data)
        self.assertIn("type", result.output_data)
        self.assertEqual(result.output_data["type"], "NonSerializableClass")
        mock_logger.warning.assert_called()

    @patch('conductor.client.worker.worker.logger')
    def test_execute_output_non_serializable_attribute_error(self, mock_logger):
        """Test execute when output causes AttributeError during serialization"""
        def task_func() -> Any:
            obj = NonSerializableClass("test")
            return obj

        worker = Worker("test_task", task_func)

        # Mock the api_client's sanitize_for_serialization to raise AttributeError
        worker.api_client.sanitize_for_serialization = Mock(side_effect=AttributeError("missing attribute"))

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIn("error", result.output_data)
        mock_logger.warning.assert_called()


class TestWorkerExecuteErrorHandling(unittest.TestCase):
    """Test error handling in Worker execute method"""

    def test_execute_with_non_retryable_exception_with_message(self):
        """Test execute with NonRetryableException with message"""
        def task_func(task: Task) -> dict:
            raise NonRetryableException("This error should not be retried")

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.FAILED_WITH_TERMINAL_ERROR)
        self.assertEqual(result.reason_for_incompletion, "This error should not be retried")

    def test_execute_with_non_retryable_exception_no_message(self):
        """Test execute with NonRetryableException without message"""
        def task_func(task: Task) -> dict:
            raise NonRetryableException()

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.FAILED_WITH_TERMINAL_ERROR)
        # No reason_for_incompletion should be set if no message

    @patch('conductor.client.worker.worker.logger')
    def test_execute_with_generic_exception_with_message(self, mock_logger):
        """Test execute with generic Exception with message"""
        def task_func(task: Task) -> dict:
            raise ValueError("Something went wrong")

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.FAILED)
        self.assertEqual(result.reason_for_incompletion, "Something went wrong")
        self.assertEqual(len(result.logs), 1)
        self.assertIn("Traceback", result.logs[0].log)
        mock_logger.error.assert_called()

    @patch('conductor.client.worker.worker.logger')
    def test_execute_with_generic_exception_no_message(self, mock_logger):
        """Test execute with generic Exception without message"""
        def task_func(task: Task) -> dict:
            raise RuntimeError()

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.FAILED)
        self.assertEqual(len(result.logs), 1)
        mock_logger.error.assert_called()


class TestWorkerExecuteTaskInProgress(unittest.TestCase):
    """Test Worker execute method with TaskInProgress"""

    def test_execute_with_task_in_progress_return(self):
        """Test execute when function returns TaskInProgress"""
        # Import here to avoid circular dependency
        from conductor.client.context.task_context import TaskInProgress

        def task_func(task: Task):
            # Return a TaskInProgress object with correct signature
            tip = TaskInProgress(callback_after_seconds=30, output={"status": "in_progress"})
            # Set task_id manually after creation
            tip.task_id = task.task_id
            return tip

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        # Should return TaskInProgress as-is
        self.assertIsInstance(result, TaskInProgress)
        self.assertEqual(result.task_id, "task-123")


class TestWorkerExecuteFunctionSetter(unittest.TestCase):
    """Test execute_function property setter"""

    def test_execute_function_setter_with_task_parameter(self):
        """Test that setting execute_function updates internal flags"""
        def func1(task: Task) -> dict:
            return {}

        def func2(name: str) -> dict:
            return {}

        worker = Worker("test_task", func1)

        # Initially should detect Task parameter
        self.assertTrue(worker._is_execute_function_input_parameter_a_task)

        # Change to function without Task parameter
        worker.execute_function = func2

        # Should update the flag
        self.assertFalse(worker._is_execute_function_input_parameter_a_task)

    def test_execute_function_setter_with_task_result_return(self):
        """Test that setting execute_function detects TaskResult return type"""
        def func1(task: Task) -> dict:
            return {}

        def func2(task: Task) -> TaskResult:
            return TaskResult()

        worker = Worker("test_task", func1)

        # Initially should not detect TaskResult return
        self.assertFalse(worker._is_execute_function_return_value_a_task_result)

        # Change to function returning TaskResult
        worker.execute_function = func2

        # Should update the flag
        self.assertTrue(worker._is_execute_function_return_value_a_task_result)

    def test_execute_function_getter(self):
        """Test execute_function property getter"""
        def original_func(task: Task) -> dict:
            return {"test": "value"}

        worker = Worker("test_task", original_func)

        # Should be able to get the function back
        retrieved_func = worker.execute_function
        self.assertEqual(retrieved_func, original_func)


class TestWorkerComplexScenarios(unittest.TestCase):
    """Test complex scenarios and edge cases"""

    def test_execute_with_nested_dataclass(self):
        """Test execute with nested dataclass parameters"""
        def task_func(order: OrderInfo) -> dict:
            return {
                "order_id": order.order_id,
                "user_name": order.user.name,
                "total": order.total
            }

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {
            "order": {
                "order_id": "ORD-001",
                "user": {
                    "name": "Eve",
                    "age": 35,
                    "email": "eve@example.com"
                },
                "total": 299.99
            }
        }

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data["order_id"], "ORD-001")
        self.assertEqual(result.output_data["user_name"], "Eve")
        self.assertEqual(result.output_data["total"], 299.99)

    def test_execute_with_mixed_simple_and_complex_types(self):
        """Test execute with mix of simple and complex type parameters"""
        def task_func(user: UserInfo, priority: str, count: int = 1) -> dict:
            return {
                "user": user.name,
                "priority": priority,
                "count": count
            }

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {
            "user": {"name": "Frank", "age": 40},
            "priority": "high"
            # count is missing, should use default
        }

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data["user"], "Frank")
        self.assertEqual(result.output_data["priority"], "high")
        self.assertEqual(result.output_data["count"], 1)

    def test_worker_initialization_with_none_poll_interval(self):
        """Test Worker initialization when poll_interval is explicitly None"""
        def simple_func(task: Task) -> dict:
            return {}

        worker = Worker("test_task", simple_func, poll_interval=None)

        # Should use default
        self.assertEqual(worker.poll_interval, 100)

    def test_worker_initialization_with_none_worker_id(self):
        """Test Worker initialization when worker_id is explicitly None"""
        def simple_func(task: Task) -> dict:
            return {}

        worker = Worker("test_task", simple_func, worker_id=None)

        # Should generate an ID
        self.assertIsNotNone(worker.worker_id)

    def test_execute_output_is_already_dict(self):
        """Test execute when output is already a dict (should not be wrapped)"""
        def task_func() -> dict:
            return {"key1": "value1", "key2": "value2"}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        # Should remain as-is
        self.assertEqual(result.output_data, {"key1": "value1", "key2": "value2"})

    def test_execute_with_empty_input_data(self):
        """Test execute with empty input_data"""
        def task_func(param: str = "default") -> dict:
            return {"param": param}

        worker = Worker("test_task", task_func)

        task = Task()
        task.task_id = "task-123"
        task.workflow_instance_id = "workflow-456"
        task.task_def_name = "test_task"
        task.input_data = {}

        result = worker.execute(task)

        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data["param"], "default")


if __name__ == '__main__':
    unittest.main()
