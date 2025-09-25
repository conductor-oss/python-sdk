from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from conductor.asyncio_client.adapters.models.correlation_ids_search_request_adapter import \
    CorrelationIdsSearchRequestAdapter
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import \
    RerunWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.scrollable_search_result_workflow_summary_adapter import \
    ScrollableSearchResultWorkflowSummaryAdapter
from conductor.asyncio_client.adapters.models.skip_task_request_adapter import \
    SkipTaskRequestAdapter
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import \
    StartWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.workflow_adapter import \
    WorkflowAdapter
from conductor.asyncio_client.adapters.models.workflow_run_adapter import \
    WorkflowRunAdapter
from conductor.asyncio_client.adapters.models.workflow_state_update_adapter import \
    WorkflowStateUpdateAdapter
from conductor.asyncio_client.adapters.models.workflow_status_adapter import \
    WorkflowStatusAdapter
from conductor.asyncio_client.adapters.models.workflow_test_request_adapter import \
    WorkflowTestRequestAdapter
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.http.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesWorkflowClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Core Workflow Execution Operations
    async def start_workflow_by_name(
        self,
        name: str,
        input_data: Dict[str, Any],
        version: Optional[int] = None,
        correlation_id: Optional[str] = None,
        priority: Optional[int] = None,
        x_idempotency_key: Optional[str] = None,
        x_on_conflict: Optional[str] = None,
    ) -> str:
        """Start a workflow by name with input data"""
        return await self.workflow_api.start_workflow1(
            name=name,
            request_body=input_data,
            version=version,
            correlation_id=correlation_id,
            priority=priority,
            x_idempotency_key=x_idempotency_key,
            x_on_conflict=x_on_conflict,
        )

    async def start_workflow(
        self, start_workflow_request: StartWorkflowRequestAdapter
    ) -> str:
        """Start a workflow with StartWorkflowRequest"""
        return await self.workflow_api.start_workflow(start_workflow_request)

    async def execute_workflow(
        self,
        start_workflow_request: StartWorkflowRequestAdapter,
        request_id: str,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: Optional[int] = None,
    ) -> WorkflowRunAdapter:
        """Execute a workflow synchronously"""
        return await self.workflow_api.execute_workflow(
            name=start_workflow_request.name,
            version=start_workflow_request.version,
            request_id=request_id,
            start_workflow_request=start_workflow_request,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    # Workflow Control Operations
    async def pause_workflow(self, workflow_id: str) -> None:
        """Pause a workflow execution"""
        await self.workflow_api.pause_workflow(workflow_id=workflow_id)

    async def resume_workflow(self, workflow_id: str) -> None:
        """Resume a paused workflow execution"""
        await self.workflow_api.resume_workflow(workflow_id=workflow_id)

    async def restart_workflow(
        self, workflow_id: str, use_latest_definitions: Optional[bool] = None
    ) -> None:
        """Restart a workflow execution"""
        await self.workflow_api.restart(
            workflow_id=workflow_id, use_latest_definitions=use_latest_definitions
        )

    async def rerun_workflow(
        self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequestAdapter
    ) -> str:
        """Rerun a workflow from a specific task"""
        return await self.workflow_api.rerun(
            workflow_id=workflow_id, rerun_workflow_request=rerun_workflow_request
        )

    async def retry_workflow(
        self,
        workflow_id: str,
        resume_subworkflow_tasks: Optional[bool] = None,
        retry_if_retried_by_parent: Optional[bool] = None,
    ) -> None:
        """Retry a failed workflow execution"""
        await self.workflow_api.retry(
            workflow_id=workflow_id,
            resume_subworkflow_tasks=resume_subworkflow_tasks,
            retry_if_retried_by_parent=retry_if_retried_by_parent,
        )

    async def terminate_workflow(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        trigger_failure_workflow: Optional[bool] = None,
    ) -> None:
        """Terminate a workflow execution"""
        await self.workflow_api.terminate1(
            workflow_id=workflow_id,
            reason=reason,
            trigger_failure_workflow=trigger_failure_workflow,
        )

    async def delete_workflow(
        self, workflow_id: str, archive_workflow: Optional[bool] = None
    ) -> None:
        """Delete a workflow execution"""
        await self.workflow_api.delete1(
            workflow_id=workflow_id, archive_workflow=archive_workflow
        )

    # Workflow Information Operations
    async def get_workflow(
        self,
        workflow_id: str,
        include_tasks: Optional[bool] = None,
        summarize: Optional[bool] = None,
    ) -> WorkflowAdapter:
        """Get workflow execution status and details"""
        return await self.workflow_api.get_execution_status(
            workflow_id=workflow_id, include_tasks=include_tasks, summarize=summarize
        )

    async def get_workflow_status_summary(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
    ) -> WorkflowStatusAdapter:
        """Get workflow status summary"""
        return await self.workflow_api.get_workflow_status_summary(
            workflow_id=workflow_id,
            include_output=include_output,
            include_variables=include_variables,
        )

    async def get_running_workflows(
        self,
        name: str,
        version: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[str]:
        """Get running workflow IDs"""
        return await self.workflow_api.get_running_workflow(
            name=name, version=version, start_time=start_time, end_time=end_time
        )

    async def get_workflows_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get workflows by correlation IDs"""
        # Create correlation IDs search request
        search_request = CorrelationIdsSearchRequestAdapter(    
            workflow_names=[workflow_name],
            correlation_ids=correlation_ids,
        )
        return await self.workflow_api.get_workflows1(
            correlation_ids_search_request=search_request,
            include_closed=include_completed,
            include_tasks=include_tasks,
        )

    async def get_workflows_by_correlation_ids_batch(
        self,
        batch_request: CorrelationIdsSearchRequestAdapter,
        include_completed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get workflows by correlation IDs in batch"""
        return await self.workflow_api.get_workflows1(
            batch_request, include_closed=include_completed, include_tasks=include_tasks
        )

    # Workflow Search Operations
    async def search_workflows(
        self,
        start: Optional[int] = None,
        size: Optional[int] = None,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
        skip_cache: Optional[bool] = None,
    ) -> ScrollableSearchResultWorkflowSummaryAdapter:
        """Search for workflows based on payload and other parameters"""
        return await self.workflow_api.search(
            start=start,
            size=size,
            sort=sort,
            free_text=free_text,
            query=query,
            skip_cache=skip_cache,
        )

    # Task Operations
    async def skip_task_from_workflow(
        self,
        workflow_id: str,
        task_reference_name: str,
        skip_task_request: SkipTaskRequestAdapter,
    ) -> None:
        """Skip a task in a workflow"""
        await self.workflow_api.skip_task_from_workflow(
            workflow_id=workflow_id,
            task_reference_name=task_reference_name,
            skip_task_request=skip_task_request,
        )

    async def jump_to_task(
        self,
        workflow_id: str,
        task_reference_name: str,
        workflow_input: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Jump to a specific task in a workflow"""
        await self.workflow_api.jump_to_task(
            workflow_id=workflow_id,
            task_reference_name=task_reference_name,
            request_body=workflow_input or {},
        )

    # Workflow State Operations
    async def update_workflow_state(
        self, workflow_id: str, workflow_state_update: WorkflowStateUpdateAdapter
    ) -> WorkflowAdapter:
        """Update workflow state"""
        # Convert the adapter to dict for the API call
        request_body = (
            workflow_state_update.to_dict()
            if hasattr(workflow_state_update, "to_dict")
            else workflow_state_update
        )
        return await self.workflow_api.update_workflow_state(
            workflow_id=workflow_id, request_body=request_body
        )

    async def update_workflow_and_task_state(
        self,
        workflow_id: str,
        workflow_state_update: WorkflowStateUpdateAdapter,
        request_id: str = str(uuid.uuid4()),
        wait_until_task_ref_name: Optional[str] = None,
        wait_for_seconds: Optional[int] = None,
    ) -> WorkflowRunAdapter:
        """Update workflow and task state"""
        return await self.workflow_api.update_workflow_and_task_state(
            workflow_id=workflow_id,
            request_id=request_id,
            workflow_state_update=workflow_state_update,
            wait_until_task_ref=wait_until_task_ref_name,
            wait_for_seconds=wait_for_seconds,
        )

    # Advanced Operations
    async def test_workflow(
        self, test_request: WorkflowTestRequestAdapter
    ) -> WorkflowAdapter:
        """Test a workflow definition"""
        return await self.workflow_api.test_workflow(workflow_test_request=test_request)

    async def reset_workflow(self, workflow_id: str) -> None:
        """Reset a workflow execution"""
        await self.workflow_api.reset_workflow(workflow_id=workflow_id)

    async def decide_workflow(self, workflow_id: str) -> None:
        """Trigger workflow decision processing"""
        await self.workflow_api.decide(workflow_id=workflow_id)

    # Convenience Methods (for backward compatibility)
    async def execute_workflow_with_return_strategy(
        self,
        start_workflow_request: StartWorkflowRequestAdapter,
        request_id: str,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 30,
    ) -> WorkflowRunAdapter:
        """Execute a workflow synchronously - alias for execute_workflow"""
        return await self.execute_workflow(
            start_workflow_request=start_workflow_request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    async def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Alias for get_workflows_by_correlation_ids"""
        return await self.get_workflows_by_correlation_ids(
            workflow_name=workflow_name,
            correlation_ids=correlation_ids,
            include_completed=include_completed,
            include_tasks=include_tasks,
        )

    async def get_by_correlation_ids_in_batch(
        self,
        batch_request: CorrelationIdsSearchRequestAdapter,
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Alias for get_workflows_by_correlation_ids_batch"""
        return await self.get_workflows_by_correlation_ids_batch(
            batch_request=batch_request,
            include_completed=include_completed,
            include_tasks=include_tasks,
        )

    async def search(
        self,
        start: int = 0,
        size: int = 100,
        free_text: str = "*",
        query: Optional[str] = None,
        skip_cache: Optional[bool] = None,
    ) -> ScrollableSearchResultWorkflowSummaryAdapter:
        """Alias for search_workflows for backward compatibility"""
        return await self.search_workflows(
            start=start,
            size=size,
            free_text=free_text,
            query=query,
            skip_cache=skip_cache,
        )

    async def remove_workflow(
        self, workflow_id: str, archive_workflow: Optional[bool] = None
    ) -> None:
        """Alias for delete_workflow"""
        await self.delete_workflow(
            workflow_id=workflow_id, archive_workflow=archive_workflow
        )

    async def update_variables(
        self, workflow_id: str, variables: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update workflow variables - implemented via workflow state update"""
        if variables:
            state_update = WorkflowStateUpdateAdapter()
            state_update.variables = variables
            await self.update_workflow_state(
                workflow_id=workflow_id, workflow_state_update=state_update
            )

    async def update_state(
        self,
        workflow_id: str,
        update_request: WorkflowStateUpdateAdapter,
    ) -> WorkflowRunAdapter:
        """Alias for update_workflow_state"""
        return await self.update_workflow_and_task_state(
            workflow_id=workflow_id, workflow_state_update=update_request
        )

    async def get_workflow_status(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
    ) -> WorkflowStatusAdapter:
        """Alias for get_workflow_status_summary"""
        return await self.get_workflow_status_summary(
            workflow_id=workflow_id,
            include_output=include_output,
            include_variables=include_variables,
        )
