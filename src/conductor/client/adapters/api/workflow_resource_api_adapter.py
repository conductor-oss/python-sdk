from typing import Dict, List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.workflow_resource_api import WorkflowResourceApi
from conductor.client.http.models.correlation_ids_search_request import CorrelationIdsSearchRequest
from conductor.client.http.models.rerun_workflow_request import RerunWorkflowRequest
from conductor.client.http.models.scrollable_search_result_workflow_summary import (
    ScrollableSearchResultWorkflowSummary,
)
from conductor.client.http.models.skip_task_request import SkipTaskRequest
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.task_list_search_result_summary import TaskListSearchResultSummary
from conductor.client.http.models.upgrade_workflow_request import UpgradeWorkflowRequest
from conductor.client.http.models.workflow import Workflow
from conductor.client.http.models.workflow_run import WorkflowRun
from conductor.client.http.models.workflow_state_update import WorkflowStateUpdate
from conductor.client.http.models.workflow_status import WorkflowStatus
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest


class WorkflowResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = WorkflowResourceApi(api_client)

    def decide(self, workflow_id: str, **kwargs) -> None:
        """Starts the decision task for a workflow"""
        return self._api.decide(workflow_id, **kwargs)

    def delete1(self, workflow_id: str, **kwargs) -> None:
        """Removes the workflow from the system"""
        return self._api.delete1(workflow_id, **kwargs)

    def execute_workflow(
        self, body: StartWorkflowRequest, request_id: str, name: str, version: int, **kwargs
    ) -> WorkflowRun:
        """Execute a workflow synchronously"""
        return self._api.execute_workflow(body, request_id, name, version, **kwargs)

    def execute_workflow_as_api(
        self, body: Dict[str, object], name: str, **kwargs
    ) -> Dict[str, object]:
        """Execute a workflow as API"""
        return self._api.execute_workflow_as_api(body, name, **kwargs)

    def execute_workflow_as_get_api(self, name: str, **kwargs) -> Dict[str, object]:
        """Execute a workflow as GET API"""
        return self._api.execute_workflow_as_get_api(name, **kwargs)

    def get_execution_status(self, workflow_id: str, **kwargs) -> Workflow:
        """Get the execution status of a workflow"""
        return self._api.get_execution_status(workflow_id, **kwargs)

    def get_execution_status_task_list(
        self, workflow_id: str, **kwargs
    ) -> TaskListSearchResultSummary:
        """Get the execution status task list of a workflow"""
        return self._api.get_execution_status_task_list(workflow_id, **kwargs)

    def get_running_workflow(self, name: str, **kwargs) -> List[str]:
        """Get the running workflows"""
        return self._api.get_running_workflow(name, **kwargs)

    def get_workflow_status_summary(self, workflow_id: str, **kwargs) -> WorkflowStatus:
        """Get the workflow status summary"""
        return self._api.get_workflow_status_summary(workflow_id, **kwargs)

    def get_workflows(self, body: List[str], name: str, **kwargs) -> Dict[str, List[Workflow]]:
        """Get the workflows"""
        return self._api.get_workflows(body, name, **kwargs)

    def get_workflows1(
        self, body: CorrelationIdsSearchRequest, **kwargs
    ) -> Dict[str, List[Workflow]]:
        """Get the workflows"""
        return self._api.get_workflows1(body, **kwargs)

    def get_workflows2(self, name: str, correlation_id: str, **kwargs) -> List[Workflow]:
        """Lists workflows for the given correlation id"""
        return self._api.get_workflows2(name, correlation_id, **kwargs)

    def jump_to_task(self, body: Dict[str, object], workflow_id: str, **kwargs) -> None:
        """Jump workflow execution to given task"""
        return self._api.jump_to_task(body, workflow_id, **kwargs)

    def pause_workflow(self, workflow_id: str, **kwargs) -> None:
        """Pauses the workflow"""
        return self._api.pause_workflow(workflow_id, **kwargs)

    def rerun(self, body: RerunWorkflowRequest, workflow_id: str, **kwargs) -> str:
        """Reruns the workflow from a specific task"""
        return self._api.rerun(body, workflow_id, **kwargs)

    def reset_workflow(self, workflow_id: str, **kwargs) -> None:
        """Resets callback times of all non-terminal SIMPLE tasks to 0"""
        return self._api.reset_workflow(workflow_id, **kwargs)

    def restart(self, workflow_id: str, **kwargs) -> None:
        """Restarts a completed workflow"""
        return self._api.restart(workflow_id, **kwargs)

    def resume_workflow(self, workflow_id: str, **kwargs) -> None:
        """Resumes the workflow"""
        return self._api.resume_workflow(workflow_id, **kwargs)

    def retry(self, workflow_id: str, **kwargs) -> None:
        """Retries the last failed task"""
        return self._api.retry(workflow_id, **kwargs)

    def search(self, **kwargs) -> ScrollableSearchResultWorkflowSummary:
        """Search for workflows based on payload and other parameters"""
        return self._api.search(**kwargs)

    def skip_task_from_workflow(
        self, body: SkipTaskRequest, workflow_id: str, task_reference_name: str, **kwargs
    ) -> None:
        """Skips a given task from a current running workflow"""
        return self._api.skip_task_from_workflow(body, workflow_id, task_reference_name, **kwargs)

    def start_workflow(self, body: StartWorkflowRequest, **kwargs) -> str:
        """Starts a workflow"""
        return self._api.start_workflow(body, **kwargs)

    def start_workflow1(self, body: Dict[str, object], name: str, **kwargs) -> str:
        """Starts a workflow"""
        return self._api.start_workflow1(body, name, **kwargs)

    def terminate1(self, workflow_id: str, **kwargs) -> None:
        """Terminates a workflow"""
        return self._api.terminate1(workflow_id, **kwargs)

    def test_workflow(self, body: WorkflowTestRequest, **kwargs) -> Workflow:
        """Tests a workflow"""
        return self._api.test_workflow(body, **kwargs)

    def update_workflow_and_task_state(
        self, body: WorkflowStateUpdate, request_id: str, workflow_id: str, **kwargs
    ) -> WorkflowRun:
        """Update a workflow state by updating variables or in progress task"""
        return self._api.update_workflow_and_task_state(body, request_id, workflow_id, **kwargs)

    def update_workflow_state(
        self, body: Dict[str, object], workflow_id: str, **kwargs
    ) -> Workflow:
        """Update workflow variables"""
        return self._api.update_workflow_state(body, workflow_id, **kwargs)

    def upgrade_running_workflow_to_version(
        self, body: UpgradeWorkflowRequest, workflow_id: str, **kwargs
    ) -> None:
        """Upgrade running workflow to newer version"""
        return self._api.upgrade_running_workflow_to_version(body, workflow_id, **kwargs)

    def execute_workflow_with_return_strategy(
        self, body: StartWorkflowRequest, name: str, version: int, **kwargs
    ) -> WorkflowRun:
        """Execute a workflow synchronously with reactive response"""
        return self._api.execute_workflow_with_return_strategy(body, name, version, **kwargs)
