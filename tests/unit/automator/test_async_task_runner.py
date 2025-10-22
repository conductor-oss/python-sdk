import logging
from datetime import datetime
import time

import pytest
from requests.structures import CaseInsensitiveDict

from conductor.asyncio_client.adapters.models.task_exec_log_adapter import TaskExecLogAdapter
from conductor.asyncio_client.automator.task_runner import AsyncTaskRunner
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters.api.task_resource_api import TaskResourceApiAdapter
from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter
from conductor.asyncio_client.adapters.models.task_result_adapter import TaskResultAdapter
from conductor.shared.http.enums import TaskResultStatus
from conductor.asyncio_client.worker.worker_interface import DEFAULT_POLLING_INTERVAL
from tests.unit.resources.workers import ClassWorker2, FaultyExecutionWorker


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def get_valid_task_runner_with_worker_config(worker_config=None):
    return AsyncTaskRunner(configuration=Configuration(), worker=get_valid_worker())


def get_valid_task_runner_with_worker_config_and_domain(domain):
    return AsyncTaskRunner(
        configuration=Configuration(), worker=get_valid_worker(domain=domain)
    )


def get_valid_task_runner_with_worker_config_and_poll_interval(poll_interval):
    return AsyncTaskRunner(
        configuration=Configuration(),
        worker=get_valid_worker(poll_interval=poll_interval),
    )


def get_valid_task_runner():
    return AsyncTaskRunner(configuration=Configuration(), worker=get_valid_worker())


def get_valid_roundrobin_task_runner():
    return AsyncTaskRunner(
        configuration=Configuration(), worker=get_valid_multi_task_worker()
    )


def get_valid_task():
    return TaskAdapter(
        task_id="VALID_TASK_ID", workflow_instance_id="VALID_WORKFLOW_INSTANCE_ID"
    )


def get_valid_task_result():
    return TaskResultAdapter(
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
    return ClassWorker2(["task1", "task2", "task3", "task4", "task5", "task6"])


def get_valid_worker(domain=None, poll_interval=None):
    cw = ClassWorker2("task")
    cw.domain = domain
    cw.poll_interval = poll_interval
    return cw


def test_initialization_with_invalid_worker():
    with pytest.raises(Exception, match="Invalid worker"):
        AsyncTaskRunner(
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


@pytest.mark.asyncio
async def test_run_once(mocker):
    expected_time = get_valid_worker().get_polling_interval_in_seconds()
    mocker.patch.object(TaskResourceApiAdapter, "poll", return_value=get_valid_task())
    mocker.patch.object(
        TaskResourceApiAdapter, "update_task", return_value="VALID_UPDATE_TASK_RESPONSE"
    )
    task_runner = get_valid_task_runner()
    start_time = time.time()
    await task_runner.run_once()
    finish_time = time.time()
    spent_time = finish_time - start_time
    assert spent_time > expected_time


@pytest.mark.asyncio
async def test_run_once_roundrobin(mocker):
    mocker.patch.object(TaskResourceApiAdapter, "poll", return_value=get_valid_task())
    mock_update_task = mocker.patch.object(TaskResourceApiAdapter, "update_task")
    mock_update_task.return_value = "VALID_UPDATE_TASK_RESPONSE"
    task_runner = get_valid_roundrobin_task_runner()
    for i in range(6):
        current_task_name = task_runner.worker.get_task_definition_name()
        await task_runner.run_once()
        assert (
            current_task_name
            == ["task1", "task2", "task3", "task4", "task5", "task6"][i]
        )


@pytest.mark.asyncio
async def test_poll_task(mocker):
    expected_task = get_valid_task()
    mocker.patch.object(TaskResourceApiAdapter, "poll", return_value=get_valid_task())
    task_runner = get_valid_task_runner()
    task = await task_runner._AsyncTaskRunner__poll_task()
    assert task == expected_task


@pytest.mark.asyncio
async def test_poll_task_with_faulty_task_api(mocker):
    expected_task = None
    mocker.patch.object(TaskResourceApiAdapter, "poll", side_effect=Exception())
    task_runner = get_valid_task_runner()
    task = await task_runner._AsyncTaskRunner__poll_task()
    assert task == expected_task


@pytest.mark.asyncio
async def test_execute_task_with_invalid_task():
    task_runner = get_valid_task_runner()
    task_result = await task_runner._AsyncTaskRunner__execute_task(None)
    assert task_result is None


@pytest.mark.asyncio
async def test_execute_task_with_faulty_execution_worker(mocker):
    worker = FaultyExecutionWorker("task")
    task_runner = AsyncTaskRunner(configuration=Configuration(), worker=worker)
    task = get_valid_task()
    task_result = await task_runner._AsyncTaskRunner__execute_task(task)

    # Check the task result properties
    assert task_result.task_id == "VALID_TASK_ID"
    assert task_result.workflow_instance_id == "VALID_WORKFLOW_INSTANCE_ID"
    assert task_result.worker_id == worker.get_identity()
    assert task_result.status == TaskResultStatus.FAILED
    assert task_result.reason_for_incompletion == "faulty execution"
    assert task_result.logs is not None
    assert len(task_result.logs) == 1

    # Check the log entry
    log_entry = task_result.logs[0]
    assert log_entry.task_id == "VALID_TASK_ID"
    assert log_entry.log is not None
    assert "faulty execution" in log_entry.log
    assert log_entry.created_time is not None


@pytest.mark.asyncio
async def test_execute_task():
    expected_task_result = get_valid_task_result()
    worker = get_valid_worker()
    task_runner = AsyncTaskRunner(configuration=Configuration(), worker=worker)
    task = get_valid_task()
    task_result = await task_runner._AsyncTaskRunner__execute_task(task)
    assert task_result == expected_task_result


@pytest.mark.asyncio
async def test_update_task_with_invalid_task_result():
    expected_response = None
    task_runner = get_valid_task_runner()
    response = await task_runner._AsyncTaskRunner__update_task(None)
    assert response == expected_response


@pytest.mark.asyncio
async def test_update_task_with_faulty_task_api(mocker):
    mocker.patch("asyncio.sleep", return_value=None)
    mocker.patch.object(TaskResourceApiAdapter, "update_task", side_effect=Exception())
    task_runner = get_valid_task_runner()
    task_result = get_valid_task_result()
    response = await task_runner._AsyncTaskRunner__update_task(task_result)
    assert response is None


@pytest.mark.asyncio
async def test_update_task(mocker):
    mocker.patch.object(
        TaskResourceApiAdapter, "update_task", return_value="VALID_UPDATE_TASK_RESPONSE"
    )
    task_runner = get_valid_task_runner()
    task_result = get_valid_task_result()
    response = await task_runner._AsyncTaskRunner__update_task(task_result)
    assert response == "VALID_UPDATE_TASK_RESPONSE"


@pytest.mark.asyncio
async def test_wait_for_polling_interval_with_faulty_worker(mocker):
    expected_exception = Exception("Failed to get polling interval")
    mocker.patch.object(
        ClassWorker2, "get_polling_interval_in_seconds", side_effect=expected_exception
    )
    task_runner = get_valid_task_runner()
    with pytest.raises(Exception, match="Failed to get polling interval"):
        await task_runner._AsyncTaskRunner__wait_for_polling_interval()


@pytest.mark.asyncio
async def test_wait_for_polling_interval():
    expected_time = get_valid_worker().get_polling_interval_in_seconds()
    task_runner = get_valid_task_runner()
    start_time = time.time()
    await task_runner._AsyncTaskRunner__wait_for_polling_interval()
    finish_time = time.time()
    spent_time = finish_time - start_time
    assert spent_time > expected_time
