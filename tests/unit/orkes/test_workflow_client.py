import json
import logging
import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.workflow_resource_api import WorkflowResourceApi
from conductor.client.http.models import SkipTaskRequest
from conductor.client.http.models.rerun_workflow_request import RerunWorkflowRequest
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.workflow import Workflow
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_run import WorkflowRun
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
from conductor.client.http.rest import ApiException
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient

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


def test_init(workflow_client):
    message = "workflowResourceApi is not of type WorkflowResourceApi"
    assert isinstance(workflow_client.workflowResourceApi, WorkflowResourceApi), message


def test_start_workflow_by_name(mocker, workflow_client, workflow_input):
    mock = mocker.patch.object(WorkflowResourceApi, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = workflow_client.start_workflow_by_name(WORKFLOW_NAME, workflow_input)
    mock.assert_called_with(workflow_input, WORKFLOW_NAME)
    assert wf_id == WORKFLOW_UUID


def test_start_workflow_by_name_with_version(mocker, workflow_client, workflow_input):
    mock = mocker.patch.object(WorkflowResourceApi, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = workflow_client.start_workflow_by_name(
        WORKFLOW_NAME, workflow_input, version=1
    )
    mock.assert_called_with(workflow_input, WORKFLOW_NAME, version=1)
    assert wf_id == WORKFLOW_UUID


def test_start_workflow_by_name_with_correlation_id(
    mocker, workflow_client, workflow_input
):
    mock = mocker.patch.object(WorkflowResourceApi, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = workflow_client.start_workflow_by_name(
        WORKFLOW_NAME, workflow_input, correlationId=CORRELATION_ID
    )
    mock.assert_called_with(
        workflow_input, WORKFLOW_NAME, correlation_id=CORRELATION_ID
    )
    assert wf_id == WORKFLOW_UUID


def test_start_workflow_by_name_with_version_and_priority(
    mocker, workflow_client, workflow_input
):
    mock = mocker.patch.object(WorkflowResourceApi, "start_workflow1")
    mock.return_value = WORKFLOW_UUID
    wf_id = workflow_client.start_workflow_by_name(
        WORKFLOW_NAME, workflow_input, version=1, priority=1
    )
    mock.assert_called_with(workflow_input, WORKFLOW_NAME, version=1, priority=1)
    assert wf_id == WORKFLOW_UUID


def test_start_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "start_workflow")
    mock.return_value = WORKFLOW_UUID
    start_workflow_req = StartWorkflowRequest()
    wf_id = workflow_client.start_workflow(start_workflow_req)
    mock.assert_called_with(start_workflow_req)
    assert wf_id == WORKFLOW_UUID


def test_execute_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "execute_workflow")
    expected_wf_run = WorkflowRun()
    mock.return_value = expected_wf_run
    start_workflow_req = StartWorkflowRequest()
    start_workflow_req.name = WORKFLOW_NAME
    start_workflow_req.version = 1
    workflow_run = workflow_client.execute_workflow(
        start_workflow_req, "request_id", None, 30
    )
    mock.assert_called_with(
        body=start_workflow_req,
        request_id="request_id",
        name=WORKFLOW_NAME,
        version=1,
        wait_until_task_ref=None,
        wait_for_seconds=30,
    )
    assert workflow_run == expected_wf_run


def test_pause_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "pause_workflow")
    workflow_client.pause_workflow(WORKFLOW_UUID)
    mock.assert_called_with(WORKFLOW_UUID)


def test_resume_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "resume_workflow")
    workflow_client.resume_workflow(WORKFLOW_UUID)
    mock.assert_called_with(WORKFLOW_UUID)


def test_restart_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "restart")
    workflow_client.restart_workflow(WORKFLOW_UUID)
    mock.assert_called_with(WORKFLOW_UUID)


def test_restart_workflow_with_latest_wf_def(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "restart")
    workflow_client.restart_workflow(WORKFLOW_UUID, True)
    mock.assert_called_with(WORKFLOW_UUID, use_latest_definitions=True)


def test_rerun_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "rerun")
    re_run_req = RerunWorkflowRequest()
    workflow_client.rerun_workflow(WORKFLOW_UUID, re_run_req)
    mock.assert_called_with(re_run_req, WORKFLOW_UUID)


def test_retry_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "retry")
    workflow_client.retry_workflow(WORKFLOW_UUID)
    mock.assert_called_with(WORKFLOW_UUID)


def test_retry_workflow_with_resume_subworkflow_tasks(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "retry")
    workflow_client.retry_workflow(WORKFLOW_UUID, True)
    mock.assert_called_with(WORKFLOW_UUID, resume_subworkflow_tasks=True)


def test_terminate_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "terminate")
    workflow_client.terminate_workflow(WORKFLOW_UUID)
    mock.assert_called_with(WORKFLOW_UUID)


def test_terminate_workflow_with_reason(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "terminate")
    reason = "Unit test failed"
    workflow_client.terminate_workflow(WORKFLOW_UUID, reason)
    mock.assert_called_with(WORKFLOW_UUID, reason=reason)


def test_get_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "get_execution_status")
    mock.return_value = Workflow(workflow_id=WORKFLOW_UUID)
    workflow = workflow_client.get_workflow(WORKFLOW_UUID)
    mock.assert_called_with(WORKFLOW_UUID, include_tasks=True)
    assert workflow.workflow_id == WORKFLOW_UUID


def test_get_workflow_without_tasks(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "get_execution_status")
    mock.return_value = Workflow(workflow_id=WORKFLOW_UUID)
    workflow = workflow_client.get_workflow(WORKFLOW_UUID, False)
    mock.assert_called_with(WORKFLOW_UUID)
    assert workflow.workflow_id == WORKFLOW_UUID


def test_get_workflow_non_existent(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "get_execution_status")
    error_body = {"status": 404, "message": "Workflow not found"}
    mock.side_effect = mocker.MagicMock(
        side_effect=ApiException(status=404, body=json.dumps(error_body))
    )
    with pytest.raises(ApiException):
        workflow_client.get_workflow(WORKFLOW_UUID, False)
        mock.assert_called_with(WORKFLOW_UUID, include_tasks=False)


def test_delete_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "delete")
    workflow = workflow_client.delete_workflow(WORKFLOW_UUID)
    mock.assert_called_with(WORKFLOW_UUID, archive_workflow=True)


def test_delete_workflow_without_archival(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "delete")
    workflow = workflow_client.delete_workflow(WORKFLOW_UUID, False)
    mock.assert_called_with(WORKFLOW_UUID, archive_workflow=False)


def test_skip_task_from_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "skip_task_from_workflow")
    task_ref_name = TASK_NAME + "_ref"
    request = SkipTaskRequest()
    workflow = workflow_client.skip_task_from_workflow(
        WORKFLOW_UUID, task_ref_name, request
    )
    mock.assert_called_with(WORKFLOW_UUID, task_ref_name, request)


def test_test_workflow(mocker, workflow_client):
    mock = mocker.patch.object(WorkflowResourceApi, "test_workflow")
    mock.return_value = Workflow(workflow_id=WORKFLOW_UUID)
    test_request = WorkflowTestRequest(
        workflow_def=WorkflowDef(name=WORKFLOW_NAME, version=1), name=WORKFLOW_NAME
    )
    workflow = workflow_client.test_workflow(test_request)
    mock.assert_called_with(test_request)
    assert workflow.workflow_id == WORKFLOW_UUID
