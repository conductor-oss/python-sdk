import json
import logging

import pytest

from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters.api.workflow_resource_api import WorkflowResourceApiAdapter
from conductor.asyncio_client.adapters.models.skip_task_request_adapter import SkipTaskRequestAdapter
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import RerunWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter
from conductor.asyncio_client.adapters.models.workflow_run_adapter import WorkflowRunAdapter
from conductor.asyncio_client.adapters.models.workflow_test_request_adapter import WorkflowTestRequestAdapter
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_workflow_client import OrkesWorkflowClient

WORKFLOW_NAME = "ut_wf"
WORKFLOW_UUID = "ut_wf_uuid"
TASK_NAME = "ut_task"
CORRELATION_ID = "correlation_id"


@pytest.fixture(scope="module")
def workflow_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesWorkflowClient(configuration)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def workflow_input():
    return {"a": "test"}


@pytest.mark.asyncio
async def test_init(workflow_client):
    message = "workflowResourceApi is not of type WorkflowResourceApiAdapter"
    assert isinstance(workflow_client.workflow_api, WorkflowResourceApiAdapter), message


@pytest.mark.asyncio
async def test_start_workflow_by_name(mocker, workflow_client, workflow_input):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = await workflow_client.start_workflow_by_name(WORKFLOW_NAME, workflow_input)
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        request_body=workflow_input,
        version=None,
        correlation_id=None,
        priority=None,
        x_idempotency_key=None,
        x_on_conflict=None,
    )
    assert wf_id == WORKFLOW_UUID


@pytest.mark.asyncio
async def test_start_workflow_by_name_with_version(mocker, workflow_client, workflow_input):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = await workflow_client.start_workflow_by_name(
        WORKFLOW_NAME, workflow_input, version=1
    )
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        request_body=workflow_input,
        version=1,
        correlation_id=None,
        priority=None,
        x_idempotency_key=None,
        x_on_conflict=None,
    )
    assert wf_id == WORKFLOW_UUID


@pytest.mark.asyncio
async def test_start_workflow_by_name_with_correlation_id(
    mocker, workflow_client, workflow_input
):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = await workflow_client.start_workflow_by_name(
        WORKFLOW_NAME, workflow_input, correlation_id=CORRELATION_ID
    )
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        request_body=workflow_input,
        version=None,
        correlation_id=CORRELATION_ID,
        priority=None,
        x_idempotency_key=None,
        x_on_conflict=None,
    )
    assert wf_id == WORKFLOW_UUID


@pytest.mark.asyncio
async def test_start_workflow_by_name_with_version_and_priority(
    mocker, workflow_client, workflow_input
):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = await workflow_client.start_workflow_by_name(
        WORKFLOW_NAME, workflow_input, version=1, priority=1
    )
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        request_body=workflow_input,
        version=1,
        correlation_id=None,
        priority=1,
        x_idempotency_key=None,
        x_on_conflict=None,
    )
    assert wf_id == WORKFLOW_UUID


@pytest.mark.asyncio
async def test_start_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "start_workflow")
    mock.return_value = WORKFLOW_UUID
    start_workflow_req = StartWorkflowRequestAdapter(name=WORKFLOW_NAME)
    wf_id = await workflow_client.start_workflow(start_workflow_req)
    mock.assert_called_with(start_workflow_req)
    assert wf_id == WORKFLOW_UUID


@pytest.mark.asyncio
async def test_execute_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "execute_workflow")
    expected_wf_run = WorkflowRunAdapter()
    mock.return_value = expected_wf_run
    start_workflow_req = StartWorkflowRequestAdapter(name=WORKFLOW_NAME, version=1)
    workflow_run = await workflow_client.execute_workflow(
        start_workflow_req, "request_id", None, 30
    )
    mock.assert_called_with(
        name=WORKFLOW_NAME,
        version=1,
        request_id="request_id",
        start_workflow_request=start_workflow_req,
        wait_until_task_ref=None,
        wait_for_seconds=30,
    )
    assert workflow_run == expected_wf_run


@pytest.mark.asyncio
async def test_pause_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "pause_workflow")
    await workflow_client.pause_workflow(WORKFLOW_UUID)
    mock.assert_called_with(workflow_id=WORKFLOW_UUID)


@pytest.mark.asyncio
async def test_resume_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "resume_workflow")
    await workflow_client.resume_workflow(WORKFLOW_UUID)
    mock.assert_called_with(workflow_id=WORKFLOW_UUID)


@pytest.mark.asyncio
async def test_restart_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "restart")
    await workflow_client.restart_workflow(WORKFLOW_UUID)
    mock.assert_called_with(workflow_id=WORKFLOW_UUID, use_latest_definitions=None)


@pytest.mark.asyncio
async def test_restart_workflow_with_latest_wf_def(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "restart")
    await workflow_client.restart_workflow(WORKFLOW_UUID, use_latest_definitions=True)
    mock.assert_called_with(workflow_id=WORKFLOW_UUID, use_latest_definitions=True)


@pytest.mark.asyncio
async def test_rerun_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "rerun")
    mock.return_value = WORKFLOW_UUID
    rerun_request = RerunWorkflowRequestAdapter()
    wf_id = await workflow_client.rerun_workflow(WORKFLOW_UUID, rerun_request)
    mock.assert_called_with(workflow_id=WORKFLOW_UUID, rerun_workflow_request=rerun_request)
    assert wf_id == WORKFLOW_UUID


@pytest.mark.asyncio
async def test_retry_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "retry")
    await workflow_client.retry_workflow(WORKFLOW_UUID)
    mock.assert_called_with(
        workflow_id=WORKFLOW_UUID,
        resume_subworkflow_tasks=None,
        retry_if_retried_by_parent=None,
    )


@pytest.mark.asyncio
async def test_retry_workflow_with_resume_subworkflow_tasks(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "retry")
    await workflow_client.retry_workflow(WORKFLOW_UUID, resume_subworkflow_tasks=True)
    mock.assert_called_with(
        workflow_id=WORKFLOW_UUID,
        resume_subworkflow_tasks=True,
        retry_if_retried_by_parent=None,
    )


@pytest.mark.asyncio
async def test_terminate_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "terminate1")
    await workflow_client.terminate_workflow(WORKFLOW_UUID)
    mock.assert_called_with(
        workflow_id=WORKFLOW_UUID,
        reason=None,
        trigger_failure_workflow=None,
    )


@pytest.mark.asyncio
async def test_terminate_workflow_with_reason(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "terminate1")
    await workflow_client.terminate_workflow(WORKFLOW_UUID, reason="test_reason")
    mock.assert_called_with(
        workflow_id=WORKFLOW_UUID,
        reason="test_reason",
        trigger_failure_workflow=None,
    )


@pytest.mark.asyncio
async def test_get_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "get_execution_status")
    expected_wf = WorkflowAdapter()
    mock.return_value = expected_wf
    wf = await workflow_client.get_workflow(WORKFLOW_UUID)
    mock.assert_called_with(
        workflow_id=WORKFLOW_UUID,
        include_tasks=None,
        summarize=None,
    )
    assert wf == expected_wf


@pytest.mark.asyncio
async def test_get_workflow_without_tasks(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "get_execution_status")
    expected_wf = WorkflowAdapter()
    mock.return_value = expected_wf
    wf = await workflow_client.get_workflow(WORKFLOW_UUID, include_tasks=False)
    mock.assert_called_with(
        workflow_id=WORKFLOW_UUID,
        include_tasks=False,
        summarize=None,
    )
    assert wf == expected_wf


@pytest.mark.asyncio
async def test_get_workflow_non_existent(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "get_execution_status")
    mock.side_effect = ApiException(status=404, reason="Not Found")
    with pytest.raises(ApiException):
        await workflow_client.get_workflow(WORKFLOW_UUID)


@pytest.mark.asyncio
async def test_delete_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "delete1")
    await workflow_client.delete_workflow(WORKFLOW_UUID)
    mock.assert_called_with(workflow_id=WORKFLOW_UUID, archive_workflow=None)


@pytest.mark.asyncio
async def test_delete_workflow_without_archival(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "delete1")
    await workflow_client.delete_workflow(WORKFLOW_UUID, archive_workflow=False)
    mock.assert_called_with(workflow_id=WORKFLOW_UUID, archive_workflow=False)


@pytest.mark.asyncio
async def test_skip_task_from_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "skip_task_from_workflow")
    skip_request = SkipTaskRequestAdapter()
    await workflow_client.skip_task_from_workflow(WORKFLOW_UUID, TASK_NAME, skip_request)
    mock.assert_called_with(
        workflow_id=WORKFLOW_UUID,
        task_reference_name=TASK_NAME,
        skip_task_request=skip_request,
    )


@pytest.mark.asyncio
async def test_test_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApiAdapter, "test_workflow")
    expected_wf = WorkflowAdapter()
    mock.return_value = expected_wf
    test_request = WorkflowTestRequestAdapter(name=WORKFLOW_NAME)
    wf = await workflow_client.test_workflow(test_request)
    mock.assert_called_with(workflow_test_request=test_request)
    assert wf == expected_wf
