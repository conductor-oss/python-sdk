import json
import logging

import pytest

from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters.api.task_resource_api import TaskResourceApiAdapter
from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter
from conductor.asyncio_client.adapters.models.task_result_adapter import TaskResultAdapter
from conductor.asyncio_client.adapters.models.task_exec_log_adapter import TaskExecLogAdapter
from conductor.asyncio_client.adapters.models.poll_data_adapter import PollDataAdapter
from conductor.asyncio_client.adapters.models.search_result_task_summary_adapter import SearchResultTaskSummaryAdapter
from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_task_client import OrkesTaskClient

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
def task_adapter():
    return TaskAdapter(
        task_type="SIMPLE",
        task_def_name=TASK_NAME,
        reference_task_name="simple_task_ref_1",
        task_id=TASK_ID,
    )


@pytest.fixture
def task_result_adapter():
    return TaskResultAdapter(
        task_id=TASK_ID,
        status="COMPLETED",
        output={"result": "success"},
        workflow_instance_id=TASK_ID
    )


@pytest.fixture
def task_exec_log_adapter():
    return TaskExecLogAdapter(
        log="Test log message",
        task_id=TASK_ID
    )


@pytest.fixture
def poll_data_adapter():
    return PollDataAdapter(
        queue_size=5,
        worker_id=WORKER_ID,
        last_poll_time=1698093000000
    )


@pytest.mark.asyncio
async def test_init(task_client):
    message = "task_api is not of type TaskResourceApiAdapter"
    assert isinstance(task_client.task_api, TaskResourceApiAdapter), message


@pytest.mark.asyncio
async def test_poll_for_task(mocker, task_client, task_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "poll")
    mock.return_value = task_adapter
    result = await task_client.poll_for_task(TASK_NAME, WORKER_ID)
    mock.assert_called_with(tasktype=TASK_NAME, workerid=WORKER_ID, domain=None)
    assert result == task_adapter


@pytest.mark.asyncio
async def test_poll_for_task_with_domain(mocker, task_client, task_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "poll")
    mock.return_value = task_adapter
    result = await task_client.poll_for_task(TASK_NAME, WORKER_ID, DOMAIN)
    mock.assert_called_with(tasktype=TASK_NAME, workerid=WORKER_ID, domain=DOMAIN)
    assert result == task_adapter


@pytest.mark.asyncio
async def test_poll_for_task_no_tasks(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "poll")
    mock.return_value = None
    result = await task_client.poll_for_task(TASK_NAME, WORKER_ID)
    mock.assert_called_with(tasktype=TASK_NAME, workerid=WORKER_ID, domain=None)
    assert result is None


@pytest.mark.asyncio
async def test_poll_for_task_batch(mocker, task_client, task_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "batch_poll")
    mock.return_value = [task_adapter]
    result = await task_client.poll_for_task_batch(TASK_NAME, WORKER_ID, 3, 200)
    mock.assert_called_with(
        tasktype=TASK_NAME,
        workerid=WORKER_ID,
        count=3,
        timeout=200,
        domain=None
    )
    assert result == [task_adapter]


@pytest.mark.asyncio
async def test_poll_for_task_batch_with_domain(mocker, task_client, task_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "batch_poll")
    mock.return_value = [task_adapter]
    result = await task_client.poll_for_task_batch(TASK_NAME, WORKER_ID, 3, 200, DOMAIN)
    mock.assert_called_with(
        tasktype=TASK_NAME,
        workerid=WORKER_ID,
        count=3,
        timeout=200,
        domain=DOMAIN
    )
    assert result == [task_adapter]


@pytest.mark.asyncio
async def test_get_task(mocker, task_client, task_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_task")
    mock.return_value = task_adapter
    result = await task_client.get_task(TASK_ID)
    mock.assert_called_with(task_id=TASK_ID)
    assert result == task_adapter


@pytest.mark.asyncio
async def test_get_task_non_existent(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_task")
    error_body = {"status": 404, "message": "Task not found"}
    mock.side_effect = ApiException(status=404, body=json.dumps(error_body))
    with pytest.raises(ApiException):
        await task_client.get_task(TASK_ID)
    mock.assert_called_with(task_id=TASK_ID)


@pytest.mark.asyncio
async def test_update_task(mocker, task_client, task_result_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "update_task")
    mock.return_value = "updated"
    result = await task_client.update_task(task_result_adapter)
    mock.assert_called_with(task_result=task_result_adapter)
    assert result == "updated"


@pytest.mark.asyncio
async def test_update_task_by_ref_name(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "update_task1")
    mock.return_value = "updated"
    status = "COMPLETED"
    request_body = {"result": {"output": "success"}}
    result = await task_client.update_task_by_ref_name("wf_id", "test_task_ref_name", status, request_body)
    mock.assert_called_with(
        workflow_id="wf_id",
        task_ref_name="test_task_ref_name",
        status=status,
        request_body=request_body,
        workerid=None
    )
    assert result == "updated"


@pytest.mark.asyncio
async def test_update_task_by_ref_name_with_worker_id(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "update_task1")
    mock.return_value = "updated"
    status = "COMPLETED"
    request_body = {"result": {"output": "success"}}
    result = await task_client.update_task_by_ref_name("wf_id", "test_task_ref_name", status, request_body, "worker_id")
    mock.assert_called_with(
        workflow_id="wf_id",
        task_ref_name="test_task_ref_name",
        status=status,
        request_body=request_body,
        workerid="worker_id"
    )
    assert result == "updated"


@pytest.mark.asyncio
async def test_update_task_sync(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "update_task_sync")
    workflow_id = "test_wf_id"
    workflow = WorkflowAdapter(workflow_id=workflow_id)
    mock.return_value = workflow
    status = "COMPLETED"
    request_body = {"result": {"output": "success"}}
    result = await task_client.update_task_sync(workflow_id, "test_task_ref_name", status, request_body)
    mock.assert_called_with(
        workflow_id=workflow_id,
        task_ref_name="test_task_ref_name",
        status=status,
        request_body=request_body,
        workerid=None
    )
    assert result == workflow


@pytest.mark.asyncio
async def test_update_task_sync_with_worker_id(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "update_task_sync")
    workflow_id = "test_wf_id"
    workflow = WorkflowAdapter(workflow_id=workflow_id)
    mock.return_value = workflow
    status = "COMPLETED"
    request_body = {"result": {"output": "success"}}
    result = await task_client.update_task_sync(workflow_id, "test_task_ref_name", status, request_body, "worker_id")
    mock.assert_called_with(
        workflow_id=workflow_id,
        task_ref_name="test_task_ref_name",
        status=status,
        request_body=request_body,
        workerid="worker_id"
    )
    assert result == workflow


@pytest.mark.asyncio
async def test_get_task_queue_sizes(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "all")
    expected_sizes = {TASK_NAME: 4, TASK_NAME_2: 2}
    mock.return_value = expected_sizes
    result = await task_client.get_task_queue_sizes()
    assert mock.called
    assert result == expected_sizes


@pytest.mark.asyncio
async def test_get_task_queue_sizes_verbose(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "all_verbose")
    expected_verbose = {
        TASK_NAME: {
            "workers": {"worker1": 2},
            "queue": {"pending": 4}
        }
    }
    mock.return_value = expected_verbose
    result = await task_client.get_task_queue_sizes_verbose()
    assert mock.called
    assert result == expected_verbose


@pytest.mark.asyncio
async def test_get_all_poll_data(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_all_poll_data")
    expected_data = {
        TASK_NAME: {
            "queue_size": 5,
            "worker_count": 2
        }
    }
    mock.return_value = expected_data
    result = await task_client.get_all_poll_data()
    assert mock.called
    assert result == expected_data


@pytest.mark.asyncio
async def test_get_poll_data(mocker, task_client, poll_data_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_poll_data")
    mock.return_value = [poll_data_adapter]
    result = await task_client.get_poll_data(TASK_NAME)
    mock.assert_called_with(task_type=TASK_NAME)
    assert result == [poll_data_adapter]


@pytest.mark.asyncio
async def test_get_task_logs(mocker, task_client, task_exec_log_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_task_logs")
    mock.return_value = [task_exec_log_adapter]
    result = await task_client.get_task_logs(TASK_ID)
    mock.assert_called_with(task_id=TASK_ID)
    assert result == [task_exec_log_adapter]


@pytest.mark.asyncio
async def test_log_task(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "log")
    log_message = "Test log message"
    await task_client.log_task(TASK_ID, log_message)
    mock.assert_called_with(task_id=TASK_ID, body=log_message)


@pytest.mark.asyncio
async def test_search_tasks(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "search1")
    expected_result = SearchResultTaskSummaryAdapter(total_hits=1)
    mock.return_value = expected_result
    result = await task_client.search_tasks(start=0, size=10, query="status:COMPLETED")
    mock.assert_called_with(
        start=0,
        size=10,
        sort=None,
        free_text=None,
        query="status:COMPLETED"
    )
    assert result == expected_result


@pytest.mark.asyncio
async def test_requeue_pending_tasks(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "requeue_pending_task")
    mock.return_value = "requeued"
    result = await task_client.requeue_pending_tasks(TASK_NAME)
    mock.assert_called_with(task_type=TASK_NAME)
    assert result == "requeued"


@pytest.mark.asyncio
async def test_get_queue_size_for_task_type(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "size")
    mock.return_value = {TASK_NAME: 4}
    result = await task_client.get_queue_size_for_task_type(TASK_NAME)
    mock.assert_called_with(task_type=TASK_NAME)
    assert result.get(TASK_NAME, 0) == 4


@pytest.mark.asyncio
async def test_get_queue_size_for_task_type_empty(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "size")
    mock.return_value = {}
    result = await task_client.get_queue_size_for_task_type(TASK_NAME)
    mock.assert_called_with(task_type=TASK_NAME)
    assert result.get(TASK_NAME, 0) == 0


@pytest.mark.asyncio
async def test_poll_for_task_api_exception(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "poll")
    mock.side_effect = ApiException(status=500, body="Internal error")
    with pytest.raises(ApiException):
        await task_client.poll_for_task(TASK_NAME, WORKER_ID)
    mock.assert_called_with(tasktype=TASK_NAME, workerid=WORKER_ID, domain=None)


@pytest.mark.asyncio
async def test_get_task_api_exception(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_task")
    mock.side_effect = ApiException(status=404, body="Task not found")
    with pytest.raises(ApiException):
        await task_client.get_task(TASK_ID)
    mock.assert_called_with(task_id=TASK_ID)


@pytest.mark.asyncio
async def test_update_task_api_exception(mocker, task_client, task_result_adapter):
    mock = mocker.patch.object(TaskResourceApiAdapter, "update_task")
    mock.side_effect = ApiException(status=400, body="Bad request")
    with pytest.raises(ApiException):
        await task_client.update_task(task_result_adapter)
    mock.assert_called_with(task_result=task_result_adapter)


@pytest.mark.asyncio
async def test_get_task_logs_api_exception(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_task_logs")
    mock.side_effect = ApiException(status=404, body="Task not found")
    with pytest.raises(ApiException):
        await task_client.get_task_logs(TASK_ID)
    mock.assert_called_with(task_id=TASK_ID)


@pytest.mark.asyncio
async def test_log_task_api_exception(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "log")
    mock.side_effect = ApiException(status=400, body="Bad request")
    with pytest.raises(ApiException):
        await task_client.log_task(TASK_ID, "Test log")
    mock.assert_called_with(task_id=TASK_ID, body="Test log")


@pytest.mark.asyncio
async def test_search_tasks_api_exception(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "search1")
    mock.side_effect = ApiException(status=500, body="Internal error")
    with pytest.raises(ApiException):
        await task_client.search_tasks()
    mock.assert_called_with(
        start=0,
        size=100,
        sort=None,
        free_text=None,
        query=None
    )


@pytest.mark.asyncio
async def test_poll_for_task_batch_empty(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "batch_poll")
    mock.return_value = []
    result = await task_client.poll_for_task_batch(TASK_NAME, WORKER_ID, 3, 200)
    mock.assert_called_with(
        tasktype=TASK_NAME,
        workerid=WORKER_ID,
        count=3,
        timeout=200,
        domain=None
    )
    assert result == []


@pytest.mark.asyncio
async def test_get_task_logs_empty(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_task_logs")
    mock.return_value = []
    result = await task_client.get_task_logs(TASK_ID)
    mock.assert_called_with(task_id=TASK_ID)
    assert result == []


@pytest.mark.asyncio
async def test_get_poll_data_empty(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_poll_data")
    mock.return_value = []
    result = await task_client.get_poll_data(TASK_NAME)
    mock.assert_called_with(task_type=TASK_NAME)
    assert result == []


@pytest.mark.asyncio
async def test_search_tasks_with_parameters(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "search1")
    expected_result = SearchResultTaskSummaryAdapter(total_hits=5)
    mock.return_value = expected_result
    result = await task_client.search_tasks(
        start=10,
        size=20,
        sort="status:ASC",
        free_text="completed",
        query="workflowId:test_workflow"
    )
    mock.assert_called_with(
        start=10,
        size=20,
        sort="status:ASC",
        free_text="completed",
        query="workflowId:test_workflow"
    )
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_all_poll_data_with_parameters(mocker, task_client):
    mock = mocker.patch.object(TaskResourceApiAdapter, "get_all_poll_data")
    expected_data = {"task1": {"queue_size": 5}}
    mock.return_value = expected_data
    result = await task_client.get_all_poll_data(
        worker_size=10,
        worker_opt="desc",
        queue_size=5,
        queue_opt="asc",
        last_poll_time_size=10,
        last_poll_time_opt="desc"
    )
    mock.assert_called_with(
        worker_size=10,
        worker_opt="desc",
        queue_size=5,
        queue_opt="asc",
        last_poll_time_size=10,
        last_poll_time_opt="desc"
    )
    assert result == expected_data
