from typing import Union, cast
from unittest.mock import patch, MagicMock

from conductor.client.worker.worker_task import WorkerTask, worker_task
from conductor.client.workflow.task.simple_task import SimpleTask


def test_worker_task_decorator_basic():
    @WorkerTask("test_task")
    def test_func(param1, param2=10):
        return {"result": f"{param1}_{param2}"}

    assert test_func.__name__ == "test_func"
    assert callable(test_func)


def test_worker_task_decorator_with_parameters():
    @WorkerTask(
        task_definition_name="test_task",
        poll_interval=200,
        domain="test_domain",
        worker_id="test_worker",
        poll_interval_seconds=5,
    )
    def test_func(param1):
        return {"result": param1}

    assert test_func.__name__ == "test_func"
    assert callable(test_func)


def test_worker_task_decorator_with_config_defaults():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 150
        mock_config.get_domain.return_value = "config_domain"
        mock_config.get_poll_interval_seconds.return_value = 3
        mock_config_class.return_value = mock_config

        @WorkerTask(
            "test_task", poll_interval=None, domain=None, poll_interval_seconds=None
        )
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"
        mock_config.get_poll_interval.assert_called_once()
        mock_config.get_domain.assert_called_once()
        mock_config.get_poll_interval_seconds.assert_called_once()


def test_worker_task_decorator_poll_interval_conversion():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 100
        mock_config.get_domain.return_value = "default_domain"
        mock_config.get_poll_interval_seconds.return_value = 0
        mock_config_class.return_value = mock_config

        @WorkerTask("test_task", poll_interval_seconds=2)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"


def test_worker_task_decorator_poll_interval_seconds_override():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 100
        mock_config.get_domain.return_value = "default_domain"
        mock_config.get_poll_interval_seconds.return_value = 0
        mock_config_class.return_value = mock_config

        @WorkerTask("test_task", poll_interval=200, poll_interval_seconds=3)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"


def test_worker_task_decorator_registration():
    with patch(
        "conductor.client.worker.worker_task.register_decorated_fn"
    ) as mock_register:

        @WorkerTask(
            "test_task",
            poll_interval=300,
            domain="test_domain",
            worker_id="test_worker",
        )
        def test_func(param1):
            return {"result": param1}

        mock_register.assert_called_once()
        call_args = mock_register.call_args
        assert call_args[1]["name"] == "test_task"
        assert call_args[1]["poll_interval"] == 300
        assert call_args[1]["domain"] == "test_domain"
        assert call_args[1]["worker_id"] == "test_worker"
        assert "func" in call_args[1]


def test_worker_task_decorator_with_task_ref_name():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @WorkerTask("test_task")
        def test_func(param1, param2=10):
            return {"result": f"{param1}_{param2}"}

        result: Union[SimpleTask, dict] = test_func(
            param1="value1", param2=20, task_ref_name="ref_task"
        )

        assert isinstance(result, SimpleTask)
        task_result = cast(SimpleTask, result)
        assert hasattr(task_result, "name")
        assert hasattr(task_result, "task_reference_name")
        assert hasattr(task_result, "input_parameters")
        assert task_result.name == "test_task"
        assert task_result.task_reference_name == "ref_task"
        assert "param1" in task_result.input_parameters
        assert "param2" in task_result.input_parameters
        assert task_result.input_parameters["param1"] == "value1"
        assert task_result.input_parameters["param2"] == 20


def test_worker_task_decorator_without_task_ref_name():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @WorkerTask("test_task")
        def test_func(param1, param2=10):
            return {"result": f"{param1}_{param2}"}

        result = test_func("value1", param2=20)

        assert result == {"result": "value1_20"}


def test_worker_task_decorator_preserves_function_metadata():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @WorkerTask("test_task")
        def test_func(param1: str, param2: int = 10) -> dict:
            """Test function docstring"""
            return {"result": f"{param1}_{param2}"}

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring"
        assert test_func.__annotations__ == {
            "param1": str,
            "param2": int,
            "return": dict,
        }


def test_worker_task_simple_decorator_basic():
    @worker_task("test_task")
    def test_func(param1, param2=10):
        return {"result": f"{param1}_{param2}"}

    assert test_func.__name__ == "test_func"
    assert callable(test_func)


def test_worker_task_simple_decorator_with_parameters():
    @worker_task(
        task_definition_name="test_task",
        poll_interval_millis=250,
        domain="test_domain",
        worker_id="test_worker",
    )
    def test_func(param1):
        return {"result": param1}

    assert test_func.__name__ == "test_func"
    assert callable(test_func)


def test_worker_task_simple_decorator_with_config_defaults():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 150
        mock_config.get_domain.return_value = "config_domain"
        mock_config_class.return_value = mock_config

        @worker_task("test_task", poll_interval_millis=None, domain=None)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"
        mock_config.get_poll_interval.assert_called_once()
        mock_config.get_domain.assert_called_once()


def test_worker_task_simple_decorator_registration():
    with patch(
        "conductor.client.worker.worker_task.register_decorated_fn"
    ) as mock_register:

        @worker_task(
            "test_task",
            poll_interval_millis=350,
            domain="test_domain",
            worker_id="test_worker",
        )
        def test_func(param1):
            return {"result": param1}

        mock_register.assert_called_once()
        call_args = mock_register.call_args
        assert call_args[1]["name"] == "test_task"
        assert call_args[1]["poll_interval"] == 350
        assert call_args[1]["domain"] == "test_domain"
        assert call_args[1]["worker_id"] == "test_worker"
        assert "func" in call_args[1]


def test_worker_task_simple_decorator_with_task_ref_name():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @worker_task("test_task")
        def test_func(param1, param2=10):
            return {"result": f"{param1}_{param2}"}

        result: Union[SimpleTask, dict] = test_func(
            param1="value1", param2=20, task_ref_name="ref_task"
        )

        assert isinstance(result, SimpleTask)
        task_result = cast(SimpleTask, result)
        assert hasattr(task_result, "name")
        assert hasattr(task_result, "task_reference_name")
        assert hasattr(task_result, "input_parameters")
        assert task_result.name == "test_task"
        assert task_result.task_reference_name == "ref_task"
        assert "param1" in task_result.input_parameters
        assert "param2" in task_result.input_parameters
        assert task_result.input_parameters["param1"] == "value1"
        assert task_result.input_parameters["param2"] == 20


def test_worker_task_simple_decorator_without_task_ref_name():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @worker_task("test_task")
        def test_func(param1, param2=10):
            return {"result": f"{param1}_{param2}"}

        result = test_func("value1", param2=20)

        assert result == {"result": "value1_20"}


def test_worker_task_simple_decorator_preserves_function_metadata():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @worker_task("test_task")
        def test_func(param1: str, param2: int = 10) -> dict:
            """Test function docstring"""
            return {"result": f"{param1}_{param2}"}

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring"
        assert test_func.__annotations__ == {
            "param1": str,
            "param2": int,
            "return": dict,
        }


def test_worker_task_poll_interval_millis_calculation():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 100
        mock_config.get_domain.return_value = "default_domain"
        mock_config.get_poll_interval_seconds.return_value = 0
        mock_config_class.return_value = mock_config

        @WorkerTask("test_task", poll_interval_seconds=2)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"


def test_worker_task_poll_interval_seconds_zero():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 100
        mock_config.get_domain.return_value = "default_domain"
        mock_config.get_poll_interval_seconds.return_value = 0
        mock_config_class.return_value = mock_config

        @WorkerTask("test_task", poll_interval=200, poll_interval_seconds=0)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"


def test_worker_task_poll_interval_seconds_positive():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 100
        mock_config.get_domain.return_value = "default_domain"
        mock_config.get_poll_interval_seconds.return_value = 0
        mock_config_class.return_value = mock_config

        @WorkerTask("test_task", poll_interval_seconds=3)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"


def test_worker_task_none_values():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 100
        mock_config.get_domain.return_value = "default_domain"
        mock_config.get_poll_interval_seconds.return_value = 0
        mock_config_class.return_value = mock_config

        @WorkerTask("test_task", domain=None, worker_id=None)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"


def test_worker_task_simple_none_values():
    with patch(
        "conductor.client.worker.worker_task.Configuration"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.get_poll_interval.return_value = 100
        mock_config.get_domain.return_value = "default_domain"
        mock_config_class.return_value = mock_config

        @worker_task("test_task", domain=None, worker_id=None)
        def test_func(param1):
            return {"result": param1}

        assert test_func.__name__ == "test_func"


def test_worker_task_task_ref_name_removal():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @WorkerTask("test_task")
        def test_func(param1, param2=10):
            return {"result": f"{param1}_{param2}"}

        result: Union[SimpleTask, dict] = test_func(
            param1="value1", param2=20, task_ref_name="ref_task"
        )

        assert isinstance(result, SimpleTask)
        task_result = cast(SimpleTask, result)
        assert hasattr(task_result, "input_parameters")
        assert "task_ref_name" not in task_result.input_parameters


def test_worker_task_simple_task_ref_name_removal():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @worker_task("test_task")
        def test_func(param1, param2=10):
            return {"result": f"{param1}_{param2}"}

        result: Union[SimpleTask, dict] = test_func(
            param1="value1", param2=20, task_ref_name="ref_task"
        )

        assert isinstance(result, SimpleTask)
        task_result = cast(SimpleTask, result)
        assert hasattr(task_result, "input_parameters")
        assert "task_ref_name" not in task_result.input_parameters


def test_worker_task_empty_kwargs():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @WorkerTask("test_task")
        def test_func():
            return {"result": "no_params"}

        result: Union[SimpleTask, dict] = test_func(task_ref_name="ref_task")

        assert isinstance(result, SimpleTask)
        task_result = cast(SimpleTask, result)
        assert hasattr(task_result, "name")
        assert hasattr(task_result, "task_reference_name")
        assert hasattr(task_result, "input_parameters")
        assert task_result.name == "test_task"
        assert task_result.task_reference_name == "ref_task"
        assert task_result.input_parameters == {}


def test_worker_task_simple_empty_kwargs():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @worker_task("test_task")
        def test_func():
            return {"result": "no_params"}

        result: Union[SimpleTask, dict] = test_func(task_ref_name="ref_task")

        assert isinstance(result, SimpleTask)
        task_result = cast(SimpleTask, result)
        assert hasattr(task_result, "name")
        assert hasattr(task_result, "task_reference_name")
        assert hasattr(task_result, "input_parameters")
        assert task_result.name == "test_task"
        assert task_result.task_reference_name == "ref_task"
        assert task_result.input_parameters == {}


def test_worker_task_functools_wraps():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @WorkerTask("test_task")
        def test_func(param1: str, param2: int = 10) -> dict:
            """Test function docstring"""
            return {"result": f"{param1}_{param2}"}

        assert hasattr(test_func, "__wrapped__")
        assert test_func.__wrapped__ is not None


def test_worker_task_simple_functools_wraps():
    with patch("conductor.client.worker.worker_task.register_decorated_fn"):

        @worker_task("test_task")
        def test_func(param1: str, param2: int = 10) -> dict:
            """Test function docstring"""
            return {"result": f"{param1}_{param2}"}

        assert hasattr(test_func, "__wrapped__")
        assert test_func.__wrapped__ is not None
