import json
import logging

import pytest

from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters.api.scheduler_resource_api import SchedulerResourceApiAdapter
from conductor.asyncio_client.adapters.models.save_schedule_request_adapter import SaveScheduleRequestAdapter
from conductor.asyncio_client.adapters.models.search_result_workflow_schedule_execution_model_adapter import (
    SearchResultWorkflowScheduleExecutionModelAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_schedule_adapter import WorkflowScheduleAdapter
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.orkes.orkes_scheduler_client import OrkesSchedulerClient

SCHEDULE_NAME = "ut_schedule"
WORKFLOW_NAME = "ut_wf"
ERROR_BODY = '{"message":"No such schedule found by name"}'


@pytest.fixture(scope="module")
def scheduler_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesSchedulerClient(configuration)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def workflow_schedule():
    return WorkflowScheduleAdapter(name=SCHEDULE_NAME)


@pytest.fixture
def save_schedule_request():
    start_req = StartWorkflowRequestAdapter(name="test_workflow")
    return SaveScheduleRequestAdapter(
        name=SCHEDULE_NAME,
        cron_expression="0 0 * * *",
        start_workflow_request=start_req
    )


@pytest.mark.asyncio
async def test_init(scheduler_client):
    message = "scheduler_api is not of type SchedulerResourceApiAdapter"
    assert isinstance(
        scheduler_client.scheduler_api, SchedulerResourceApiAdapter
    ), message


@pytest.mark.asyncio
async def test_save_schedule(mocker, scheduler_client, save_schedule_request):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "save_schedule")
    await scheduler_client.save_schedule(save_schedule_request)
    assert mock.called
    mock.assert_called_with(save_schedule_request)


@pytest.mark.asyncio
async def test_get_schedule(mocker, scheduler_client, workflow_schedule):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "get_schedule")
    mock.return_value = workflow_schedule
    schedule = await scheduler_client.get_schedule(SCHEDULE_NAME)
    assert schedule == workflow_schedule
    assert mock.called
    mock.assert_called_with(SCHEDULE_NAME)


@pytest.mark.asyncio
async def test_get_schedule_non_existing(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "get_schedule")
    error_body = {"status": 404, "message": "Schedule not found"}
    mock.side_effect = mocker.MagicMock(
        side_effect=ApiException(status=404, body=json.dumps(error_body))
    )
    with pytest.raises(ApiException):
        await scheduler_client.get_schedule("WRONG_SCHEDULE")


@pytest.mark.asyncio
async def test_get_all_schedules(mocker, scheduler_client, workflow_schedule):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "get_all_schedules")
    mock.return_value = [workflow_schedule]
    schedules = await scheduler_client.get_all_schedules()
    assert schedules == [workflow_schedule]
    assert mock.called


@pytest.mark.asyncio
async def test_get_all_schedules_with_workflow_name(
    mocker, scheduler_client, workflow_schedule
):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "get_all_schedules")
    mock.return_value = [workflow_schedule]
    schedules = await scheduler_client.get_all_schedules(WORKFLOW_NAME)
    assert schedules == [workflow_schedule]
    mock.assert_called_with(workflow_name=WORKFLOW_NAME)


@pytest.mark.asyncio
async def test_get_next_few_schedule_execution_times(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "get_next_few_schedules")
    expected_next_few_schedule_execution_times = 3
    cron_expression = "0 */5 * ? * *"
    mock.return_value = [1698093000000, 1698093300000, 1698093600000]
    times = await scheduler_client.get_next_few_schedules(cron_expression)
    assert len(times) == expected_next_few_schedule_execution_times
    mock.assert_called_with(
        cron_expression=cron_expression,
        schedule_start_time=None,
        schedule_end_time=None,
        limit=None
    )


@pytest.mark.asyncio
async def test_get_next_few_schedule_execution_times_with_optional_params(
    mocker, scheduler_client
):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "get_next_few_schedules")
    expected_next_few_schedule_execution_times = 2
    cron_expression = "0 */5 * ? * *"
    mock.return_value = [1698093300000, 1698093600000]
    times = await scheduler_client.get_next_few_schedules(
        cron_expression, 1698093300000, 1698093600000, 2
    )
    assert len(times) == expected_next_few_schedule_execution_times
    mock.assert_called_with(
        cron_expression=cron_expression,
        schedule_start_time=1698093300000,
        schedule_end_time=1698093600000,
        limit=2,
    )


@pytest.mark.asyncio
async def test_delete_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "delete_schedule")
    await scheduler_client.delete_schedule(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)


@pytest.mark.asyncio
async def test_pause_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "pause_schedule")
    await scheduler_client.pause_schedule(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)


@pytest.mark.asyncio
async def test_pause_all_schedules(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "pause_all_schedules")
    await scheduler_client.pause_all_schedules()
    assert mock.called


@pytest.mark.asyncio
async def test_resume_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "resume_schedule")
    await scheduler_client.resume_schedule(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)


@pytest.mark.asyncio
async def test_resume_all_schedules(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "resume_all_schedules")
    await scheduler_client.resume_all_schedules()
    assert mock.called


@pytest.mark.asyncio
async def test_requeue_all_execution_records(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "requeue_all_execution_records")
    await scheduler_client.requeue_all_execution_records()
    assert mock.called


@pytest.mark.asyncio
async def test_search_schedule_executions(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "search_v2")
    srw = SearchResultWorkflowScheduleExecutionModelAdapter(total_hits=2)
    mock.return_value = srw
    start = 1698093300000
    sort = "name&sort=workflowId:DESC"
    free_text = "abc"
    query = "workflowId=abc"
    search_result = await scheduler_client.search_schedules(
        start, 2, sort, free_text, query
    )
    mock.assert_called_with(
        start=start,
        size=2,
        sort=sort,
        free_text=free_text,
        query=query,
    )
    assert search_result == srw


@pytest.mark.asyncio
async def test_put_tag_for_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "put_tag_for_schedule")
    tag1 = TagAdapter(key="tag1", value="val1")
    tag2 = TagAdapter(key="tag2", value="val2")
    tags = [tag1, tag2]
    await scheduler_client.put_tag_for_schedule(SCHEDULE_NAME, tags)
    mock.assert_called_with(SCHEDULE_NAME, tags)


@pytest.mark.asyncio
async def test_get_tags_for_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "get_tags_for_schedule")
    expected_tags_len = 2
    tag1 = TagAdapter(key="tag1", value="val1")
    tag2 = TagAdapter(key="tag2", value="val2")
    mock.return_value = [tag1, tag2]
    tags = await scheduler_client.get_tags_for_schedule(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)
    assert len(tags) == expected_tags_len


@pytest.mark.asyncio
async def test_delete_tag_for_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApiAdapter, "delete_tag_for_schedule")
    tag1 = TagAdapter(key="tag1", value="val1")
    tag2 = TagAdapter(key="tag2", value="val2")
    tags = [tag1, tag2]
    await scheduler_client.delete_tag_for_schedule(SCHEDULE_NAME, tags)
    mock.assert_called_with(SCHEDULE_NAME, tags)
