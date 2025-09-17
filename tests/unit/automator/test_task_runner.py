import logging
import time

import pytest
from requests.structures import CaseInsensitiveDict

from conductor.client.automator.task_runner import TaskRunner
from conductor.client.codegen.rest import AuthorizationException, ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.telemetry.metrics_collector import MetricsCollector
from conductor.shared.configuration.settings.metrics_settings import MetricsSettings
from conductor.shared.http.enums.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import DEFAULT_POLLING_INTERVAL
from tests.unit.resources.workers import ClassWorker, OldFaultyExecutionWorker


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def get_valid_task_runner_with_worker_config():
    return TaskRunner(configuration=Configuration(), worker=get_valid_worker())


def get_valid_task_runner_with_worker_config_and_domain(domain):
    return TaskRunner(
        configuration=Configuration(), worker=get_valid_worker(domain=domain)
    )


def get_valid_task_runner_with_worker_config_and_poll_interval(poll_interval):
    return TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(poll_interval=poll_interval),
    )


def get_valid_task_runner():
    return TaskRunner(configuration=Configuration(), worker=get_valid_worker())


def get_valid_roundrobin_task_runner():
    return TaskRunner(
        configuration=Configuration(), worker=get_valid_multi_task_worker()
    )


def get_valid_task():
    return Task(
        task_id="VALID_TASK_ID", workflow_instance_id="VALID_WORKFLOW_INSTANCE_ID"
    )


def get_valid_task_result():
    return TaskResult(
        task_id="VALID_TASK_ID",
        workflow_instance_id="VALID_WORKFLOW_INSTANCE_ID",
        worker_id=get_valid_worker().get_identity(),
        status=TaskResultStatus.COMPLETED,
        output_data={
            "worker_style": "class",
            "secret_number": 1234,
            "is_it_true": False,
            "dictionary_ojb": {"name": "sdk_worker", "idx": 465},
            "case_insensitive_dictionary_ojb": CaseInsensitiveDict(
                data={"NaMe": "sdk_worker", "iDX": 465}
            ),
        },
    )


def get_valid_multi_task_worker():
    return ClassWorker(["task1", "task2", "task3", "task4", "task5", "task6"])


def get_valid_worker(domain=None, poll_interval=None):
    cw = ClassWorker("task")
    cw.domain = domain
    cw.poll_interval = poll_interval
    return cw


def test_initialization_with_invalid_worker():
    with pytest.raises(Exception, match="Invalid worker"):
        TaskRunner(
            configuration=Configuration("http://localhost:8080/api"), worker=None
        )


def test_initialization_with_domain_passed_in_constructor():
    task_runner = get_valid_task_runner_with_worker_config_and_domain("passed")
    assert task_runner.worker.domain == "passed"


def test_initialization_with_generic_domain_in_worker_config(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_DOMAIN", "generic")
    task_runner = get_valid_task_runner_with_worker_config_and_domain("passed")
    assert task_runner.worker.domain == "generic"


def test_initialization_with_specific_domain_in_worker_config(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_DOMAIN", "generic")
    monkeypatch.setenv("conductor_worker_task_domain", "test")
    task_runner = get_valid_task_runner_with_worker_config_and_domain("passed")
    assert task_runner.worker.domain == "test"


def test_initialization_with_generic_domain_in_env_var(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_DOMAIN", "cool")
    monkeypatch.setenv("CONDUCTOR_WORKER_task2_DOMAIN", "test")
    task_runner = get_valid_task_runner_with_worker_config_and_domain("passed")
    assert task_runner.worker.domain == "cool"


def test_initialization_with_specific_domain_in_env_var(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_DOMAIN", "generic")
    monkeypatch.setenv("CONDUCTOR_WORKER_task_DOMAIN", "hot")
    task_runner = get_valid_task_runner_with_worker_config_and_domain("passed")
    assert task_runner.worker.domain == "hot"


def test_initialization_with_default_polling_interval(monkeypatch):
    monkeypatch.delenv("conductor_worker_polling_interval", raising=False)
    task_runner = get_valid_task_runner()
    assert (
        task_runner.worker.get_polling_interval_in_seconds() * 1000
        == DEFAULT_POLLING_INTERVAL
    )


def test_initialization_with_polling_interval_passed_in_constructor(monkeypatch):
    expected_polling_interval_in_seconds = 3.0
    monkeypatch.delenv("conductor_worker_polling_interval", raising=False)
    task_runner = get_valid_task_runner_with_worker_config_and_poll_interval(3000)
    assert (
        task_runner.worker.get_polling_interval_in_seconds()
        == expected_polling_interval_in_seconds
    )


def test_initialization_with_common_polling_interval_in_worker_config(monkeypatch):
    monkeypatch.setenv("conductor_worker_polling_interval", "2000")
    expected_polling_interval_in_seconds = 2.0
    task_runner = get_valid_task_runner_with_worker_config_and_poll_interval(3000)
    assert (
        task_runner.worker.get_polling_interval_in_seconds()
        == expected_polling_interval_in_seconds
    )


def test_initialization_with_specific_polling_interval_in_worker_config(monkeypatch):
    monkeypatch.setenv("conductor_worker_polling_interval", "2000")
    monkeypatch.setenv("conductor_worker_task_polling_interval", "5000")
    expected_polling_interval_in_seconds = 5.0
    task_runner = get_valid_task_runner_with_worker_config_and_poll_interval(3000)
    assert (
        task_runner.worker.get_polling_interval_in_seconds()
        == expected_polling_interval_in_seconds
    )


def test_initialization_with_generic_polling_interval_in_env_var(monkeypatch):
    monkeypatch.setenv("conductor_worker_polling_interval", "1000.0")
    task_runner = get_valid_task_runner_with_worker_config_and_poll_interval(3000)
    assert task_runner.worker.get_polling_interval_in_seconds() == 1.0


def test_initialization_with_specific_polling_interval_in_env_var(monkeypatch):
    expected_polling_interval_in_seconds = 0.25
    monkeypatch.setenv("CONDUCTOR_WORKER_task_POLLING_INTERVAL", "250.0")
    task_runner = get_valid_task_runner_with_worker_config_and_poll_interval(3000)
    assert (
        task_runner.worker.get_polling_interval_in_seconds()
        == expected_polling_interval_in_seconds
    )


def test_run_once(mocker):
    expected_time = get_valid_worker().get_polling_interval_in_seconds()
    mocker.patch.object(TaskResourceApi, "poll", return_value=get_valid_task())
    mocker.patch.object(
        TaskResourceApi, "update_task", return_value="VALID_UPDATE_TASK_RESPONSE"
    )
    task_runner = get_valid_task_runner()
    start_time = time.time()
    task_runner.run_once()
    finish_time = time.time()
    spent_time = finish_time - start_time
    assert spent_time > expected_time


def test_run_once_roundrobin(mocker):
    mocker.patch.object(TaskResourceApi, "poll", return_value=get_valid_task())
    mock_update_task = mocker.patch.object(TaskResourceApi, "update_task")
    mock_update_task.return_value = "VALID_UPDATE_TASK_RESPONSE"
    task_runner = get_valid_roundrobin_task_runner()
    for i in range(6):
        current_task_name = task_runner.worker.get_task_definition_name()
        task_runner.run_once()
        assert (
            current_task_name
            == ["task1", "task2", "task3", "task4", "task5", "task6"][i]
        )


def test_poll_task(mocker):
    expected_task = get_valid_task()
    mocker.patch.object(TaskResourceApi, "poll", return_value=get_valid_task())
    task_runner = get_valid_task_runner()
    task = task_runner._TaskRunner__poll_task()
    assert task == expected_task


def test_poll_task_with_faulty_task_api(mocker):
    expected_task = None
    mocker.patch.object(TaskResourceApi, "poll", side_effect=Exception())
    task_runner = get_valid_task_runner()
    task = task_runner._TaskRunner__poll_task()
    assert task == expected_task


def test_execute_task_with_invalid_task():
    task_runner = get_valid_task_runner()
    task_result = task_runner._TaskRunner__execute_task(None)
    assert task_result is None


def test_execute_task_with_faulty_execution_worker(mocker):
    worker = OldFaultyExecutionWorker("task")
    expected_task_result = TaskResult(
        task_id="VALID_TASK_ID",
        workflow_instance_id="VALID_WORKFLOW_INSTANCE_ID",
        worker_id=worker.get_identity(),
        status=TaskResultStatus.FAILED,
        reason_for_incompletion="faulty execution",
        logs=mocker.ANY,
    )
    task_runner = TaskRunner(configuration=Configuration(), worker=worker)
    task = get_valid_task()
    task_result = task_runner._TaskRunner__execute_task(task)
    assert task_result == expected_task_result
    assert task_result.logs is not None


def test_execute_task():
    expected_task_result = get_valid_task_result()
    worker = get_valid_worker()
    task_runner = TaskRunner(configuration=Configuration(), worker=worker)
    task = get_valid_task()
    task_result = task_runner._TaskRunner__execute_task(task)
    assert task_result == expected_task_result


def test_update_task_with_invalid_task_result():
    expected_response = None
    task_runner = get_valid_task_runner()
    response = task_runner._TaskRunner__update_task(None)
    assert response == expected_response


def test_update_task_with_faulty_task_api(mocker):
    mocker.patch("time.sleep", return_value=None)
    mocker.patch.object(TaskResourceApi, "update_task", side_effect=Exception())
    task_runner = get_valid_task_runner()
    task_result = get_valid_task_result()
    response = task_runner._TaskRunner__update_task(task_result)
    assert response is None


def test_update_task(mocker):
    mocker.patch.object(
        TaskResourceApi, "update_task", return_value="VALID_UPDATE_TASK_RESPONSE"
    )
    task_runner = get_valid_task_runner()
    task_result = get_valid_task_result()
    response = task_runner._TaskRunner__update_task(task_result)
    assert response == "VALID_UPDATE_TASK_RESPONSE"


def test_wait_for_polling_interval_with_faulty_worker(mocker):
    expected_exception = Exception("Failed to get polling interval")
    mocker.patch.object(
        ClassWorker, "get_polling_interval_in_seconds", side_effect=expected_exception
    )
    task_runner = get_valid_task_runner()
    with pytest.raises(Exception, match="Failed to get polling interval"):
        task_runner._TaskRunner__wait_for_polling_interval()


def test_wait_for_polling_interval():
    expected_time = get_valid_worker().get_polling_interval_in_seconds()
    task_runner = get_valid_task_runner()
    start_time = time.time()
    task_runner._TaskRunner__wait_for_polling_interval()
    finish_time = time.time()
    spent_time = finish_time - start_time
    assert spent_time > expected_time


def test_initialization_with_metrics_collector():
    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )
    assert isinstance(task_runner.metrics_collector, MetricsCollector)


def test_initialization_without_metrics_collector():
    task_runner = TaskRunner(configuration=Configuration(), worker=get_valid_worker())
    assert task_runner.metrics_collector is None


def test_initialization_with_none_configuration():
    task_runner = TaskRunner(worker=get_valid_worker())
    assert isinstance(task_runner.configuration, Configuration)


def test_run_method_logging_config_application(mocker):
    mock_apply_logging = mocker.patch.object(Configuration, "apply_logging_config")
    mock_run_once = mocker.patch.object(TaskRunner, "run_once")
    mock_run_once.side_effect = KeyboardInterrupt()

    task_runner = get_valid_task_runner()
    try:
        task_runner.run()
    except KeyboardInterrupt:
        pass

    mock_apply_logging.assert_called_once()


def test_run_once_with_exception_handling(mocker):
    worker = get_valid_worker()
    mock_clear_cache = mocker.patch.object(worker, "clear_task_definition_name_cache")
    mocker.patch.object(
        TaskRunner,
        "_TaskRunner__wait_for_polling_interval",
        side_effect=Exception("Test exception"),
    )

    task_runner = TaskRunner(worker=worker)
    task_runner.run_once()

    mock_clear_cache.assert_not_called()


def test_poll_task_with_paused_worker(mocker):
    worker = get_valid_worker()
    mocker.patch.object(worker, "paused", return_value=True)

    task_runner = TaskRunner(worker=worker)
    result = task_runner._TaskRunner__poll_task()

    assert result is None


def test_poll_task_with_metrics_collector(mocker):
    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mocker.patch.object(TaskResourceApi, "poll", return_value=get_valid_task())
    mock_increment = mocker.patch.object(MetricsCollector, "increment_task_poll")
    mock_record_time = mocker.patch.object(MetricsCollector, "record_task_poll_time")

    task_runner._TaskRunner__poll_task()

    mock_increment.assert_called_once()
    mock_record_time.assert_called_once()


def test_poll_task_authorization_exception_invalid_token(mocker):
    auth_exception = AuthorizationException(status=401, reason="Unauthorized")
    auth_exception._error_code = "INVALID_TOKEN"

    mocker.patch.object(TaskResourceApi, "poll", side_effect=auth_exception)
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__poll_task()

    assert result is None


def test_poll_task_authorization_exception_with_metrics(mocker):
    auth_exception = AuthorizationException(status=403, reason="Forbidden")
    auth_exception._error_code = "FORBIDDEN"

    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mocker.patch.object(TaskResourceApi, "poll", side_effect=auth_exception)
    mock_increment_error = mocker.patch.object(
        MetricsCollector, "increment_task_poll_error"
    )

    result = task_runner._TaskRunner__poll_task()

    assert result is None
    mock_increment_error.assert_called_once()


def test_poll_task_api_exception(mocker):
    api_exception = ApiException()
    api_exception.reason = "Server Error"
    api_exception.code = 500

    mocker.patch.object(TaskResourceApi, "poll", side_effect=api_exception)
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__poll_task()

    assert result is None


def test_poll_task_api_exception_with_metrics(mocker):
    api_exception = ApiException()
    api_exception.reason = "Bad Request"
    api_exception.code = 400

    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mocker.patch.object(TaskResourceApi, "poll", side_effect=api_exception)
    mock_increment_error = mocker.patch.object(
        MetricsCollector, "increment_task_poll_error"
    )

    result = task_runner._TaskRunner__poll_task()

    assert result is None
    mock_increment_error.assert_called_once()


def test_poll_task_generic_exception_with_metrics(mocker):
    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mocker.patch.object(
        TaskResourceApi, "poll", side_effect=ValueError("Generic error")
    )
    mock_increment_error = mocker.patch.object(
        MetricsCollector, "increment_task_poll_error"
    )

    result = task_runner._TaskRunner__poll_task()

    assert result is None
    mock_increment_error.assert_called_once()


def test_execute_task_with_metrics_collector(mocker):
    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mock_record_time = mocker.patch.object(MetricsCollector, "record_task_execute_time")
    mock_record_size = mocker.patch.object(
        MetricsCollector, "record_task_result_payload_size"
    )

    task = get_valid_task()
    task_runner._TaskRunner__execute_task(task)

    mock_record_time.assert_called_once()
    mock_record_size.assert_called_once()


def test_execute_task_exception_with_metrics(mocker):
    metrics_settings = MetricsSettings()
    worker = OldFaultyExecutionWorker("task")
    task_runner = TaskRunner(
        configuration=Configuration(), worker=worker, metrics_settings=metrics_settings
    )

    mock_increment_error = mocker.patch.object(
        MetricsCollector, "increment_task_execution_error"
    )

    task = get_valid_task()
    task_result = task_runner._TaskRunner__execute_task(task)

    assert task_result.status == "FAILED"
    assert task_result.reason_for_incompletion == "faulty execution"
    assert len(task_result.logs) == 1
    assert isinstance(task_result.logs[0], TaskExecLog)
    mock_increment_error.assert_called_once()


def test_update_task_with_metrics_collector(mocker):
    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mocker.patch.object(TaskResourceApi, "update_task", return_value="SUCCESS")
    mock_increment_error = mocker.patch.object(
        MetricsCollector, "increment_task_update_error"
    )

    task_result = get_valid_task_result()
    response = task_runner._TaskRunner__update_task(task_result)

    assert response == "SUCCESS"
    mock_increment_error.assert_not_called()


def test_update_task_retry_logic_with_metrics(mocker):
    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mock_sleep = mocker.patch("time.sleep")
    mock_update = mocker.patch.object(TaskResourceApi, "update_task")
    mock_update.side_effect = [
        Exception("First attempt"),
        Exception("Second attempt"),
        "SUCCESS",
    ]
    mock_increment_error = mocker.patch.object(
        MetricsCollector, "increment_task_update_error"
    )

    task_result = get_valid_task_result()
    response = task_runner._TaskRunner__update_task(task_result)

    assert response == "SUCCESS"
    assert mock_sleep.call_count == 2
    assert mock_increment_error.call_count == 2


def test_update_task_all_retries_fail_with_metrics(mocker):
    metrics_settings = MetricsSettings()
    task_runner = TaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(),
        metrics_settings=metrics_settings,
    )

    mock_sleep = mocker.patch("time.sleep")
    mock_update = mocker.patch.object(TaskResourceApi, "update_task")
    mock_update.side_effect = Exception("All attempts fail")
    mock_increment_error = mocker.patch.object(
        MetricsCollector, "increment_task_update_error"
    )

    task_result = get_valid_task_result()
    response = task_runner._TaskRunner__update_task(task_result)

    assert response is None
    assert mock_sleep.call_count == 3
    assert mock_increment_error.call_count == 4


def test_get_property_value_from_env_generic_property(monkeypatch):
    monkeypatch.setenv("conductor_worker_domain", "test_domain")
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__get_property_value_from_env("domain", "task")
    assert result == "test_domain"


def test_get_property_value_from_env_uppercase_generic(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_DOMAIN", "test_domain_upper")
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__get_property_value_from_env("domain", "task")
    assert result == "test_domain_upper"


def test_get_property_value_from_env_task_specific(monkeypatch):
    monkeypatch.setenv("conductor_worker_domain", "generic_domain")
    monkeypatch.setenv("conductor_worker_task_domain", "task_specific_domain")
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__get_property_value_from_env("domain", "task")
    assert result == "task_specific_domain"


def test_get_property_value_from_env_uppercase_task_specific(monkeypatch):
    monkeypatch.setenv("conductor_worker_domain", "generic_domain")
    monkeypatch.setenv("CONDUCTOR_WORKER_task_DOMAIN", "task_specific_upper")
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__get_property_value_from_env("domain", "task")
    assert result == "task_specific_upper"


def test_get_property_value_from_env_fallback_to_generic(monkeypatch):
    monkeypatch.setenv("conductor_worker_domain", "generic_domain")
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__get_property_value_from_env(
        "domain", "nonexistent_task"
    )
    assert result == "generic_domain"


def test_get_property_value_from_env_no_value():
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__get_property_value_from_env(
        "nonexistent_prop", "task"
    )
    assert result is None


def test_set_worker_properties_invalid_polling_interval(monkeypatch, caplog):
    monkeypatch.setenv("conductor_worker_polling_interval", "invalid_float")
    worker = get_valid_worker()
    task_runner = TaskRunner(worker=worker)

    with caplog.at_level(logging.ERROR):
        task_runner._TaskRunner__set_worker_properties()

    assert "Error converting polling_interval to float value" in caplog.text


def test_set_worker_properties_exception_in_polling_interval(monkeypatch, caplog):
    monkeypatch.setenv("conductor_worker_polling_interval", "invalid_float")
    worker = get_valid_worker()
    task_runner = TaskRunner(worker=worker)

    with caplog.at_level(logging.ERROR):
        task_runner._TaskRunner__set_worker_properties()

    assert (
        "Error converting polling_interval to float value" in caplog.text
    )


def test_set_worker_properties_domain_from_env(monkeypatch):
    monkeypatch.setenv("conductor_worker_task_domain", "env_domain")
    worker = get_valid_worker()
    task_runner = TaskRunner(worker=worker)
    assert task_runner.worker.domain == "env_domain"


def test_set_worker_properties_polling_interval_from_env(monkeypatch):
    monkeypatch.setenv("conductor_worker_task_polling_interval", "2.5")
    worker = get_valid_worker()
    task_runner = TaskRunner(worker=worker)
    assert task_runner.worker.poll_interval == 2.5


def test_poll_task_with_domain_parameter(mocker):
    worker = get_valid_worker()
    mocker.patch.object(worker, "paused", return_value=False)
    mocker.patch.object(worker, "get_domain", return_value="test_domain")

    task_runner = TaskRunner(worker=worker)
    mock_poll = mocker.patch.object(
        TaskResourceApi, "poll", return_value=get_valid_task()
    )

    task_runner._TaskRunner__poll_task()

    mock_poll.assert_called_once_with(
        tasktype="task", workerid=worker.get_identity(), domain="test_domain"
    )


def test_poll_task_without_domain_parameter(mocker):
    worker = get_valid_worker()
    mocker.patch.object(worker, "paused", return_value=False)
    mocker.patch.object(worker, "get_domain", return_value=None)

    task_runner = TaskRunner(worker=worker)
    mock_poll = mocker.patch.object(
        TaskResourceApi, "poll", return_value=get_valid_task()
    )

    task_runner._TaskRunner__poll_task()

    mock_poll.assert_called_once_with(tasktype="task", workerid=worker.get_identity())


def test_execute_task_with_non_task_input():
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__execute_task("not_a_task")
    assert result is None


def test_update_task_with_non_task_result():
    task_runner = get_valid_task_runner()
    result = task_runner._TaskRunner__update_task("not_a_task_result")
    assert result is None


def test_run_once_with_no_task(mocker):
    worker = get_valid_worker()
    mock_clear_cache = mocker.patch.object(worker, "clear_task_definition_name_cache")
    mocker.patch.object(TaskResourceApi, "poll", return_value=None)

    task_runner = TaskRunner(worker=worker)
    task_runner.run_once()

    mock_clear_cache.assert_called_once()


def test_run_once_with_task_no_id(mocker):
    worker = get_valid_worker()
    mock_clear_cache = mocker.patch.object(worker, "clear_task_definition_name_cache")
    task_without_id = Task(workflow_instance_id="test_workflow")
    mocker.patch.object(TaskResourceApi, "poll", return_value=task_without_id)

    task_runner = TaskRunner(worker=worker)
    task_runner.run_once()

    mock_clear_cache.assert_called_once()
