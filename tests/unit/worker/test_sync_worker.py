import dataclasses
import logging
from unittest.mock import MagicMock, patch
from typing import Any

import pytest

from conductor.client.worker.worker import (
    Worker,
    is_callable_input_parameter_a_task,
    is_callable_return_value_of_type,
)
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.shared.http.enums import TaskResultStatus
from conductor.shared.worker.exception import NonRetryableException


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_task():
    task = MagicMock(spec=Task)
    task.task_id = "test_task_id"
    task.workflow_instance_id = "test_workflow_id"
    task.task_def_name = "test_task"
    task.input_data = {"param1": "value1", "param2": 42}
    return task


@pytest.fixture
def simple_execute_function():
    def func(param1: str, param2: int = 10):
        return {"result": f"{param1}_{param2}"}

    return func


@pytest.fixture
def task_input_execute_function():
    def func(task: Task):
        return {"result": f"processed_{task.task_id}"}

    return func


@pytest.fixture
def task_result_execute_function():
    def func(param1: str) -> TaskResult:
        result = TaskResult(
            task_id="test_task_id",
            workflow_instance_id="test_workflow_id",
            status=TaskResultStatus.COMPLETED,
            output_data={"result": f"task_result_{param1}"},
        )
        return result

    return func


@pytest.fixture
def worker(simple_execute_function):
    return Worker(
        task_definition_name="test_task",
        execute_function=simple_execute_function,
        poll_interval=200,
        domain="test_domain",
        worker_id="test_worker_id",
    )


def test_init_with_all_parameters(simple_execute_function):
    worker = Worker(
        task_definition_name="test_task",
        execute_function=simple_execute_function,
        poll_interval=300,
        domain="test_domain",
        worker_id="custom_worker_id",
    )

    assert worker.task_definition_name == "test_task"
    assert worker.poll_interval == 300
    assert worker.domain == "test_domain"
    assert worker.worker_id == "custom_worker_id"
    assert worker.execute_function == simple_execute_function


def test_init_with_defaults(simple_execute_function):
    worker = Worker(
        task_definition_name="test_task", execute_function=simple_execute_function
    )

    assert worker.task_definition_name == "test_task"
    assert worker.poll_interval == 100
    assert worker.domain is None
    assert worker.worker_id is not None
    assert worker.execute_function == simple_execute_function


def test_get_identity(worker):
    identity = worker.get_identity()
    assert identity == "test_worker_id"


def test_execute_success_with_simple_function(worker, mock_task):
    result = worker.execute(mock_task)

    assert isinstance(result, TaskResult)
    assert result.task_id == "test_task_id"
    assert result.workflow_instance_id == "test_workflow_id"
    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "value1_42"}


def test_execute_success_with_task_input_function(
    task_input_execute_function, mock_task
):
    worker = Worker(
        task_definition_name="test_task", execute_function=task_input_execute_function
    )

    result = worker.execute(mock_task)

    assert isinstance(result, TaskResult)
    assert result.task_id == "test_task_id"
    assert result.workflow_instance_id == "test_workflow_id"
    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "processed_test_task_id"}


def test_execute_success_with_task_result_function(
    task_result_execute_function, mock_task
):
    worker = Worker(
        task_definition_name="test_task", execute_function=task_result_execute_function
    )

    result = worker.execute(mock_task)

    assert isinstance(result, TaskResult)
    assert result.task_id == "test_task_id"
    assert result.workflow_instance_id == "test_workflow_id"
    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "task_result_value1"}


def test_execute_with_missing_parameters(worker, mock_task):
    mock_task.input_data = {"param1": "value1"}

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "value1_10"}


def test_execute_with_none_parameters(worker, mock_task):
    mock_task.input_data = {"param1": "value1", "param2": None}

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "value1_None"}


def test_execute_with_non_retryable_exception(worker, mock_task):
    def failing_function(param1: str, param2: int):
        raise NonRetryableException("Terminal error")

    worker.execute_function = failing_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
    assert result.reason_for_incompletion == "Terminal error"


def test_execute_with_general_exception(worker, mock_task):
    def failing_function(param1: str, param2: int):
        raise ValueError("General error")

    worker.execute_function = failing_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.FAILED
    assert result.reason_for_incompletion == "General error"
    assert len(result.logs) == 1
    assert "ValueError: General error" in result.logs[0].created_time


def test_execute_with_none_output(worker, mock_task):
    def none_function(param1: str, param2: int):
        return None

    worker.execute_function = none_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": None}


def test_execute_with_dataclass_output(worker, mock_task):
    @dataclasses.dataclass
    class TestOutput:
        value: str
        number: int

    def dataclass_function(param1: str, param2: int):
        return TestOutput(value=param1, number=param2)

    worker.execute_function = dataclass_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"value": "value1", "number": 42}


def test_execute_with_non_dict_output(worker, mock_task):
    def string_function(param1: str, param2: int):
        return f"result_{param1}_{param2}"

    worker.execute_function = string_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "result_value1_42"}


def test_execute_function_property(worker, simple_execute_function):
    assert worker.execute_function == simple_execute_function


def test_execute_function_setter(worker):
    def new_function(param1: str):
        return {"new_result": param1}

    worker.execute_function = new_function

    assert worker.execute_function == new_function
    assert worker._is_execute_function_input_parameter_a_task is False
    assert worker._is_execute_function_return_value_a_task_result is False


def test_execute_function_setter_with_task_input(task_input_execute_function):
    worker = Worker(task_definition_name="test_task", execute_function=lambda x: x)

    worker.execute_function = task_input_execute_function

    assert worker._is_execute_function_input_parameter_a_task is True
    assert worker._is_execute_function_return_value_a_task_result is False


def test_execute_function_setter_with_task_result(task_result_execute_function):
    worker = Worker(task_definition_name="test_task", execute_function=lambda x: x)

    worker.execute_function = task_result_execute_function

    assert worker._is_execute_function_input_parameter_a_task is False
    assert worker._is_execute_function_return_value_a_task_result is True


def test_is_callable_input_parameter_a_task_with_task_input(
    task_input_execute_function,
):
    result = is_callable_input_parameter_a_task(task_input_execute_function, Task)
    assert result is True


def test_is_callable_input_parameter_a_task_with_simple_function(
    simple_execute_function,
):
    result = is_callable_input_parameter_a_task(simple_execute_function, Task)
    assert result is False


def test_is_callable_input_parameter_a_task_with_multiple_parameters():
    def multi_param_func(param1: str, param2: int):
        return param1 + str(param2)

    result = is_callable_input_parameter_a_task(multi_param_func, Task)
    assert result is False


def test_is_callable_input_parameter_a_task_with_no_parameters():
    def no_param_func():
        return "result"

    result = is_callable_input_parameter_a_task(no_param_func, Task)
    assert result is False


def test_is_callable_input_parameter_a_task_with_empty_annotation():
    def empty_annotation_func(param):
        return param

    result = is_callable_input_parameter_a_task(empty_annotation_func, Task)
    assert result is True


def test_is_callable_input_parameter_a_task_with_object_annotation():
    def object_annotation_func(param: object):
        return param

    result = is_callable_input_parameter_a_task(object_annotation_func, Task)
    assert result is True


def test_is_callable_return_value_of_type_with_task_result(
    task_result_execute_function,
):
    result = is_callable_return_value_of_type(task_result_execute_function, TaskResult)
    assert result is True


def test_is_callable_return_value_of_type_with_simple_function(simple_execute_function):
    result = is_callable_return_value_of_type(simple_execute_function, TaskResult)
    assert result is False


def test_is_callable_return_value_of_type_with_any_return():
    def any_return_func(param1: str) -> Any:
        return {"result": param1}

    result = is_callable_return_value_of_type(any_return_func, TaskResult)
    assert result is False


def test_execute_with_empty_input_data(worker, mock_task):
    mock_task.input_data = {}

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "None_10"}


def test_execute_with_exception_no_args(worker, mock_task):
    def failing_function(param1: str, param2: int):
        raise Exception()

    worker.execute_function = failing_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.FAILED
    assert result.reason_for_incompletion is None


def test_execute_with_non_retryable_exception_no_args(worker, mock_task):
    def failing_function(param1: str, param2: int):
        raise NonRetryableException()

    worker.execute_function = failing_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
    assert result.reason_for_incompletion is None


def test_execute_with_task_result_returning_function(mock_task):
    def task_result_function(param1: str, param2: int) -> TaskResult:
        result = TaskResult(
            task_id="custom_task_id",
            workflow_instance_id="custom_workflow_id",
            status=TaskResultStatus.IN_PROGRESS,
            output_data={"custom_result": f"{param1}_{param2}"},
        )
        return result

    worker = Worker(
        task_definition_name="test_task", execute_function=task_result_function
    )

    result = worker.execute(mock_task)

    assert result.task_id == "test_task_id"
    assert result.workflow_instance_id == "test_workflow_id"
    assert result.status == TaskResultStatus.IN_PROGRESS
    assert result.output_data == {"custom_result": "value1_42"}


def test_execute_with_complex_input_data(worker, mock_task):
    mock_task.input_data = {
        "param1": "value1",
        "param2": 42,
        "param3": "simple_string",
        "param4": 123,
    }

    def complex_function(
        param1: str, param2: int, param3: str = None, param4: int = None
    ):
        return {"param1": param1, "param2": param2, "param3": param3, "param4": param4}

    worker.execute_function = complex_function

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {
        "param1": "value1",
        "param2": 42,
        "param3": "simple_string",
        "param4": 123,
    }


def test_execute_with_default_parameter_values(worker, mock_task):
    mock_task.input_data = {"param1": "value1"}

    def function_with_defaults(param1: str, param2: int = 100, param3: str = "default"):
        return f"{param1}_{param2}_{param3}"

    worker.execute_function = function_with_defaults

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "value1_100_default"}


def test_execute_with_serialization_sanitization(worker, mock_task):
    class CustomObject:
        def __init__(self, value):
            self.value = value

    def custom_object_function(param1: str, param2: int):
        return CustomObject(f"{param1}_{param2}")

    worker.execute_function = custom_object_function

    with patch.object(worker.api_client, "sanitize_for_serialization") as mock_sanitize:
        mock_sanitize.return_value = {"sanitized": "value"}

        result = worker.execute(mock_task)

        assert result.status == TaskResultStatus.COMPLETED
        mock_sanitize.assert_called_once()
        assert result.output_data == {"sanitized": "value"}


def test_execute_with_serialization_sanitization_non_dict_result(worker, mock_task):
    def string_function(param1: str, param2: int):
        return f"result_{param1}_{param2}"

    worker.execute_function = string_function

    with patch.object(worker.api_client, "sanitize_for_serialization") as mock_sanitize:
        mock_sanitize.return_value = "sanitized_string"

        result = worker.execute(mock_task)

        assert result.status == TaskResultStatus.COMPLETED
        mock_sanitize.assert_called_once()
        assert result.output_data == {"result": "sanitized_string"}


def test_worker_identity_generation():
    worker1 = Worker("task1", lambda x: x)
    worker2 = Worker("task2", lambda x: x)

    assert worker1.worker_id is not None
    assert worker2.worker_id is not None
    assert worker1.worker_id == worker2.worker_id  # Both use hostname


def test_worker_domain_property():
    worker = Worker("task", lambda x: x, domain="test_domain")
    assert worker.domain == "test_domain"

    worker.domain = "new_domain"
    assert worker.domain == "new_domain"


def test_worker_poll_interval_property():
    worker = Worker("task", lambda x: x, poll_interval=500)
    assert worker.poll_interval == 500

    worker.poll_interval = 1000
    assert worker.poll_interval == 1000


def test_execute_with_parameter_annotation_typing():
    def typed_function(param1: str, param2: str = None, param3: str = None):
        return {"result": f"{param1}_{param2}_{param3}"}

    worker = Worker("task", typed_function)
    mock_task = MagicMock(spec=Task)
    mock_task.task_id = "test_task_id"
    mock_task.workflow_instance_id = "test_workflow_id"
    mock_task.task_def_name = "test_task"
    mock_task.input_data = {
        "param1": "value1",
        "param2": "test_string",
        "param3": "another_string",
    }

    result = worker.execute(mock_task)

    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "value1_test_string_another_string"}
