import json
import logging

import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.adapters.api import SchedulerResourceApi
from conductor.client.adapters.models.save_schedule_request_adapter import SaveScheduleRequestAdapter as SaveScheduleRequest
from conductor.client.adapters.models.search_result_workflow_schedule_execution_model_adapter import SearchResultWorkflowScheduleExecutionModelAdapter as SearchResultWorkflowScheduleExecutionModel
from conductor.client.adapters.models.workflow_schedule_adapter import WorkflowScheduleAdapter as WorkflowSchedule
from conductor.client.http.rest import ApiException
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient

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
    return WorkflowSchedule(name=SCHEDULE_NAME)


@pytest.fixture
def save_schedule_request():
    return SaveScheduleRequest(name=SCHEDULE_NAME)


def test_init(scheduler_client):
    message = "schedulerResourceApi is not of type SchedulerResourceApi"
    assert isinstance(
        scheduler_client.schedulerResourceApi, SchedulerResourceApi
    ), message


def test_save_schedule(mocker, scheduler_client, save_schedule_request):
    mock = mocker.patch.object(SchedulerResourceApi, "save_schedule")
    scheduler_client.save_schedule(save_schedule_request)
    assert mock.called
    mock.assert_called_with(save_schedule_request)


def test_get_schedule(mocker, scheduler_client, workflow_schedule):
    mock = mocker.patch.object(SchedulerResourceApi, "get_schedule")
    mock.return_value = workflow_schedule
    schedule = scheduler_client.get_schedule(SCHEDULE_NAME)
    assert schedule == workflow_schedule
    assert mock.called
    mock.assert_called_with(SCHEDULE_NAME)


def test_get_schedule_non_existing(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "get_schedule")
    error_body = {"status": 404, "message": "Schedule not found"}
    mock.side_effect = mocker.MagicMock(
        side_effect=ApiException(status=404, body=json.dumps(error_body))
    )
    with pytest.raises(ApiException):
        scheduler_client.get_schedule("WRONG_SCHEDULE")


def test_get_all_schedules(mocker, scheduler_client, workflow_schedule):
    mock = mocker.patch.object(SchedulerResourceApi, "get_all_schedules")
    mock.return_value = [workflow_schedule]
    schedules = scheduler_client.get_all_schedules()
    assert schedules == [workflow_schedule]
    assert mock.called


def test_get_all_schedules_with_workflow_name(
    mocker, scheduler_client, workflow_schedule
):
    mock = mocker.patch.object(SchedulerResourceApi, "get_all_schedules")
    mock.return_value = [workflow_schedule]
    schedules = scheduler_client.get_all_schedules(WORKFLOW_NAME)
    assert schedules == [workflow_schedule]
    mock.assert_called_with(workflow_name=WORKFLOW_NAME)


def test_get_next_few_schedule_execution_times(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "get_next_few_schedules")
    expected_next_few_schedule_execution_times = 3
    cron_expression = "0 */5 * ? * *"
    mock.return_value = [1698093000000, 1698093300000, 1698093600000]
    times = scheduler_client.get_next_few_schedule_execution_times(cron_expression)
    assert len(times) == expected_next_few_schedule_execution_times
    mock.assert_called_with(cron_expression)


def test_get_next_few_schedule_execution_times_with_optional_params(
    mocker, scheduler_client
):
    mock = mocker.patch.object(SchedulerResourceApi, "get_next_few_schedules")
    expected_next_few_schedule_execution_times = 2
    cron_expression = "0 */5 * ? * *"
    mock.return_value = [1698093300000, 1698093600000]
    times = scheduler_client.get_next_few_schedule_execution_times(
        cron_expression, 1698093300000, 1698093600000, 2
    )
    assert len(times) == expected_next_few_schedule_execution_times
    mock.assert_called_with(
        cron_expression,
        schedule_start_time=1698093300000,
        schedule_end_time=1698093600000,
        limit=2,
    )


def test_delete_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "delete_schedule")
    scheduler_client.delete_schedule(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)


def test_pause_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "pause_schedule")
    scheduler_client.pause_schedule(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)


def test_pause_all_schedules(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "pause_all_schedules")
    scheduler_client.pause_all_schedules()
    assert mock.called


def test_resume_schedule(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "resume_schedule")
    scheduler_client.resume_schedule(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)


def test_resume_all_schedules(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "resume_all_schedules")
    scheduler_client.resume_all_schedules()
    assert mock.called


def test_requeue_all_execution_records(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "requeue_all_execution_records")
    scheduler_client.requeue_all_execution_records()
    assert mock.called


def test_search_schedule_executions(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "search_v2")
    srw = SearchResultWorkflowScheduleExecutionModel(total_hits=2)
    mock.return_value = srw
    start = 1698093300000
    sort = "name&sort=workflowId:DESC"
    free_text = "abc"
    query = "workflowId=abc"
    search_result = scheduler_client.search_schedule_executions(
        start, 2, sort, free_text, query
    )
    mock.assert_called_with(
        start=start,
        size=2,
        sort=sort,
        freeText=free_text,
        query=query,
    )
    assert search_result == srw


def test_set_scheduler_tags(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "put_tag_for_schedule")
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    tags = [tag1, tag2]
    scheduler_client.set_scheduler_tags(tags, SCHEDULE_NAME)
    mock.assert_called_with(tags, SCHEDULE_NAME)


def test_get_scheduler_tags(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "get_tags_for_schedule")
    expected_tags_len = 2
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    mock.return_value = [tag1, tag2]
    tags = scheduler_client.get_scheduler_tags(SCHEDULE_NAME)
    mock.assert_called_with(SCHEDULE_NAME)
    assert len(tags) == expected_tags_len


def test_delete_scheduler_tags(mocker, scheduler_client):
    mock = mocker.patch.object(SchedulerResourceApi, "delete_tag_for_schedule")
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    tags = [tag1, tag2]
    scheduler_client.delete_scheduler_tags(tags, SCHEDULE_NAME)
    mock.assert_called_with(tags, SCHEDULE_NAME)
