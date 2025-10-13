import pytest

from conductor.shared.worker.task_options import (
    TaskOptions,
    get_task_options,
    task_options,
)


def test_task_options_all_parameters():
    options = TaskOptions(
        timeout_seconds=120,
        response_timeout_seconds=60,
        poll_timeout_seconds=30,
        retry_count=3,
        retry_logic="LINEAR_BACKOFF",
        retry_delay_seconds=1,
        backoff_scale_factor=2,
        rate_limit_per_frequency=100,
        rate_limit_frequency_in_seconds=10,
        concurrent_exec_limit=5,
        timeout_policy="TIME_OUT_WF",
        owner_email="test@example.com",
        description="Test task",
    )

    assert options.timeout_seconds == 120
    assert options.response_timeout_seconds == 60
    assert options.poll_timeout_seconds == 30
    assert options.retry_count == 3
    assert options.retry_logic == "LINEAR_BACKOFF"
    assert options.retry_delay_seconds == 1
    assert options.backoff_scale_factor == 2
    assert options.rate_limit_per_frequency == 100
    assert options.rate_limit_frequency_in_seconds == 10
    assert options.concurrent_exec_limit == 5
    assert options.timeout_policy == "TIME_OUT_WF"
    assert options.owner_email == "test@example.com"
    assert options.description == "Test task"


def test_task_options_partial_parameters():
    options = TaskOptions(
        timeout_seconds=120,
        retry_count=3,
    )

    assert options.timeout_seconds == 120
    assert options.retry_count == 3
    assert options.response_timeout_seconds is None
    assert options.poll_timeout_seconds is None


def test_task_options_to_dict():
    options = TaskOptions(
        timeout_seconds=120,
        retry_count=3,
        retry_logic="LINEAR_BACKOFF",
    )

    result = options.to_dict()

    assert result["timeout_seconds"] == 120
    assert result["retry_count"] == 3
    assert result["retry_logic"] == "LINEAR_BACKOFF"
    assert "response_timeout_seconds" not in result


def test_task_options_validation_negative_timeout():
    with pytest.raises(ValueError, match="timeout_seconds must be >= 0"):
        TaskOptions(timeout_seconds=-1)


def test_task_options_validation_response_timeout_zero():
    with pytest.raises(ValueError, match="response_timeout_seconds must be >= 1"):
        TaskOptions(response_timeout_seconds=0)


def test_task_options_validation_negative_retry_count():
    with pytest.raises(ValueError, match="retry_count must be >= 0"):
        TaskOptions(retry_count=-1)


def test_task_options_validation_invalid_retry_logic():
    with pytest.raises(ValueError, match="retry_logic must be one of"):
        TaskOptions(retry_logic="INVALID")


def test_task_options_validation_valid_retry_logics():
    for logic in ["FIXED", "LINEAR_BACKOFF", "EXPONENTIAL_BACKOFF"]:
        options = TaskOptions(retry_logic=logic)
        assert options.retry_logic == logic


def test_task_options_validation_invalid_timeout_policy():
    with pytest.raises(ValueError, match="timeout_policy must be one of"):
        TaskOptions(timeout_policy="INVALID")


def test_task_options_validation_valid_timeout_policies():
    for policy in ["TIME_OUT_WF", "ALERT_ONLY", "RETRY"]:
        options = TaskOptions(timeout_policy=policy)
        assert options.timeout_policy == policy


def test_task_options_validation_negative_backoff_scale_factor():
    with pytest.raises(ValueError, match="backoff_scale_factor must be >= 1"):
        TaskOptions(backoff_scale_factor=0)


def test_task_options_validation_negative_rate_limit():
    with pytest.raises(ValueError, match="rate_limit_per_frequency must be >= 0"):
        TaskOptions(rate_limit_per_frequency=-1)


def test_task_options_validation_negative_concurrent_exec_limit():
    with pytest.raises(ValueError, match="concurrent_exec_limit must be >= 0"):
        TaskOptions(concurrent_exec_limit=-1)


def test_task_options_decorator_basic():
    @task_options(timeout_seconds=120, retry_count=3)
    def my_task(_input_data):
        return {"result": "success"}

    options = get_task_options(my_task)

    assert options is not None
    assert options.timeout_seconds == 120
    assert options.retry_count == 3


def test_task_options_decorator_all_parameters():
    @task_options(
        timeout_seconds=120,
        response_timeout_seconds=60,
        poll_timeout_seconds=30,
        retry_count=3,
        retry_logic="LINEAR_BACKOFF",
        retry_delay_seconds=1,
        backoff_scale_factor=2,
        rate_limit_per_frequency=100,
        rate_limit_frequency_in_seconds=10,
        concurrent_exec_limit=5,
        timeout_policy="TIME_OUT_WF",
        owner_email="test@example.com",
        description="Test task",
    )
    def my_task(_input_data):
        return {"result": "success"}

    options = get_task_options(my_task)

    assert options.timeout_seconds == 120
    assert options.response_timeout_seconds == 60
    assert options.poll_timeout_seconds == 30
    assert options.retry_count == 3
    assert options.retry_logic == "LINEAR_BACKOFF"
    assert options.retry_delay_seconds == 1
    assert options.backoff_scale_factor == 2
    assert options.rate_limit_per_frequency == 100
    assert options.rate_limit_frequency_in_seconds == 10
    assert options.concurrent_exec_limit == 5
    assert options.timeout_policy == "TIME_OUT_WF"
    assert options.owner_email == "test@example.com"
    assert options.description == "Test task"


def test_task_options_decorator_function_still_callable():
    @task_options(timeout_seconds=120)
    def my_task(input_data):
        return {"result": input_data}

    result = my_task("test")
    assert result == {"result": "test"}


def test_task_options_decorator_function_name_preserved():
    @task_options(timeout_seconds=120)
    def my_task(_input_data):
        return {"result": "success"}

    assert my_task.__name__ == "my_task"


def test_get_task_options_no_decorator():
    def my_task(_input_data):
        return {"result": "success"}

    options = get_task_options(my_task)
    assert options is None


def test_task_options_decorator_validation_error():
    with pytest.raises(ValueError, match="timeout_seconds must be >= 0"):

        @task_options(timeout_seconds=-1)
        def my_task(_input_data):
            return {"result": "success"}
