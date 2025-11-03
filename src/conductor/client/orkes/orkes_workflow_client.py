from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Any

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.correlation_ids_search_request import CorrelationIdsSearchRequest
from conductor.client.http.models.rerun_workflow_request import RerunWorkflowRequest
from conductor.client.http.models.scrollable_search_result_workflow_summary import (
    ScrollableSearchResultWorkflowSummary,
)
from conductor.client.http.models.skip_task_request import SkipTaskRequest
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.workflow import Workflow
from conductor.client.http.models.workflow_run import WorkflowRun
from conductor.client.http.models.workflow_state_update import WorkflowStateUpdate
from conductor.client.http.models.workflow_status import WorkflowStatus
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.workflow_client import WorkflowClient
from conductor.client.http.models.task_list_search_result_summary import TaskListSearchResultSummary
from conductor.client.http.models.upgrade_workflow_request import UpgradeWorkflowRequest


class OrkesWorkflowClient(OrkesBaseClient, WorkflowClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def start_workflow_by_name(
        self,
        name: str,
        input: Dict[str, object],
        version: Optional[int] = None,
        correlationId: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> str:
        kwargs = {}
        if version:
            kwargs.update({"version": version})
        if correlationId:
            kwargs.update({"correlation_id": correlationId})
        if priority:
            kwargs.update({"priority": priority})

        return self._workflow_api.start_workflow1(input, name, **kwargs)

    def start_workflow(self, start_workflow_request: StartWorkflowRequest, **kwargs) -> str:
        return self._workflow_api.start_workflow(start_workflow_request)

    def execute_workflow(
        self,
        start_workflow_request: StartWorkflowRequest,
        request_id: Optional[str] = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 30,
        **kwargs,
    ) -> WorkflowRun:
        return self._workflow_api.execute_workflow(
            body=start_workflow_request,
            request_id=request_id,
            version=start_workflow_request.version,
            name=start_workflow_request.name,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            **kwargs,
        )

    def execute_workflow_with_return_strategy(
        self,
        start_workflow_request: StartWorkflowRequest,
        request_id: Optional[str] = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 30,
        consistency: Optional[str] = None,
        return_strategy: Optional[str] = None,
        **kwargs,
    ) -> WorkflowRun:
        """Execute a workflow synchronously with optional reactive features
        Args:
            start_workflow_request: StartWorkflowRequest containing workflow details
            request_id: Optional request ID for tracking
            wait_until_task_ref: Wait until this task reference is reached
            wait_for_seconds: How long to wait for completion (default 30)
            consistency: Workflow consistency level - 'DURABLE' or 'SYNCHRONOUS' or 'REGION_DURABLE'
            return_strategy: Return strategy - 'TARGET_WORKFLOW' or 'BLOCKING_WORKFLOW' or 'BLOCKING_TASK' or 'BLOCKING_TASK_INPUT'
        Returns:
            WorkflowRun: The workflow execution result
        """
        if consistency is None:
            consistency = "DURABLE"
        if return_strategy is None:
            return_strategy = "TARGET_WORKFLOW"

        return self._workflow_api.execute_workflow_with_return_strategy(
            body=start_workflow_request,
            name=start_workflow_request.name,
            version=start_workflow_request.version,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            consistency=consistency,
            return_strategy=return_strategy,
            **kwargs,
        )

    def pause_workflow(self, workflow_id: str, **kwargs) -> None:
        self._workflow_api.pause_workflow(workflow_id, **kwargs)

    def resume_workflow(self, workflow_id: str, **kwargs) -> None:
        self._workflow_api.resume_workflow(workflow_id, **kwargs)

    def restart_workflow(self, workflow_id: str, use_latest_def: Optional[bool] = False) -> None:
        kwargs = {}

        if use_latest_def:
            kwargs["use_latest_definitions"] = use_latest_def

        self._workflow_api.restart(workflow_id, **kwargs)

    def rerun_workflow(
        self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequest, **kwargs
    ) -> str:
        rerun_workflow_request.re_run_from_workflow_id = workflow_id
        return self._workflow_api.rerun(rerun_workflow_request, workflow_id, **kwargs)

    def retry_workflow(
        self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = False
    ) -> None:
        kwargs = {}
        if resume_subworkflow_tasks:
            kwargs["resume_subworkflow_tasks"] = resume_subworkflow_tasks
        self._workflow_api.retry(workflow_id, **kwargs)

    def terminate_workflow(
        self, workflow_id: str, reason: Optional[str] = None, trigger_failure_workflow: bool = False
    ) -> None:
        kwargs = {}
        if reason:
            kwargs["reason"] = reason
        if trigger_failure_workflow:
            kwargs["trigger_failure_workflow"] = trigger_failure_workflow  # type: ignore[assignment]
        self._workflow_api.terminate1(workflow_id, **kwargs)

    def get_workflow(self, workflow_id: str, include_tasks: Optional[bool] = True) -> Workflow:
        kwargs = {}
        if include_tasks:
            kwargs["include_tasks"] = include_tasks
        return self._workflow_api.get_execution_status(workflow_id, **kwargs)

    def get_workflow_status(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
    ) -> WorkflowStatus:
        kwargs = {}
        if include_output is not None:
            kwargs["include_output"] = include_output
        if include_variables is not None:
            kwargs["include_variables"] = include_variables
        return self._workflow_api.get_workflow_status_summary(workflow_id, **kwargs)

    def delete_workflow(self, workflow_id: str, archive_workflow: Optional[bool] = True):
        self._workflow_api.delete1(workflow_id, archive_workflow=archive_workflow)

    def skip_task_from_workflow(
        self,
        workflow_id: str,
        task_reference_name: str,
        request: Optional[SkipTaskRequest],
        **kwargs,
    ) -> None:
        self._workflow_api.skip_task_from_workflow(
            workflow_id, task_reference_name, request, **kwargs
        )

    def test_workflow(self, test_request: WorkflowTestRequest, **kwargs) -> Workflow:
        return self._workflow_api.test_workflow(test_request, **kwargs)

    def search(
        self,
        start: int = 0,
        size: int = 100,
        free_text: str = "*",
        query: Optional[str] = None,
        query_id: Optional[str] = None,
        skip_cache: bool = False,
    ) -> ScrollableSearchResultWorkflowSummary:
        kwargs = {}

        if start is not None:
            kwargs["start"] = start
        if size is not None:
            kwargs["size"] = size
        if free_text is not None:
            kwargs["free_text"] = free_text
        if query is not None:
            kwargs["query"] = query
        if query_id is not None:
            kwargs["query_id"] = query_id
        if skip_cache is not None:
            kwargs["skip_cache"] = skip_cache

        return self._workflow_api.search(**kwargs)

    def get_by_correlation_ids_in_batch(
        self,
        batch_request: CorrelationIdsSearchRequest,
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> Dict[str, List[Workflow]]:
        """Given the list of correlation ids and list of workflow names, find and return workflows
        Returns a map with key as correlationId and value as a list of Workflows
        When IncludeClosed is set to true, the return value also includes workflows that are completed otherwise only running workflows are returned"""
        kwargs = {}

        kwargs["body"] = batch_request
        if include_tasks:
            kwargs["include_tasks"] = include_tasks
        if include_completed:
            kwargs["include_closed"] = include_completed
        return self._workflow_api.get_workflows1(**kwargs)

    def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> Dict[str, List[Workflow]]:
        """Lists workflows for the given correlation id list"""
        kwargs = {}
        if include_tasks:
            kwargs["include_tasks"] = include_tasks
        if include_completed:
            kwargs["include_closed"] = include_completed

        return self._workflow_api.get_workflows(body=correlation_ids, name=workflow_name, **kwargs)

    def remove_workflow(self, workflow_id: str):
        self._workflow_api.delete1(workflow_id)

    def update_variables(
        self, workflow_id: str, variables: Optional[Dict[str, object]] = None, **kwargs
    ) -> None:
        variables = variables or {}
        self._workflow_api.update_workflow_state(variables, workflow_id, **kwargs)

    def update_state(
        self,
        workflow_id: str,
        update_request: WorkflowStateUpdate,
        wait_until_task_ref_names: Optional[List[str]] = None,
        wait_for_seconds: Optional[int] = None,
    ) -> WorkflowRun:
        kwargs = {}
        request_id = str(uuid.uuid4())
        if wait_until_task_ref_names is not None:
            kwargs["wait_until_task_ref"] = ",".join(wait_until_task_ref_names)
        if wait_for_seconds is not None:
            kwargs["wait_for_seconds"] = wait_for_seconds

        return self._workflow_api.update_workflow_and_task_state(
            body=update_request, workflow_id=workflow_id, request_id=request_id, **kwargs
        )

    def decide(self, workflow_id: str, **kwargs) -> None:
        self._workflow_api.decide(workflow_id, **kwargs)

    def execute_workflow_as_api(
        self, body: Dict[str, object], name: str, **kwargs
    ) -> Dict[str, Any]:
        return self._workflow_api.execute_workflow_as_api(body, name, **kwargs)

    def execute_workflow_as_get_api(self, name: str, **kwargs) -> Dict[str, Any]:
        return self._workflow_api.execute_workflow_as_get_api(name, **kwargs)

    def get_execution_status_task_list(
        self, workflow_id: str, **kwargs
    ) -> TaskListSearchResultSummary:
        return self._workflow_api.get_execution_status_task_list(workflow_id, **kwargs)

    def get_running_workflow(self, name: str, **kwargs) -> List[str]:
        return self._workflow_api.get_running_workflow(name, **kwargs)

    def get_workflows_by_correlation_id(
        self, name: str, correlation_id: str, **kwargs
    ) -> List[Workflow]:
        return self._workflow_api.get_workflows2(name, correlation_id, **kwargs)

    def jump_to_task(
        self, body: Dict[str, object], workflow_id: str, task_reference_name: str
    ) -> None:
        kwargs = {}

        if task_reference_name is not None:
            kwargs["task_reference_name"] = task_reference_name

        return self._workflow_api.jump_to_task(body, workflow_id, **kwargs)

    def reset_workflow(self, workflow_id: str, **kwargs) -> None:
        self._workflow_api.reset_workflow(workflow_id, **kwargs)

    def upgrade_running_workflow_to_version(
        self, body: UpgradeWorkflowRequest, workflow_id: str, **kwargs
    ) -> None:
        return self._workflow_api.upgrade_running_workflow_to_version(body, workflow_id, **kwargs)
