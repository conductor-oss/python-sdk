import json
import logging
import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.http.models.workflow import Workflow
from conductor.client.http.rest import ApiException
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.workflow.task.task_type import TaskType

TASK_NAME = "ut_task"
TASK_ID = "task_id_1"
TASK_NAME_2 = "ut_task_2"
WORKER_ID = "ut_worker_id"
DOMAIN = "test_domain"


@pytest.fixture(scope="module")
def task_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesTaskClient(configuration)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def tasks():
    return [
        Task(
            task_type=TaskType.SIMPLE,
            task_def_name=TASK_NAME,
            reference_task_name="simple_task_ref_1",
            task_id=TASK_ID,
        ),
        Task(
            task_type=TaskType.SIMPLE,
            task_def_name=TASK_NAME,
            reference_task_name="simple_task_ref_2",
            task_id="task_id_2",
        ),
        Task(
            task_type=TaskType.SIMPLE,
            task_def_name=TASK_NAME,
            reference_task_name="simple_task_ref_3",
            task_id="task_id_3",
        ),
    ]


def test_init(task_client):
    message = "taskResourceApi is not of type TaskResourceApi"
    assert isinstance(task_client.taskResourceApi, TaskResourceApi), message


def test_poll_task(mocker, task_client, tasks):
    mock = mocker.patch.object(TaskResourceApi, "poll")
    mock.return_value = tasks[0]
    polled_task = task_client.poll_task(TASK_NAME)
    mock.assert_called_with(TASK_NAME)
    assert polled_task == tasks[0]


def test_poll_task_with_worker_and_domain(mocker, task_client, tasks):
    mock = mocker.patch.object(TaskResourceApi, "poll")
    mock.return_value = tasks[0]
    polled_task = task_client.poll_task(TASK_NAME, WORKER_ID, DOMAIN)
    mock.assert_called_with(TASK_NAME, workerid=WORKER_ID, domain=DOMAIN)
    assert polled_task == tasks[0]


def test_poll_task_no_tasks(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "poll")
    mock.return_value = None
    polled_task = task_client.poll_task(TASK_NAME)
    mock.assert_called_with(TASK_NAME)
    assert polled_task is None


def test_batch_poll_tasks(mocker, task_client, tasks):
    mock = mocker.patch.object(TaskResourceApi, "batch_poll")
    mock.return_value = tasks
    polled_tasks = task_client.batch_poll_tasks(TASK_NAME, WORKER_ID, 3, 200)
    mock.assert_called_with(TASK_NAME, workerid=WORKER_ID, count=3, timeout=200)
    assert len(polled_tasks) == len(tasks)


def test_batch_poll_tasks_in_domain(mocker, task_client, tasks):
    mock = mocker.patch.object(TaskResourceApi, "batch_poll")
    mock.return_value = tasks
    polled_tasks = task_client.batch_poll_tasks(TASK_NAME, WORKER_ID, 3, 200, DOMAIN)
    mock.assert_called_with(
        TASK_NAME, workerid=WORKER_ID, domain=DOMAIN, count=3, timeout=200
    )
    assert len(polled_tasks) == len(tasks)


def test_get_task(mocker, task_client, tasks):
    mock = mocker.patch.object(TaskResourceApi, "get_task")
    mock.return_value = tasks[0]
    task = task_client.get_task(TASK_ID)
    mock.assert_called_with(TASK_ID)
    assert task.task_id == TASK_ID


def test_get_task_non_existent(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "get_task")
    error_body = {"status": 404, "message": "Task not found"}
    mock.side_effect = mocker.MagicMock(
        side_effect=ApiException(status=404, body=json.dumps(error_body))
    )
    with pytest.raises(ApiException):
        task_client.get_task(TASK_ID)
        mock.assert_called_with(TASK_ID)


def test_update_task(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "update_task")
    task_result_status = TaskResult(task_id=TASK_ID, status=TaskResultStatus.COMPLETED)
    task_client.update_task(task_result_status)
    mock.assert_called_with(task_result_status)


def test_update_task_by_ref_name(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "update_task1")
    status = TaskResultStatus.COMPLETED
    output = {"a": 56}
    task_client.update_task_by_ref_name("wf_id", "test_task_ref_name", status, output)
    mock.assert_called_with({"result": output}, "wf_id", "test_task_ref_name", status)


def test_update_task_by_ref_name_with_worker_id(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "update_task1")
    status = TaskResultStatus.COMPLETED
    output = {"a": 56}
    task_client.update_task_by_ref_name(
        "wf_id", "test_task_ref_name", status, output, "worker_id"
    )
    mock.assert_called_with(
        {"result": output}, "wf_id", "test_task_ref_name", status, workerid="worker_id"
    )


def test_update_task_sync(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "update_task_sync")
    workflow_id = "test_wf_id"
    workflow = Workflow(workflow_id=workflow_id)
    mock.return_value = workflow
    status = TaskResultStatus.COMPLETED
    output = {"a": 56}
    returned_workflow = task_client.update_task_sync(
        workflow_id, "test_task_ref_name", status, output
    )
    mock.assert_called_with(output, workflow_id, "test_task_ref_name", status)
    assert returned_workflow == workflow


def test_update_task_sync_with_worker_id(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "update_task_sync")
    workflow_id = "test_wf_id"
    workflow = Workflow(workflow_id=workflow_id)
    mock.return_value = workflow
    status = TaskResultStatus.COMPLETED
    output = {"a": 56}
    returned_workflow = task_client.update_task_sync(
        workflow_id, "test_task_ref_name", status, output, "worker_id"
    )
    mock.assert_called_with(
        output, workflow_id, "test_task_ref_name", status, workerid="worker_id"
    )
    assert returned_workflow == workflow


def test_get_queue_size_for_task(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "size")
    mock.return_value = {TASK_NAME: 4}
    size = task_client.get_queue_size_for_task(TASK_NAME)
    mock.assert_called_with(task_type=[TASK_NAME])
    assert size == 4


def test_get_queue_size_for_task_empty(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "size")
    mock.return_value = {}
    size = task_client.get_queue_size_for_task(TASK_NAME)
    mock.assert_called_with(task_type=[TASK_NAME])
    assert size == 0


def test_add_task_log(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "log")
    log_message = "Test log"
    task_client.add_task_log(TASK_ID, log_message)
    mock.assert_called_with(log_message, TASK_ID)


def test_get_task_logs(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApi, "get_task_logs")
    task_exec_log1 = TaskExecLog("Test log 1", TASK_ID)
    task_exec_log2 = TaskExecLog("Test log 2", TASK_ID)
    mock.return_value = [task_exec_log1, task_exec_log2]
    logs = task_client.get_task_logs(TASK_ID)
    mock.assert_called_with(TASK_ID)
    assert len(logs) == 2
