from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from conductor.asyncio_client.adapters.api.metadata_resource_api import \
    MetadataResourceApiAdapter
from conductor.asyncio_client.adapters.api.task_resource_api import \
    TaskResourceApiAdapter
from conductor.asyncio_client.adapters.models.correlation_ids_search_request_adapter import \
    CorrelationIdsSearchRequestAdapter
from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import \
    ExtendedWorkflowDefAdapter
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import \
    RerunWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.scrollable_search_result_workflow_summary_adapter import \
    ScrollableSearchResultWorkflowSummaryAdapter
from conductor.asyncio_client.adapters.models.skip_task_request_adapter import \
    SkipTaskRequestAdapter
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import \
    StartWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.task_result_adapter import \
    TaskResultAdapter
from conductor.asyncio_client.adapters.models.workflow_adapter import \
    WorkflowAdapter
from conductor.asyncio_client.adapters.models.workflow_run_adapter import \
    WorkflowRunAdapter
from conductor.asyncio_client.adapters.models.workflow_status_adapter import \
    WorkflowStatusAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.orkes.orkes_workflow_client import \
    OrkesWorkflowClient


class AsyncWorkflowExecutor:
    def __init__(self, configuration: Configuration):
        api_client = ApiClient(configuration)
        self.metadata_client = MetadataResourceApiAdapter(api_client)
        self.task_client = TaskResourceApiAdapter(api_client)
        self.workflow_client = OrkesWorkflowClient(configuration)

    async def register_workflow(
        self, workflow: ExtendedWorkflowDefAdapter, overwrite: Optional[bool] = None
    ) -> object:
        """Create a new workflow definition"""
        return await self.metadata_client.update(
            extended_workflow_def=[workflow], overwrite=overwrite
        )

    async def start_workflow(
        self, start_workflow_request: StartWorkflowRequestAdapter
    ) -> str:
        """Start a new workflow with StartWorkflowRequest, which allows task to be executed in a domain"""
        return await self.workflow_client.start_workflow(
            start_workflow_request=start_workflow_request,
        )

    async def start_workflows(
        self, *start_workflow_requests: StartWorkflowRequestAdapter
    ) -> list[str]:
        """Start multiple workflow instances sequentially.

        Note: There is no parallelism implemented here, so providing a very large
        number of workflows can impact latency and performance.
        """
        return [
            await self.start_workflow(start_workflow_request=request)
            for request in start_workflow_requests
        ]

    async def execute_workflow(
        self,
        request: StartWorkflowRequestAdapter,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 10,
        request_id: Optional[str] = None,
    ) -> WorkflowRunAdapter:
        """Executes a workflow with StartWorkflowRequest and waits for the completion of the workflow or until a
        specific task in the workflow"""
        if request_id is None:
            request_id = str(uuid.uuid4())

        return await self.workflow_client.execute_workflow(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    async def execute_workflow_with_return_strategy(
        self,
        request: StartWorkflowRequestAdapter,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 10,
        request_id: Optional[str] = None,
    ) -> WorkflowRunAdapter:
        """Execute a workflow synchronously with optional reactive features"""
        if request_id is None:
            request_id = str(uuid.uuid4())

        return await self.workflow_client.execute_workflow_with_return_strategy(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    async def execute(
        self,
        name: str,
        version: Optional[int] = None,
        workflow_input: Any = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 10,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> WorkflowRunAdapter:
        """Executes a workflow with StartWorkflowRequest and waits for the completion of the workflow or until a
        specific task in the workflow"""
        workflow_input = workflow_input or {}
        if request_id is None:
            request_id = str(uuid.uuid4())

        request = StartWorkflowRequestAdapter()
        request.name = name
        if version:
            request.version = version
        request.input = workflow_input
        request.correlation_id = correlation_id
        if domain is not None:
            request.task_to_domain = {"*": domain}

        return await self.workflow_client.execute_workflow(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    async def remove_workflow(
        self, workflow_id: str, archive_workflow: Optional[bool] = None
    ) -> None:
        """Removes the workflow permanently from the system"""
        kwargs = {}
        if archive_workflow is not None:
            kwargs["archive_workflow"] = archive_workflow
        return await self.workflow_client.delete_workflow(
            workflow_id=workflow_id, **kwargs
        )

    async def get_workflow(
        self, workflow_id: str, include_tasks: Optional[bool] = None
    ) -> WorkflowAdapter:
        """Gets the workflow by workflow id"""
        kwargs = {}
        if include_tasks is not None:
            kwargs["include_tasks"] = include_tasks
        return await self.workflow_client.get_workflow(
            workflow_id=workflow_id, **kwargs
        )

    async def get_workflow_status(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
    ) -> WorkflowStatusAdapter:
        """Gets the workflow by workflow id"""
        kwargs = {}
        if include_output is not None:
            kwargs["include_output"] = include_output
        if include_variables is not None:
            kwargs["include_variables"] = include_variables
        return await self.workflow_client.get_workflow_status(
            workflow_id=workflow_id,
            include_output=include_output,
            include_variables=include_variables,
        )

    async def search(
        self,
        start: Optional[int] = None,
        size: Optional[int] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        skip_cache: Optional[bool] = None,
    ) -> ScrollableSearchResultWorkflowSummaryAdapter:
        """Search for workflows based on payload and other parameters"""
        return await self.workflow_client.search(
            start=start,
            size=size,
            free_text=free_text,
            query=query,
            skip_cache=skip_cache,
        )

    async def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_closed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Lists workflows for the given correlation id list"""
        return await self.workflow_client.get_by_correlation_ids(
            correlation_ids=correlation_ids,
            workflow_name=workflow_name,
            include_tasks=include_tasks,
            include_completed=include_closed,
        )

    async def get_by_correlation_ids_and_names(
        self,
        batch_request: CorrelationIdsSearchRequestAdapter,
        include_closed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """
        Given the list of correlation ids and list of workflow names, find and return workflows Returns a map with
        key as correlationId and value as a list of Workflows When IncludeClosed is set to true, the return value
        also includes workflows that are completed otherwise only running workflows are returned
        """
        return await self.workflow_client.get_by_correlation_ids_in_batch(
            batch_request=batch_request,
            include_completed=include_closed,
            include_tasks=include_tasks,
        )

    async def pause(self, workflow_id: str) -> None:
        """Pauses the workflow"""
        return await self.workflow_client.pause_workflow(workflow_id=workflow_id)

    async def resume(self, workflow_id: str) -> None:
        """Resumes the workflow"""
        return await self.workflow_client.resume_workflow(workflow_id=workflow_id)

    async def terminate(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        trigger_failure_workflow: Optional[bool] = None,
    ) -> None:
        """Terminate workflow execution"""
        return await self.workflow_client.terminate_workflow(
            workflow_id=workflow_id,
            reason=reason,
            trigger_failure_workflow=trigger_failure_workflow,
        )

    async def restart(
        self, workflow_id: str, use_latest_definitions: Optional[bool] = None
    ) -> None:
        """Restarts a completed workflow"""
        return await self.workflow_client.restart_workflow(
            workflow_id=workflow_id, use_latest_definitions=use_latest_definitions
        )

    async def retry(
        self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = None
    ) -> None:
        """Retries the last failed task"""
        return await self.workflow_client.retry_workflow(
            workflow_id=workflow_id, resume_subworkflow_tasks=resume_subworkflow_tasks
        )

    async def rerun(
        self, rerun_workflow_request: RerunWorkflowRequestAdapter, workflow_id: str
    ) -> str:
        """Reruns the workflow from a specific task"""
        return await self.workflow_client.rerun_workflow(
            rerun_workflow_request=rerun_workflow_request,
            workflow_id=workflow_id,
        )

    async def skip_task_from_workflow(
        self,
        workflow_id: str,
        task_reference_name: str,
        skip_task_request: SkipTaskRequestAdapter = None,
    ) -> None:
        """Skips a given task from a current running workflow"""
        return await self.workflow_client.skip_task_from_workflow(
            workflow_id=workflow_id,
            task_reference_name=task_reference_name,
            skip_task_request=skip_task_request,
        )

    async def update_task(
        self, task_id: str, workflow_id: str, task_output: Dict[str, Any], status: str
    ) -> str:
        """Update a task"""
        task_result = self.__get_task_result(task_id, workflow_id, task_output, status)
        return await self.task_client.update_task(
            task_result=task_result,
        )

    async def update_task_by_ref_name(
        self,
        task_output: Dict[str, Any],
        workflow_id: str,
        task_reference_name: str,
        status: str,
    ) -> str:
        """Update a task By Ref Name"""
        return await self.task_client.update_task1(
            request_body=task_output,
            workflow_id=workflow_id,
            task_ref_name=task_reference_name,
            status=status,
        )

    async def update_task_by_ref_name_sync(
        self,
        task_output: Dict[str, Any],
        workflow_id: str,
        task_reference_name: str,
        status: str,
    ) -> WorkflowAdapter:
        """Update a task By Ref Name"""
        return await self.task_client.update_task_sync(
            request_body=task_output,
            workflow_id=workflow_id,
            task_ref_name=task_reference_name,
            status=status,
        )

    async def get_task(self, task_id: str) -> str:
        """Get task by Id"""
        return await self.task_client.get_task(task_id=task_id)

    def __get_task_result(
        self, task_id: str, workflow_id: str, task_output: Dict[str, Any], status: str
    ) -> TaskResultAdapter:
        return TaskResultAdapter(
            workflow_instance_id=workflow_id,
            task_id=task_id,
            output_data=task_output,
            status=status,
        )
