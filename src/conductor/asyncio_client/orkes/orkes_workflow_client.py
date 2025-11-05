from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, cast

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.correlation_ids_search_request_adapter import (
    CorrelationIdsSearchRequestAdapter,
)
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import (
    RerunWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.scrollable_search_result_workflow_summary_adapter import (
    ScrollableSearchResultWorkflowSummaryAdapter,
)
from conductor.asyncio_client.adapters.models.skip_task_request_adapter import (
    SkipTaskRequestAdapter,
)
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import (
    StartWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.task_list_search_result_summary_adapter import (
    TaskListSearchResultSummaryAdapter,
)
from conductor.asyncio_client.adapters.models.upgrade_workflow_request_adapter import (
    UpgradeWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter
from conductor.asyncio_client.adapters.models.workflow_run_adapter import WorkflowRunAdapter
from conductor.asyncio_client.adapters.models.workflow_state_update_adapter import (
    WorkflowStateUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_status_adapter import WorkflowStatusAdapter
from conductor.asyncio_client.adapters.models.workflow_test_request_adapter import (
    WorkflowTestRequestAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesWorkflowClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        """Initialize the OrkesWorkflowClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            workflow_client = OrkesWorkflowClient(config, api_client)
            ```
        """
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
        **kwargs,
    ) -> str:
        """Start a workflow by name with input data.

        Args:
            name: Name of the workflow to start
            input_data: Input data for the workflow as dictionary
            version: Optional workflow version. If None, uses latest version
            correlation_id: Optional correlation ID for tracking related workflows
            priority: Optional priority level (0-99, higher is more priority)
            x_idempotency_key: Optional idempotency key to prevent duplicate executions
            x_on_conflict: Optional conflict resolution strategy
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow ID as string

        Example:
            ```python
            # Start a simple workflow
            workflow_id = await workflow_client.start_workflow_by_name(
                "order_processing",
                {"order_id": "12345", "customer_id": "cust-999"}
            )
            print(f"Started workflow: {workflow_id}")

            # Start with priority and correlation
            workflow_id = await workflow_client.start_workflow_by_name(
                "urgent_order_processing",
                {"order_id": "99999"},
                version=2,
                priority=10,
                correlation_id="batch-2024-01"
            )
            ```
        """
        return await self._workflow_api.start_workflow1(
            name=name,
            request_body=input_data,
            version=version,
            correlation_id=correlation_id,
            priority=priority,
            x_idempotency_key=x_idempotency_key,
            x_on_conflict=x_on_conflict,
            **kwargs,
        )

    async def start_workflow(
        self, start_workflow_request: StartWorkflowRequestAdapter, **kwargs
    ) -> str:
        """Start a workflow with StartWorkflowRequest.

        Args:
            start_workflow_request: Complete workflow start request with all parameters
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow ID as string

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter

            request = StartWorkflowRequestAdapter(
                name="order_processing",
                version=1,
                input={"order_id": "12345"},
                correlation_id="batch-001",
                priority=5
            )
            workflow_id = await workflow_client.start_workflow(request)
            ```
        """
        return await self._workflow_api.start_workflow(start_workflow_request, **kwargs)

    async def execute_workflow(
        self,
        start_workflow_request: StartWorkflowRequestAdapter,
        request_id: str,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: Optional[int] = None,
        **kwargs,
    ) -> WorkflowRunAdapter:
        """Execute a workflow synchronously and wait for completion or specific task.

        Args:
            start_workflow_request: Workflow start request
            request_id: Unique request ID for idempotency
            wait_until_task_ref: Optional task reference to wait for. If None, waits for completion
            wait_for_seconds: Maximum seconds to wait. If None, waits indefinitely
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowRunAdapter containing execution results

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
            import uuid

            request = StartWorkflowRequestAdapter(
                name="order_processing",
                input={"order_id": "12345"}
            )
            result = await workflow_client.execute_workflow(
                request,
                request_id=str(uuid.uuid4()),
                wait_for_seconds=30
            )
            print(f"Status: {result.status}, Output: {result.output}")
            ```
        """
        return await self._workflow_api.execute_workflow(
            name=start_workflow_request.name,
            version=start_workflow_request.version or 1,
            request_id=request_id,
            start_workflow_request=start_workflow_request,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            **kwargs,
        )

    # Workflow Control Operations
    async def pause_workflow(self, workflow_id: str, **kwargs) -> None:
        """Pause a workflow execution.

        Args:
            workflow_id: ID of the workflow to pause
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.pause_workflow("workflow-123")
            ```
        """
        await self._workflow_api.pause_workflow(workflow_id=workflow_id, **kwargs)

    async def resume_workflow(self, workflow_id: str, **kwargs) -> None:
        """Resume a paused workflow execution.

        Args:
            workflow_id: ID of the workflow to resume
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.resume_workflow("workflow-123")
            ```
        """
        await self._workflow_api.resume_workflow(workflow_id=workflow_id, **kwargs)

    async def restart_workflow(
        self, workflow_id: str, use_latest_definitions: Optional[bool] = None, **kwargs
    ) -> None:
        """Restart a workflow execution from the beginning.

        Args:
            workflow_id: ID of the workflow to restart
            use_latest_definitions: If True, use latest workflow and task definitions
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Restart with latest definitions
            await workflow_client.restart_workflow("workflow-123", use_latest_definitions=True)
            ```
        """
        await self._workflow_api.restart(
            workflow_id=workflow_id, use_latest_definitions=use_latest_definitions, **kwargs
        )

    async def rerun_workflow(
        self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequestAdapter, **kwargs
    ) -> str:
        """Rerun a workflow from a specific task.

        Args:
            workflow_id: ID of the workflow to rerun
            rerun_workflow_request: Configuration for rerun including from which task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            New workflow ID as string

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import RerunWorkflowRequestAdapter

            rerun_request = RerunWorkflowRequestAdapter(
                re_run_from_task_id="task-456",
                task_input={"retry_count": 1}
            )
            new_workflow_id = await workflow_client.rerun_workflow("workflow-123", rerun_request)
            ```
        """
        return await self._workflow_api.rerun(
            workflow_id=workflow_id, rerun_workflow_request=rerun_workflow_request, **kwargs
        )

    async def retry_workflow(
        self,
        workflow_id: str,
        resume_subworkflow_tasks: Optional[bool] = None,
        retry_if_retried_by_parent: Optional[bool] = None,
        **kwargs,
    ) -> None:
        """Retry a failed workflow execution.

        Args:
            workflow_id: ID of the workflow to retry
            resume_subworkflow_tasks: If True, resume subworkflow tasks
            retry_if_retried_by_parent: If True, retry even if parent already retried
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.retry_workflow("workflow-123", resume_subworkflow_tasks=True)
            ```
        """
        await self._workflow_api.retry(
            workflow_id=workflow_id,
            resume_subworkflow_tasks=resume_subworkflow_tasks,
            retry_if_retried_by_parent=retry_if_retried_by_parent,
            **kwargs,
        )

    async def terminate_workflow(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        trigger_failure_workflow: Optional[bool] = None,
        **kwargs,
    ) -> None:
        """Terminate a workflow execution.

        Args:
            workflow_id: ID of the workflow to terminate
            reason: Optional reason for termination
            trigger_failure_workflow: If True, trigger failure workflow if configured
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.terminate_workflow(
                "workflow-123",
                reason="Cancelled by user request"
            )
            ```
        """
        await self._workflow_api.terminate1(
            workflow_id=workflow_id,
            reason=reason,
            trigger_failure_workflow=trigger_failure_workflow,
            **kwargs,
        )

    async def delete_workflow(
        self, workflow_id: str, archive_workflow: Optional[bool] = None, **kwargs
    ) -> None:
        """Delete a workflow execution.

        Args:
            workflow_id: ID of the workflow to delete
            archive_workflow: If True, archive instead of permanently deleting
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Permanently delete
            await workflow_client.delete_workflow("workflow-123")

            # Archive workflow
            await workflow_client.delete_workflow("workflow-123", archive_workflow=True)
            ```
        """
        await self._workflow_api.delete1(
            workflow_id=workflow_id, archive_workflow=archive_workflow, **kwargs
        )

    # Workflow Information Operations
    async def get_workflow(
        self,
        workflow_id: str,
        include_tasks: Optional[bool] = None,
        summarize: Optional[bool] = None,
        **kwargs,
    ) -> WorkflowAdapter:
        """Get workflow execution status and details.

        Args:
            workflow_id: ID of the workflow
            include_tasks: If True, include task details in the response
            summarize: If True, return summarized information
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowAdapter instance with execution details

        Example:
            ```python
            workflow = await workflow_client.get_workflow("workflow-123", include_tasks=True)
            print(f"Status: {workflow.status}")
            print(f"Tasks: {len(workflow.tasks)}")
            ```
        """
        return await self._workflow_api.get_execution_status(
            workflow_id=workflow_id, include_tasks=include_tasks, summarize=summarize, **kwargs
        )

    async def get_workflow_status_summary(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
        **kwargs,
    ) -> WorkflowStatusAdapter:
        """Get workflow status summary.

        Args:
            workflow_id: ID of the workflow
            include_output: If True, include workflow output in the response
            include_variables: If True, include workflow variables in the response
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowStatusAdapter with status information

        Example:
            ```python
            status = await workflow_client.get_workflow_status_summary(
                "workflow-123",
                include_output=True,
                include_variables=True
            )
            print(f"Status: {status.status}")
            print(f"Output: {status.output}")
            ```
        """
        return await self._workflow_api.get_workflow_status_summary(
            workflow_id=workflow_id,
            include_output=include_output,
            include_variables=include_variables,
            **kwargs,
        )

    async def get_running_workflows(
        self,
        name: str,
        version: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        **kwargs,
    ) -> List[str]:
        """Get running workflow IDs.

        Args:
            name: Name of the workflow
            version: Optional workflow version filter
            start_time: Optional start time filter (epoch milliseconds)
            end_time: Optional end time filter (epoch milliseconds)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of running workflow IDs

        Example:
            ```python
            running = await workflow_client.get_running_workflows("order_processing")
            print(f"{len(running)} workflows currently running")
            ```
        """
        return await self._workflow_api.get_running_workflow(
            name=name, version=version, start_time=start_time, end_time=end_time, **kwargs
        )

    async def get_workflows_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
        **kwargs,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get workflows by correlation IDs.

        Args:
            workflow_name: Name of the workflow
            correlation_ids: List of correlation IDs to search for
            include_completed: If True, include completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping correlation IDs to lists of WorkflowAdapter instances

        Example:
            ```python
            workflows = await workflow_client.get_workflows_by_correlation_ids(
                "order_processing",
                ["batch-001", "batch-002"],
                include_completed=True
            )
            for corr_id, wfs in workflows.items():
                print(f"Correlation {corr_id}: {len(wfs)} workflows")
            ```
        """
        # Create correlation IDs search request
        search_request = CorrelationIdsSearchRequestAdapter(
            workflow_names=[workflow_name],
            correlation_ids=correlation_ids,
        )
        return await self._workflow_api.get_workflows1(
            correlation_ids_search_request=search_request,
            include_closed=include_completed,
            include_tasks=include_tasks,
            **kwargs,
        )

    async def get_workflows_by_correlation_ids_batch(
        self,
        batch_request: CorrelationIdsSearchRequestAdapter,
        include_completed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
        **kwargs,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get workflows by correlation IDs in batch.

        Args:
            batch_request: Batch request with workflow names and correlation IDs
            include_completed: If True, include completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping correlation IDs to lists of WorkflowAdapter instances

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.correlation_ids_search_request_adapter import CorrelationIdsSearchRequestAdapter

            batch = CorrelationIdsSearchRequestAdapter(
                workflow_names=["order_processing", "payment_processing"],
                correlation_ids=["batch-001", "batch-002"]
            )
            workflows = await workflow_client.get_workflows_by_correlation_ids_batch(batch)
            ```
        """
        return await self._workflow_api.get_workflows1(
            correlation_ids_search_request=batch_request,
            include_closed=include_completed,
            include_tasks=include_tasks,
            **kwargs,
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
        **kwargs,
    ) -> ScrollableSearchResultWorkflowSummaryAdapter:
        """Search for workflows based on payload and other parameters.

        Args:
            start: Start index for pagination
            size: Number of results to return
            sort: Sort specification
            free_text: Free text search query
            query: Structured query string (e.g., "status:FAILED")
            skip_cache: If True, skip cache and query database directly
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ScrollableSearchResultWorkflowSummaryAdapter with matching workflows

        Example:
            ```python
            # Search for failed workflows
            results = await workflow_client.search_workflows(
                query="status:FAILED",
                size=50
            )
            print(f"Found {results.total_hits} failed workflows")

            # Search by workflow name
            results = await workflow_client.search_workflows(
                query="workflowType:order_processing"
            )
            ```
        """
        return await self._workflow_api.search(
            start=start,
            size=size,
            sort=sort,
            free_text=free_text,
            query=query,
            skip_cache=skip_cache,
            **kwargs,
        )

    # Task Operations
    async def skip_task_from_workflow(
        self,
        workflow_id: str,
        task_reference_name: str,
        skip_task_request: Optional[SkipTaskRequestAdapter] = None,
        **kwargs,
    ) -> None:
        """Skip a task in a workflow.

        Args:
            workflow_id: ID of the workflow
            task_reference_name: Reference name of the task to skip
            skip_task_request: Optional skip request with input/output data
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.skip_task_from_workflow(
                "workflow-123",
                "manual_approval_task"
            )
            ```
        """
        await self._workflow_api.skip_task_from_workflow(
            workflow_id=workflow_id,
            task_reference_name=task_reference_name,
            skip_task_request=skip_task_request,  # type: ignore[arg-type]
            **kwargs,
        )

    async def jump_to_task(
        self,
        workflow_id: str,
        task_reference_name: str,
        workflow_input: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """Jump to a specific task in a workflow.

        Args:
            workflow_id: ID of the workflow
            task_reference_name: Reference name of the task to jump to
            workflow_input: Optional updated workflow input
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.jump_to_task(
                "workflow-123",
                "retry_payment_task",
                workflow_input={"retry_count": 1}
            )
            ```
        """
        await self._workflow_api.jump_to_task(
            workflow_id=workflow_id,
            task_reference_name=task_reference_name,
            request_body=workflow_input or {},
            **kwargs,
        )

    # Workflow State Operations
    async def update_workflow_state(
        self, workflow_id: str, workflow_state_update: WorkflowStateUpdateAdapter, **kwargs
    ) -> WorkflowAdapter:
        """Update workflow state (variables, tasks, etc.).

        Args:
            workflow_id: ID of the workflow
            workflow_state_update: State update containing variables and task updates
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowAdapter with updated state

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.workflow_state_update_adapter import WorkflowStateUpdateAdapter

            state_update = WorkflowStateUpdateAdapter(
                variables={"retry_count": 2, "last_error": "timeout"}
            )
            workflow = await workflow_client.update_workflow_state("workflow-123", state_update)
            ```
        """
        # Convert the adapter to dict for the API call
        if hasattr(workflow_state_update, "to_dict"):
            request_body: Dict[str, Any] = workflow_state_update.to_dict()
        else:
            request_body = cast(Dict[str, Any], workflow_state_update)
        return await self._workflow_api.update_workflow_state(
            workflow_id=workflow_id, request_body=request_body, **kwargs
        )

    async def update_workflow_and_task_state(
        self,
        workflow_id: str,
        workflow_state_update: WorkflowStateUpdateAdapter,
        request_id: str = str(uuid.uuid4()),
        wait_until_task_ref_name: Optional[str] = None,
        wait_for_seconds: Optional[int] = None,
        **kwargs,
    ) -> WorkflowRunAdapter:
        """Update workflow and task state synchronously.

        Args:
            workflow_id: ID of the workflow
            workflow_state_update: State update containing variables and task updates
            request_id: Unique request ID (default: generated UUID)
            wait_until_task_ref_name: Optional task to wait for
            wait_for_seconds: Maximum seconds to wait
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowRunAdapter with execution results

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.workflow_state_update_adapter import WorkflowStateUpdateAdapter

            state_update = WorkflowStateUpdateAdapter(
                variables={"step": "payment_processing"}
            )
            result = await workflow_client.update_workflow_and_task_state(
                "workflow-123",
                state_update,
                wait_for_seconds=30
            )
            ```
        """
        return await self._workflow_api.update_workflow_and_task_state(
            workflow_id=workflow_id,
            request_id=request_id,
            workflow_state_update=workflow_state_update,
            wait_until_task_ref=wait_until_task_ref_name,
            wait_for_seconds=wait_for_seconds,
            **kwargs,
        )

    # Advanced Operations
    async def test_workflow(
        self, test_request: WorkflowTestRequestAdapter, **kwargs
    ) -> WorkflowAdapter:
        """Test a workflow definition without actually executing it.

        Args:
            test_request: Workflow test request with definition and input
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowAdapter with simulated execution results

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.workflow_test_request_adapter import WorkflowTestRequestAdapter

            test_request = WorkflowTestRequestAdapter(
                workflow_def=workflow_definition,
                input={"test_data": "value"}
            )
            result = await workflow_client.test_workflow(test_request)
            print(f"Test result: {result.status}")
            ```
        """
        return await self._workflow_api.test_workflow(workflow_test_request=test_request, **kwargs)

    async def reset_workflow(self, workflow_id: str, **kwargs) -> None:
        """Reset a workflow execution to initial state.

        Args:
            workflow_id: ID of the workflow to reset
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.reset_workflow("workflow-123")
            ```
        """
        await self._workflow_api.reset_workflow(workflow_id=workflow_id, **kwargs)

    @deprecated("decide_workflow is deprecated; use decide instead")
    @typing_deprecated("decide_workflow is deprecated; use decide instead")
    async def decide_workflow(self, workflow_id: str) -> None:
        """Trigger workflow decision processing.

        .. deprecated::
            Use decide instead for consistent API interface.

        Args:
            workflow_id: ID of the workflow

        Returns:
            None

        Example:
            ```python
            await workflow_client.decide_workflow("workflow-123")
            ```
        """
        await self._workflow_api.decide(workflow_id=workflow_id)

    async def decide(self, workflow_id: str, **kwargs) -> None:
        """Trigger workflow decision processing.

        Forces the workflow to re-evaluate and process pending tasks.

        Args:
            workflow_id: ID of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.decide("workflow-123")
            ```
        """
        await self._workflow_api.decide(workflow_id=workflow_id, **kwargs)

    # Convenience Methods (for backward compatibility)
    async def execute_workflow_with_return_strategy(
        self,
        start_workflow_request: StartWorkflowRequestAdapter,
        request_id: str,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 30,
        **kwargs,
    ) -> WorkflowRunAdapter:
        """Execute a workflow synchronously (alias for execute_workflow).

        Args:
            start_workflow_request: Workflow start request
            request_id: Unique request ID
            wait_until_task_ref: Optional task to wait for
            wait_for_seconds: Seconds to wait (default: 30)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowRunAdapter with execution results

        Example:
            ```python
            result = await workflow_client.execute_workflow_with_return_strategy(
                start_request, request_id="req-123", wait_for_seconds=60
            )
            ```
        """
        return await self.execute_workflow(
            start_workflow_request=start_workflow_request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            **kwargs,
        )

    async def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: bool = False,
        include_tasks: bool = False,
        **kwargs,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get workflows by correlation IDs (alias).

        Args:
            workflow_name: Name of the workflow
            correlation_ids: List of correlation IDs
            include_completed: If True, include completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping correlation IDs to workflow lists

        Example:
            ```python
            workflows = await workflow_client.get_by_correlation_ids(
                "order_processing", ["batch-001"]
            )
            ```
        """
        return await self.get_workflows_by_correlation_ids(
            workflow_name=workflow_name,
            correlation_ids=correlation_ids,
            include_completed=include_completed,
            include_tasks=include_tasks,
            **kwargs,
        )

    async def get_by_correlation_ids_in_batch(
        self,
        batch_request: CorrelationIdsSearchRequestAdapter,
        include_completed: bool = False,
        include_tasks: bool = False,
        **kwargs,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get workflows by correlation IDs in batch (alias).

        Args:
            batch_request: Batch correlation search request
            include_completed: If True, include completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping correlation IDs to workflow lists

        Example:
            ```python
            workflows = await workflow_client.get_by_correlation_ids_in_batch(batch_request)
            ```
        """
        return await self.get_workflows_by_correlation_ids_batch(
            batch_request=batch_request,
            include_completed=include_completed,
            include_tasks=include_tasks,
            **kwargs,
        )

    async def search(
        self,
        start: int = 0,
        size: int = 100,
        free_text: str = "*",
        query: Optional[str] = None,
        skip_cache: Optional[bool] = None,
        **kwargs,
    ) -> ScrollableSearchResultWorkflowSummaryAdapter:
        """Search for workflows (alias for search_workflows).

        Args:
            start: Start index for pagination (default: 0)
            size: Number of results (default: 100)
            free_text: Free text search (default: "*")
            query: Structured query string
            skip_cache: If True, skip cache
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ScrollableSearchResultWorkflowSummaryAdapter with results

        Example:
            ```python
            results = await workflow_client.search(query="status:FAILED")
            ```
        """
        return await self.search_workflows(
            start=start,
            size=size,
            free_text=free_text,
            query=query,
            skip_cache=skip_cache,
            **kwargs,
        )

    async def remove_workflow(
        self, workflow_id: str, archive_workflow: Optional[bool] = None, **kwargs
    ) -> None:
        """Delete a workflow (alias for delete_workflow).

        Args:
            workflow_id: ID of the workflow to delete
            archive_workflow: If True, archive instead of delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.remove_workflow("workflow-123")
            ```
        """
        await self.delete_workflow(
            workflow_id=workflow_id, archive_workflow=archive_workflow, **kwargs
        )

    async def update_variables(
        self, workflow_id: str, variables: Optional[Dict[str, Any]] = None, **kwargs
    ) -> None:
        """Update workflow variables.

        Args:
            workflow_id: ID of the workflow
            variables: Dictionary of variables to update
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await workflow_client.update_variables(
                "workflow-123",
                {"retry_count": 3, "last_attempt": "2024-01-01"}
            )
            ```
        """
        if variables:
            state_update = WorkflowStateUpdateAdapter()
            state_update.variables = variables
            await self.update_workflow_state(
                workflow_id=workflow_id, workflow_state_update=state_update, **kwargs
            )

    async def update_state(
        self, workflow_id: str, update_request: WorkflowStateUpdateAdapter, **kwargs
    ) -> WorkflowRunAdapter:
        """Update workflow state (alias for update_workflow_and_task_state).

        Args:
            workflow_id: ID of the workflow
            update_request: State update request
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowRunAdapter with results

        Example:
            ```python
            result = await workflow_client.update_state("workflow-123", state_update)
            ```
        """
        return await self.update_workflow_and_task_state(
            workflow_id=workflow_id, workflow_state_update=update_request, **kwargs
        )

    async def get_workflow_status(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
        **kwargs,
    ) -> WorkflowStatusAdapter:
        """Get workflow status (alias for get_workflow_status_summary).

        Args:
            workflow_id: ID of the workflow
            include_output: If True, include output
            include_variables: If True, include variables
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowStatusAdapter with status

        Example:
            ```python
            status = await workflow_client.get_workflow_status("workflow-123")
            ```
        """
        return await self.get_workflow_status_summary(
            workflow_id=workflow_id,
            include_output=include_output,
            include_variables=include_variables,
            **kwargs,
        )

    async def execute_workflow_as_api(
        self,
        name: str,
        request_body: Dict[str, Dict[str, Any]],
        version: Optional[int] = None,
        request_id: Optional[str] = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: Optional[int] = None,
        x_idempotency_key: Optional[str] = None,
        x_on_conflict: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a workflow as an API call (POST method).

        Args:
            name: Name of the workflow
            request_body: Request body with workflow input
            version: Optional workflow version
            request_id: Optional unique request ID
            wait_until_task_ref: Optional task to wait for
            wait_for_seconds: Maximum seconds to wait
            x_idempotency_key: Optional idempotency key
            x_on_conflict: Optional conflict resolution strategy
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary with workflow execution results

        Example:
            ```python
            result = await workflow_client.execute_workflow_as_api(
                "order_processing",
                {"input": {"order_id": "12345"}},
                wait_for_seconds=30
            )
            ```
        """
        return await self._workflow_api.execute_workflow_as_api(
            name=name,
            request_body=request_body,
            version=version,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            x_idempotency_key=x_idempotency_key,
            x_on_conflict=x_on_conflict,
            **kwargs,
        )

    async def execute_workflow_as_get_api(
        self,
        name: str,
        version: Optional[int] = None,
        request_id: Optional[str] = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: Optional[int] = None,
        x_idempotency_key: Optional[str] = None,
        x_on_conflict: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a workflow as a GET API call.

        Args:
            name: Name of the workflow
            version: Optional workflow version
            request_id: Optional unique request ID
            wait_until_task_ref: Optional task to wait for
            wait_for_seconds: Maximum seconds to wait
            x_idempotency_key: Optional idempotency key
            x_on_conflict: Optional conflict resolution strategy
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary with workflow execution results

        Example:
            ```python
            result = await workflow_client.execute_workflow_as_get_api(
                "simple_workflow",
                version=1,
                wait_for_seconds=30
            )
            ```
        """
        return await self._workflow_api.execute_workflow_as_get_api(
            name=name,
            version=version,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            x_idempotency_key=x_idempotency_key,
            x_on_conflict=x_on_conflict,
            **kwargs,
        )

    async def get_execution_status_task_list(
        self,
        workflow_id: str,
        start: Optional[int] = None,
        count: Optional[int] = None,
        status: Optional[List[str]] = None,
        **kwargs,
    ) -> TaskListSearchResultSummaryAdapter:
        """Get the execution status task list for a workflow.

        Args:
            workflow_id: ID of the workflow
            start: Start index for pagination
            count: Number of tasks to return
            status: Optional list of task statuses to filter by
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            TaskListSearchResultSummaryAdapter with task information

        Example:
            ```python
            tasks = await workflow_client.get_execution_status_task_list(
                "workflow-123",
                status=["FAILED", "TIMED_OUT"]
            )
            ```
        """
        return await self._workflow_api.get_execution_status_task_list(
            workflow_id=workflow_id, start=start, count=count, status=status, **kwargs
        )

    async def get_workflows(
        self,
        name: str,
        request_body: List[str],
        include_closed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
        **kwargs,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get workflows by workflow IDs.

        Args:
            name: Name of the workflow
            request_body: List of workflow IDs to retrieve
            include_closed: If True, include closed/completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping workflow IDs to workflow lists

        Example:
            ```python
            workflows = await workflow_client.get_workflows(
                "order_processing",
                ["wf-123", "wf-456"],
                include_tasks=True
            )
            ```
        """
        return await self._workflow_api.get_workflows(
            name=name,
            request_body=request_body,
            include_closed=include_closed,
            include_tasks=include_tasks,
            **kwargs,
        )

    async def get_workflows_by_correlation_id(
        self,
        name: str,
        correlation_id: str,
        include_closed: Optional[bool] = None,
        include_tasks: Optional[bool] = None,
        **kwargs,
    ) -> List[WorkflowAdapter]:
        """Get workflows by single correlation ID.

        Args:
            name: Name of the workflow
            correlation_id: Correlation ID to search for
            include_closed: If True, include closed/completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowAdapter instances

        Example:
            ```python
            workflows = await workflow_client.get_workflows_by_correlation_id(
                "order_processing",
                "batch-001",
                include_completed=True
            )
            ```
        """
        return await self._workflow_api.get_workflows2(
            name=name,
            correlation_id=correlation_id,
            include_closed=include_closed,
            include_tasks=include_tasks,
            **kwargs,
        )

    async def upgrade_running_workflow_to_version(
        self, workflow_id: str, upgrade_workflow_request: UpgradeWorkflowRequestAdapter, **kwargs
    ) -> None:
        """Upgrade a running workflow to a new version.

        Args:
            workflow_id: ID of the workflow to upgrade
            upgrade_workflow_request: Upgrade request specifying target version
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upgrade_workflow_request_adapter import UpgradeWorkflowRequestAdapter

            upgrade_request = UpgradeWorkflowRequestAdapter(version=2)
            await workflow_client.upgrade_running_workflow_to_version(
                "workflow-123",
                upgrade_request
            )
            ```
        """
        await self._workflow_api.upgrade_running_workflow_to_version(
            workflow_id=workflow_id, upgrade_workflow_request=upgrade_workflow_request, **kwargs
        )
