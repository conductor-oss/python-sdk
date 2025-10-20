from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.workflow import Workflow
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_run import WorkflowRun
from conductor.client.http.models.workflow_status import WorkflowStatus
from conductor.client.http.models.scrollable_search_result_workflow_summary import (
    ScrollableSearchResultWorkflowSummary,
)
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.skip_task_request import SkipTaskRequest
from conductor.client.http.models.rerun_workflow_request import RerunWorkflowRequest
from conductor.client.http.models.signal_response import SignalResponse
from conductor.client.http.models.correlation_ids_search_request import CorrelationIdsSearchRequest
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient


class WorkflowExecutor:
    def __init__(self, configuration: Configuration) -> Self:
        api_client = ApiClient(configuration)
        self.metadata_client = MetadataResourceApi(api_client)
        self.task_client = TaskResourceApi(api_client)
        self.workflow_client = OrkesWorkflowClient(configuration)

    def register_workflow(self, workflow: WorkflowDef, overwrite: Optional[bool] = None) -> object:
        """Create a new workflow definition"""
        kwargs = {}
        if overwrite is not None:
            kwargs["overwrite"] = overwrite
        return self.metadata_client.update(body=[workflow], **kwargs)

    def start_workflow(self, start_workflow_request: StartWorkflowRequest) -> str:
        """Start a new workflow with StartWorkflowRequest, which allows task to be executed in a domain"""
        return self.workflow_client.start_workflow(
            start_workflow_request=start_workflow_request,
        )

    def start_workflows(self, *start_workflow_request: StartWorkflowRequest) -> List[str]:
        """Start multiple instances of workflows.  Note, there is no parallelism implemented in starting so giving a
        very large number can impact the latencies and performance
        """
        workflow_id_list = [""] * len(start_workflow_request)
        for i in range(len(start_workflow_request)):
            workflow_id_list[i] = self.start_workflow(start_workflow_request=start_workflow_request[i])
        return workflow_id_list

    def execute_workflow(
        self,
        request: StartWorkflowRequest,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 10,
        request_id: Optional[str] = None,
    ) -> WorkflowRun:
        """Executes a workflow with StartWorkflowRequest and waits for the completion of the workflow or until a
        specific task in the workflow"""
        if request_id is None:
            request_id = str(uuid.uuid4())

        return self.workflow_client.execute_workflow(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    def execute_workflow_with_return_strategy(
        self,
        request: StartWorkflowRequest,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 10,
        request_id: Optional[str] = None,
        consistency: Optional[str] = None,
        return_strategy: Optional[str] = None,
    ) -> SignalResponse:
        """Execute a workflow synchronously with optional reactive features"""
        if request_id is None:
            request_id = str(uuid.uuid4())

        return self.workflow_client.execute_workflow_with_return_strategy(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            consistency=consistency,
            return_strategy=return_strategy,
        )

    def execute(
        self,
        name: str,
        version: Optional[int] = None,
        workflow_input: Any = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 10,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> WorkflowRun:
        """Executes a workflow with StartWorkflowRequest and waits for the completion of the workflow or until a
        specific task in the workflow"""
        workflow_input = workflow_input or {}
        if request_id is None:
            request_id = str(uuid.uuid4())

        request = StartWorkflowRequest()
        request.name = name
        if version:
            request.version = version
        request.input = workflow_input
        request.correlation_id = correlation_id
        if domain is not None:
            request.task_to_domain = {"*": domain}

        return self.workflow_client.execute_workflow(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    def remove_workflow(self, workflow_id: str, archive_workflow: Optional[bool] = None) -> None:
        """Removes the workflow permanently from the system"""
        kwargs = {}
        if archive_workflow is not None:
            kwargs["archive_workflow"] = archive_workflow
        return self.workflow_client.delete_workflow(workflow_id=workflow_id, **kwargs)

    def get_workflow(self, workflow_id: str, include_tasks: Optional[bool] = None) -> Workflow:
        """Gets the workflow by workflow id"""
        kwargs = {}
        if include_tasks is not None:
            kwargs["include_tasks"] = include_tasks
        return self.workflow_client.get_workflow(workflow_id=workflow_id, **kwargs)

    def get_workflow_status(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
    ) -> WorkflowStatus:
        """Gets the workflow by workflow id"""
        kwargs = {}
        if include_output is not None:
            kwargs["include_output"] = include_output
        if include_variables is not None:
            kwargs["include_variables"] = include_variables
        return self.workflow_client.get_workflow_status(
            workflow_id=workflow_id,
            include_output=include_output,
            include_variables=include_variables,
        )

    def search(
        self,
        query_id: Optional[str] = None,
        start: Optional[int] = None,
        size: Optional[int] = None,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        skip_cache: Optional[bool] = None,
    ) -> ScrollableSearchResultWorkflowSummary:
        """Search for workflows based on payload and other parameters"""
        return self.workflow_client.search(start=start, size=size, free_text=free_text, query=query)

    def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_closed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
    ) -> Dict[str, List[Workflow]]:
        """Lists workflows for the given correlation id list"""
        return self.workflow_client.get_by_correlation_ids(
            correlation_ids=correlation_ids,
            workflow_name=workflow_name,
            include_tasks=include_tasks,
            include_completed=include_closed,
        )

    def get_by_correlation_ids_and_names(
        self,
        batch_request: CorrelationIdsSearchRequest,
        include_closed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
    ) -> Dict[str, List[Workflow]]:
        """
        Given the list of correlation ids and list of workflow names, find and return workflows Returns a map with
        key as correlationId and value as a list of Workflows When IncludeClosed is set to true, the return value
        also includes workflows that are completed otherwise only running workflows are returned
        """
        return self.workflow_client.get_by_correlation_ids_in_batch(
            batch_request=batch_request,
            include_completed=include_closed,
            include_tasks=include_tasks,
        )

    def pause(self, workflow_id: str) -> None:
        """Pauses the workflow"""
        return self.workflow_client.pause_workflow(workflow_id=workflow_id)

    def resume(self, workflow_id: str) -> None:
        """Resumes the workflow"""
        return self.workflow_client.resume_workflow(workflow_id=workflow_id)

    def terminate(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        trigger_failure_workflow: Optional[bool] = None,
    ) -> None:
        """Terminate workflow execution"""
        return self.workflow_client.terminate_workflow(
            workflow_id=workflow_id,
            reason=reason,
            trigger_failure_workflow=trigger_failure_workflow,
        )

    def restart(self, workflow_id: str, use_latest_definitions: Optional[bool] = None) -> None:
        """Restarts a completed workflow"""
        return self.workflow_client.restart_workflow(workflow_id=workflow_id, use_latest_def=use_latest_definitions)

    def retry(self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = None) -> None:
        """Retries the last failed task"""
        return self.workflow_client.retry_workflow(
            workflow_id=workflow_id, resume_subworkflow_tasks=resume_subworkflow_tasks
        )

    def rerun(self, rerun_workflow_request: RerunWorkflowRequest, workflow_id: str) -> str:
        """Reruns the workflow from a specific task"""
        return self.workflow_client.rerun_workflow(
            rerun_workflow_request=rerun_workflow_request,
            workflow_id=workflow_id,
        )

    def skip_task_from_workflow(
        self, workflow_id: str, task_reference_name: str, skip_task_request: SkipTaskRequest = None
    ) -> None:
        """Skips a given task from a current running workflow"""
        return self.workflow_client.skip_task_from_workflow(
            workflow_id=workflow_id,
            task_reference_name=task_reference_name,
            request=skip_task_request,
        )

    def update_task(self, task_id: str, workflow_id: str, task_output: Dict[str, Any], status: str) -> str:
        """Update a task"""
        task_result = self.__get_task_result(task_id, workflow_id, task_output, status)
        return self.task_client.update_task(
            body=task_result,
        )

    def update_task_by_ref_name(
        self, task_output: Dict[str, Any], workflow_id: str, task_reference_name: str, status: str
    ) -> str:
        """Update a task By Ref Name"""
        return self.task_client.update_task1(
            body=task_output,
            workflow_id=workflow_id,
            task_ref_name=task_reference_name,
            status=status,
        )

    def update_task_by_ref_name_sync(
        self, task_output: Dict[str, Any], workflow_id: str, task_reference_name: str, status: str
    ) -> Workflow:
        """Update a task By Ref Name"""
        return self.task_client.update_task_sync(
            body=task_output,
            workflow_id=workflow_id,
            task_ref_name=task_reference_name,
            status=status,
        )

    def get_task(self, task_id: str) -> str:
        """Get task by Id"""
        return self.task_client.get_task(task_id=task_id)

    def signal(
        self,
        workflow_id: str,
        status: str,
        body: Dict[str, Any],
        return_strategy: Optional[str] = None,
    ) -> SignalResponse:
        """Update running task in the workflow with given status and output synchronously and return back updated workflow"""
        return self.task_client.signal_workflow_task_sync(
            workflow_id=workflow_id, status=status, body=body, return_strategy=return_strategy
        )

    def signal_async(self, workflow_id: str, status: str, body: Dict[str, Any]) -> None:
        """Update running task in the workflow with given status and output asynchronously"""
        return self.task_client.signal_workflow_task_async(workflow_id=workflow_id, status=status, body=body)

    def __get_task_result(self, task_id: str, workflow_id: str, task_output: Dict[str, Any], status: str) -> TaskResult:
        return TaskResult(
            workflow_instance_id=workflow_id,
            task_id=task_id,
            output_data=task_output,
            status=status,
        )
