import logging
from unittest.mock import MagicMock, patch

import pytest

from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter
from conductor.asyncio_client.adapters.models.task_result_adapter import TaskResultAdapter
from conductor.asyncio_client.worker.worker import Worker, is_callable_input_parameter_a_task, is_callable_return_value_of_type
from conductor.shared.http.enums import TaskResultStatus
from conductor.shared.worker.exception import NonRetryableException


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_task():
    task = MagicMock(spec=TaskAdapter)
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
    def func(task: TaskAdapter):
        return {"result": f"processed_{task.task_id}"}
    return func


@pytest.fixture
def task_result_execute_function():
    def func(param1: str):
        result = TaskResultAdapter(
            task_id="test_task_id",
            workflow_instance_id="test_workflow_id",
            status=TaskResultStatus.COMPLETED,
            output_data={"result": f"task_result_{param1}"}
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
        worker_id="test_worker_id"
    )


def test_init_with_all_parameters(simple_execute_function):
    worker = Worker(
        task_definition_name="test_task",
        execute_function=simple_execute_function,
        poll_interval=300,
        domain="test_domain",
        worker_id="custom_worker_id"
    )
    
    assert worker.task_definition_name == "test_task"
    assert worker.poll_interval == 300
    assert worker.domain == "test_domain"
    assert worker.worker_id == "custom_worker_id"
    assert worker.execute_function == simple_execute_function


def test_init_with_defaults(simple_execute_function):
    worker = Worker(
        task_definition_name="test_task",
        execute_function=simple_execute_function
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
    
    assert isinstance(result, TaskResultAdapter)
    assert result.task_id == "test_task_id"
    assert result.workflow_instance_id == "test_workflow_id"
    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "value1_42"}


def test_execute_success_with_task_input_function(task_input_execute_function, mock_task):
    worker = Worker(
        task_definition_name="test_task",
        execute_function=task_input_execute_function
    )
    
    result = worker.execute(mock_task)
    
    assert isinstance(result, TaskResultAdapter)
    assert result.task_id == "test_task_id"
    assert result.workflow_instance_id == "test_workflow_id"
    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": "processed_test_task_id"}


def test_execute_success_with_task_result_function(task_result_execute_function, mock_task):
    worker = Worker(
        task_definition_name="test_task",
        execute_function=task_result_execute_function
    )
    
    result = worker.execute(mock_task)
    
    assert isinstance(result, TaskResultAdapter)
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
    assert "ValueError: General error" in result.logs[0].log


def test_execute_with_none_output(worker, mock_task):
    def none_function(param1: str, param2: int):
        return None
    
    worker.execute_function = none_function
    
    result = worker.execute(mock_task)
    
    assert result.status == TaskResultStatus.COMPLETED
    assert result.output_data == {"result": None}


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
    worker = Worker(
        task_definition_name="test_task",
        execute_function=lambda x: x
    )
    
    worker.execute_function = task_input_execute_function
    
    assert worker._is_execute_function_input_parameter_a_task is True
    assert worker._is_execute_function_return_value_a_task_result is False


def test_execute_function_setter_with_task_result(task_result_execute_function):
    worker = Worker(
        task_definition_name="test_task",
        execute_function=lambda x: x
    )
    
    worker.execute_function = task_result_execute_function
    
    assert worker._is_execute_function_input_parameter_a_task is False
    assert worker._is_execute_function_return_value_a_task_result is False


def test_is_callable_input_parameter_a_task_with_task_input(task_input_execute_function):
    result = is_callable_input_parameter_a_task(task_input_execute_function, TaskAdapter)
    assert result is True


def test_is_callable_input_parameter_a_task_with_simple_function(simple_execute_function):
    result = is_callable_input_parameter_a_task(simple_execute_function, TaskAdapter)
    assert result is False


def test_is_callable_input_parameter_a_task_with_multiple_parameters():
    def multi_param_func(param1: str, param2: int):
        return param1 + str(param2)
    
    result = is_callable_input_parameter_a_task(multi_param_func, TaskAdapter)
    assert result is False


def test_is_callable_input_parameter_a_task_with_no_parameters():
    def no_param_func():
        return "result"
    
    result = is_callable_input_parameter_a_task(no_param_func, TaskAdapter)
    assert result is False


def test_is_callable_return_value_of_type_with_task_result(task_result_execute_function):
    result = is_callable_return_value_of_type(task_result_execute_function, TaskResultAdapter)
    assert result is False


def test_is_callable_return_value_of_type_with_simple_function(simple_execute_function):
    result = is_callable_return_value_of_type(simple_execute_function, TaskResultAdapter)
    assert result is False


def test_is_callable_return_value_of_type_with_any_return():
    def any_return_func(param1: str) -> any:
        return {"result": param1}
    
    result = is_callable_return_value_of_type(any_return_func, TaskResultAdapter)
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
    def task_result_function(param1: str, param2: int):
        result = TaskResultAdapter(
            task_id="custom_task_id",
            workflow_instance_id="custom_workflow_id",
            status=TaskResultStatus.IN_PROGRESS,
            output_data={"custom_result": f"{param1}_{param2}"}
        )
        return result
    
    worker = Worker(
        task_definition_name="test_task",
        execute_function=task_result_function
    )
    
    result = worker.execute(mock_task)
    
    assert result.task_id == "test_task_id"
    assert result.workflow_instance_id == "test_workflow_id"
    assert result.status == TaskResultStatus.IN_PROGRESS
    assert result.output_data == {"custom_result": "value1_42"}
