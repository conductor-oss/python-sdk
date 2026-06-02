import json
import logging
import unittest
from unittest.mock import patch, MagicMock

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

WORKFLOW_NAME = 'ut_wf'
WORKFLOW_UUID = 'ut_wf_uuid'
TASK_NAME = 'ut_task'
CORRELATION_ID = 'correlation_id'


class TestOrkesWorkflowClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        configuration = Configuration("http://localhost:8080/api")
        cls.workflow_client = OrkesWorkflowClient(configuration)

    def setUp(self):
        self.input = {"a": "test"}
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_init(self):
        message = "workflowResourceApi is not of type WorkflowResourceApi"
        self.assertIsInstance(self.workflow_client.workflowResourceApi, WorkflowResourceApi, message)

    @patch.object(WorkflowResourceApi, 'start_workflow1_with_http_info')
    def test_startWorkflowByName(self, mock):
        mock.return_value = (WORKFLOW_UUID, 200, {}, 42)
        wfId = self.workflow_client.start_workflow_by_name(WORKFLOW_NAME, self.input)
        mock.assert_called_with(self.input, WORKFLOW_NAME)
        self.assertEqual(wfId, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'start_workflow1_with_http_info')
    def test_startWorkflowByName_with_version(self, mock):
        mock.return_value = (WORKFLOW_UUID, 200, {}, 42)
        wfId = self.workflow_client.start_workflow_by_name(WORKFLOW_NAME, self.input, version=1)
        mock.assert_called_with(self.input, WORKFLOW_NAME, version=1)
        self.assertEqual(wfId, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'start_workflow1_with_http_info')
    def test_startWorkflowByName_with_correlation_id(self, mock):
        mock.return_value = (WORKFLOW_UUID, 200, {}, 42)
        wfId = self.workflow_client.start_workflow_by_name(WORKFLOW_NAME, self.input, correlationId=CORRELATION_ID)
        mock.assert_called_with(self.input, WORKFLOW_NAME, correlation_id=CORRELATION_ID)
        self.assertEqual(wfId, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'start_workflow1_with_http_info')
    def test_startWorkflowByName_with_version_and_priority(self, mock):
        mock.return_value = (WORKFLOW_UUID, 200, {}, 42)
        wfId = self.workflow_client.start_workflow_by_name(WORKFLOW_NAME, self.input, version=1, priority=1)
        mock.assert_called_with(self.input, WORKFLOW_NAME, version=1, priority=1)
        self.assertEqual(wfId, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'start_workflow_with_http_info')
    def test_startWorkflow(self, mock):
        mock.return_value = (WORKFLOW_UUID, 200, {}, 42)
        startWorkflowReq = StartWorkflowRequest()
        wfId = self.workflow_client.start_workflow(startWorkflowReq)
        mock.assert_called_with(startWorkflowReq)
        self.assertEqual(wfId, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'execute_workflow')
    def test_executeWorkflow(self, mock):
        expectedWfRun = WorkflowRun()
        mock.return_value = expectedWfRun
        startWorkflowReq = StartWorkflowRequest()
        startWorkflowReq.name = WORKFLOW_NAME
        startWorkflowReq.version = 1
        workflowRun = self.workflow_client.execute_workflow(
            startWorkflowReq, "request_id", None, 30
        )
        mock.assert_called_with(body=startWorkflowReq, request_id="request_id", name=WORKFLOW_NAME, version=1,
                                wait_until_task_ref=None, wait_for_seconds=30)
        self.assertEqual(workflowRun, expectedWfRun)

    @patch.object(WorkflowResourceApi, 'pause_workflow')
    def test_pauseWorkflow(self, mock):
        self.workflow_client.pause_workflow(WORKFLOW_UUID)
        mock.assert_called_with(WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'resume_workflow')
    def test_resumeWorkflow(self, mock):
        self.workflow_client.resume_workflow(WORKFLOW_UUID)
        mock.assert_called_with(WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'restart')
    def test_restartWorkflow(self, mock):
        self.workflow_client.restart_workflow(WORKFLOW_UUID)
        mock.assert_called_with(WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'restart')
    def test_restartWorkflow_with_latest_wfDef(self, mock):
        self.workflow_client.restart_workflow(WORKFLOW_UUID, True)
        mock.assert_called_with(WORKFLOW_UUID, use_latest_definitions=True)

    @patch.object(WorkflowResourceApi, 'rerun')
    def test_rerunWorkflow(self, mock):
        reRunReq = RerunWorkflowRequest()
        self.workflow_client.rerun_workflow(WORKFLOW_UUID, reRunReq)
        mock.assert_called_with(reRunReq, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'retry')
    def test_retryWorkflow(self, mock):
        self.workflow_client.retry_workflow(WORKFLOW_UUID)
        mock.assert_called_with(WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'retry')
    def test_retryWorkflow_with_resumeSubworkflowTasks(self, mock):
        self.workflow_client.retry_workflow(WORKFLOW_UUID, True)
        mock.assert_called_with(WORKFLOW_UUID, resume_subworkflow_tasks=True)

    @patch.object(WorkflowResourceApi, 'terminate')
    def test_terminateWorkflow(self, mock):
        self.workflow_client.terminate_workflow(WORKFLOW_UUID)
        mock.assert_called_with(WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'terminate')
    def test_terminateWorkflow_with_reason(self, mock):
        reason = "Unit test failed"
        self.workflow_client.terminate_workflow(WORKFLOW_UUID, reason)
        mock.assert_called_with(WORKFLOW_UUID, reason=reason)

    @patch.object(WorkflowResourceApi, 'get_execution_status')
    def test_getWorkflow(self, mock):
        mock.return_value = Workflow(workflow_id=WORKFLOW_UUID)
        workflow = self.workflow_client.get_workflow(WORKFLOW_UUID)
        mock.assert_called_with(WORKFLOW_UUID, include_tasks=True)
        self.assertEqual(workflow.workflow_id, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'get_execution_status')
    def test_getWorkflow_without_tasks(self, mock):
        mock.return_value = Workflow(workflow_id=WORKFLOW_UUID)
        workflow = self.workflow_client.get_workflow(WORKFLOW_UUID, False)
        mock.assert_called_with(WORKFLOW_UUID)
        self.assertEqual(workflow.workflow_id, WORKFLOW_UUID)

    @patch.object(WorkflowResourceApi, 'get_execution_status')
    def test_getWorkflow_non_existent(self, mock):
        error_body = {'status': 404, 'message': 'Workflow not found'}
        mock.side_effect = MagicMock(side_effect=ApiException(status=404, body=json.dumps(error_body)))
        with self.assertRaises(ApiException):
            self.workflow_client.get_workflow(WORKFLOW_UUID, False)
            mock.assert_called_with(WORKFLOW_UUID, include_tasks=False)

    @patch.object(WorkflowResourceApi, 'delete')
    def test_deleteWorkflow(self, mock):
        workflow = self.workflow_client.delete_workflow(WORKFLOW_UUID)
        mock.assert_called_with(WORKFLOW_UUID, archive_workflow=True)

    @patch.object(WorkflowResourceApi, 'delete')
    def test_deleteWorkflow_without_archival(self, mock):
        workflow = self.workflow_client.delete_workflow(WORKFLOW_UUID, False)
        mock.assert_called_with(WORKFLOW_UUID, archive_workflow=False)

    @patch.object(WorkflowResourceApi, 'skip_task_from_workflow')
    def test_skipTaskFromWorkflow(self, mock):
        taskRefName = TASK_NAME + "_ref"
        request = SkipTaskRequest()
        workflow = self.workflow_client.skip_task_from_workflow(WORKFLOW_UUID, taskRefName, request)
        mock.assert_called_with(WORKFLOW_UUID, taskRefName, request)

    @patch.object(WorkflowResourceApi, 'test_workflow')
    def test_testWorkflow(self, mock):
        mock.return_value = Workflow(workflow_id=WORKFLOW_UUID)
        testRequest = WorkflowTestRequest(
            workflow_def=WorkflowDef(name=WORKFLOW_NAME, version=1),
            name=WORKFLOW_NAME
        )
        workflow = self.workflow_client.test_workflow(testRequest)
        mock.assert_called_with(testRequest)
        self.assertEqual(workflow.workflow_id, WORKFLOW_UUID)
