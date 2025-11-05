from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.client.configuration.configuration import Configuration
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
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.workflow_client import WorkflowClient


class OrkesWorkflowClient(OrkesBaseClient, WorkflowClient):
    def __init__(self, configuration: Configuration):
        """Initialize the OrkesWorkflowClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            workflow_client = OrkesWorkflowClient(config)
            ```
        """
        super().__init__(configuration)

    @deprecated(
        "start_workflow_by_name is deprecated; use start_workflow_by_name_validated instead"
    )
    @typing_deprecated(
        "start_workflow_by_name is deprecated; use start_workflow_by_name_validated instead"
    )
    def start_workflow_by_name(
        self,
        name: str,
        input: Dict[str, object],
        version: Optional[int] = None,
        correlationId: Optional[str] = None,
        priority: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Start a workflow by name with input data.

        .. deprecated::
            Use start_workflow_by_name_validated() instead.

        Args:
            name: Name of the workflow to start
            input: Input data for the workflow as dictionary
            version: Optional workflow version
            correlationId: Optional correlation ID
            priority: Optional priority level
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow ID as string
        """
        if version:
            kwargs.update({"version": version})
        if correlationId:
            kwargs.update({"correlation_id": correlationId})
        if priority:
            kwargs.update({"priority": priority})

        return self._workflow_api.start_workflow1(input, name, **kwargs)

    def start_workflow_by_name_validated(
        self,
        name: str,
        input: Dict[str, object],
        version: Optional[int] = None,
        correlation_id: Optional[str] = None,
        priority: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Start a workflow by name with input data.

        Args:
            name: Name of the workflow to start
            input: Input data for the workflow as dictionary
            version: Optional workflow version. If None, uses latest version
            correlation_id: Optional correlation ID for tracking related workflows
            priority: Optional priority level (0-99, higher is more priority)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow ID as string

        Example:
            ```python
            # Start a simple workflow
            workflow_id = workflow_client.start_workflow_by_name_validated(
                "order_processing",
                {"order_id": "12345", "customer_id": "cust-999"}
            )
            print(f"Started workflow: {workflow_id}")

            # Start with priority and correlation
            workflow_id = workflow_client.start_workflow_by_name_validated(
                "urgent_order_processing",
                {"order_id": "99999"},
                version=2,
                priority=10,
                correlation_id="batch-2024-01"
            )
            ```
        """
        if version:
            kwargs.update({"version": version})
        if correlation_id:
            kwargs.update({"correlation_id": correlation_id})
        if priority:
            kwargs.update({"priority": priority})

        return self._workflow_api.start_workflow1(body=input, name=name, **kwargs)

    def start_workflow(self, start_workflow_request: StartWorkflowRequest, **kwargs) -> str:
        """Start a workflow using a StartWorkflowRequest object.

        Args:
            start_workflow_request: Workflow start request with all parameters
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow ID as string

        Example:
            ```python
            from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

            request = StartWorkflowRequest(
                name="order_processing",
                version=1,
                input={"order_id": "12345"},
                correlation_id="batch-001",
                priority=5
            )
            workflow_id = workflow_client.start_workflow(request)
            ```
        """
        return self._workflow_api.start_workflow(body=start_workflow_request, **kwargs)

    def execute_workflow(
        self,
        start_workflow_request: StartWorkflowRequest,
        request_id: Optional[str] = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 30,
        **kwargs,
    ) -> WorkflowRun:
        """Execute a workflow synchronously and wait for completion.

        Args:
            start_workflow_request: Workflow start request
            request_id: Optional request ID for tracking
            wait_until_task_ref: Wait until this task reference is reached
            wait_for_seconds: How long to wait for completion (default 30)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowRun with execution result

        Example:
            ```python
            from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

            request = StartWorkflowRequest(
                name="order_processing",
                version=1,
                input={"order_id": "12345"}
            )

            result = workflow_client.execute_workflow(
                request,
                wait_for_seconds=60
            )

            print(f"Workflow status: {result.status}")
            print(f"Output: {result.output}")
            ```
        """
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
        """Execute a workflow synchronously with optional reactive features.

        Args:
            start_workflow_request: StartWorkflowRequest containing workflow details
            request_id: Optional request ID for tracking
            wait_until_task_ref: Wait until this task reference is reached
            wait_for_seconds: How long to wait for completion (default 30)
            consistency: Workflow consistency level - 'DURABLE' or 'SYNCHRONOUS' or 'REGION_DURABLE'
            return_strategy: Return strategy - 'TARGET_WORKFLOW' or 'BLOCKING_WORKFLOW' or 'BLOCKING_TASK' or 'BLOCKING_TASK_INPUT'
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowRun with the workflow execution result

        Example:
            ```python
            from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

            request = StartWorkflowRequest(
                name="data_pipeline",
                version=1,
                input={"dataset": "customers"}
            )

            result = workflow_client.execute_workflow_with_return_strategy(
                request,
                wait_for_seconds=120,
                consistency="SYNCHRONOUS",
                return_strategy="TARGET_WORKFLOW"
            )
            ```
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
        """Pause a running workflow.

        Args:
            workflow_id: ID of the workflow to pause
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.pause_workflow("workflow-123")
            ```
        """
        self._workflow_api.pause_workflow(workflow_id=workflow_id, **kwargs)

    def resume_workflow(self, workflow_id: str, **kwargs) -> None:
        """Resume a paused workflow.

        Args:
            workflow_id: ID of the workflow to resume
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.resume_workflow("workflow-123")
            ```
        """
        self._workflow_api.resume_workflow(workflow_id=workflow_id, **kwargs)

    def restart_workflow(
        self, workflow_id: str, use_latest_def: Optional[bool] = False, **kwargs
    ) -> None:
        """Restart a workflow from the beginning.

        Args:
            workflow_id: ID of the workflow to restart
            use_latest_def: If True, use latest workflow definition
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Restart with current definition
            workflow_client.restart_workflow("workflow-123")

            # Restart with latest definition
            workflow_client.restart_workflow("workflow-123", use_latest_def=True)
            ```
        """
        if use_latest_def:
            kwargs.update({"use_latest_definitions": use_latest_def})

        self._workflow_api.restart(workflow_id=workflow_id, **kwargs)

    def rerun_workflow(
        self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequest, **kwargs
    ) -> str:
        """Rerun a workflow from a specific task.

        Args:
            workflow_id: ID of the workflow to rerun
            rerun_workflow_request: Configuration for the rerun
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            New workflow ID as string

        Example:
            ```python
            from conductor.client.http.models.rerun_workflow_request import RerunWorkflowRequest

            rerun_request = RerunWorkflowRequest(
                re_run_from_task_id="task-456"
            )

            new_workflow_id = workflow_client.rerun_workflow("workflow-123", rerun_request)
            print(f"Rerun workflow ID: {new_workflow_id}")
            ```
        """
        rerun_workflow_request.re_run_from_workflow_id = workflow_id
        return self._workflow_api.rerun(
            body=rerun_workflow_request, workflow_id=workflow_id, **kwargs
        )

    def retry_workflow(
        self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = False, **kwargs
    ) -> None:
        """Retry a failed workflow.

        Args:
            workflow_id: ID of the workflow to retry
            resume_subworkflow_tasks: If True, resume subworkflow tasks
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.retry_workflow("workflow-123", resume_subworkflow_tasks=True)
            ```
        """
        if resume_subworkflow_tasks:
            kwargs.update({"resume_subworkflow_tasks": resume_subworkflow_tasks})
        self._workflow_api.retry(workflow_id=workflow_id, **kwargs)

    def terminate_workflow(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        trigger_failure_workflow: bool = False,
        **kwargs,
    ) -> None:
        """Terminate a running workflow.

        Args:
            workflow_id: ID of the workflow to terminate
            reason: Optional reason for termination
            trigger_failure_workflow: If True, trigger the failure workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.terminate_workflow(
                "workflow-123",
                reason="Cancelled by user",
                trigger_failure_workflow=True
            )
            ```
        """
        if reason:
            kwargs.update({"reason": reason})
        if trigger_failure_workflow:
            kwargs.update({"trigger_failure_workflow": trigger_failure_workflow})
        self._workflow_api.terminate1(workflow_id=workflow_id, **kwargs)

    def get_workflow(
        self, workflow_id: str, include_tasks: Optional[bool] = True, **kwargs
    ) -> Workflow:
        """Get workflow execution status and details.

        Args:
            workflow_id: ID of the workflow
            include_tasks: If True, include task details in the response
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow instance with execution details

        Example:
            ```python
            workflow = workflow_client.get_workflow("workflow-123", include_tasks=True)
            print(f"Status: {workflow.status}")
            print(f"Tasks: {len(workflow.tasks)}")
            ```
        """
        if include_tasks:
            kwargs.update({"include_tasks": include_tasks})
        return self._workflow_api.get_execution_status(workflow_id=workflow_id, **kwargs)

    def get_workflow_status(
        self,
        workflow_id: str,
        include_output: Optional[bool] = None,
        include_variables: Optional[bool] = None,
        **kwargs,
    ) -> WorkflowStatus:
        """Get workflow status summary.

        Args:
            workflow_id: ID of the workflow
            include_output: If True, include workflow output in the response
            include_variables: If True, include workflow variables in the response
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowStatus with status information

        Example:
            ```python
            status = workflow_client.get_workflow_status(
                "workflow-123",
                include_output=True,
                include_variables=True
            )
            print(f"Status: {status.status}")
            print(f"Output: {status.output}")
            ```
        """
        if include_output is not None:
            kwargs.update({"include_output": include_output})
        if include_variables is not None:
            kwargs.update({"include_variables": include_variables})
        return self._workflow_api.get_workflow_status_summary(workflow_id=workflow_id, **kwargs)

    def delete_workflow(self, workflow_id: str, archive_workflow: Optional[bool] = True, **kwargs):
        """Delete a workflow from the system.

        Args:
            workflow_id: ID of the workflow to delete
            archive_workflow: If True, archive instead of permanently deleting
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Archive the workflow
            workflow_client.delete_workflow("workflow-123", archive_workflow=True)

            # Permanently delete
            workflow_client.delete_workflow("workflow-123", archive_workflow=False)
            ```
        """
        self._workflow_api.delete1(
            workflow_id=workflow_id, archive_workflow=archive_workflow, **kwargs
        )

    def skip_task_from_workflow(
        self,
        workflow_id: str,
        task_reference_name: str,
        request: Optional[SkipTaskRequest],
        **kwargs,
    ) -> None:
        """Skip a task in a running workflow.

        Args:
            workflow_id: ID of the workflow
            task_reference_name: Reference name of the task to skip
            request: Optional skip task request with parameters
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.skip_task_request import SkipTaskRequest

            skip_request = SkipTaskRequest(
                task_input={"skipped": True},
                task_output={"result": "skipped"}
            )

            workflow_client.skip_task_from_workflow(
                "workflow-123",
                "send_email",
                skip_request
            )
            ```
        """
        self._workflow_api.skip_task_from_workflow(
            workflow_id=workflow_id, task_reference_name=task_reference_name, body=request, **kwargs
        )

    def test_workflow(self, test_request: WorkflowTestRequest, **kwargs) -> Workflow:
        """Test a workflow definition without persisting it.

        Args:
            test_request: Workflow test request with definition and input
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Workflow instance with test execution result

        Example:
            ```python
            from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
            from conductor.client.http.models.workflow_def import WorkflowDef

            workflow_def = WorkflowDef(
                name="test_workflow",
                version=1,
                tasks=[...]
            )

            test_request = WorkflowTestRequest(
                workflow_def=workflow_def,
                input={"test": "data"}
            )

            result = workflow_client.test_workflow(test_request)
            print(f"Test result: {result.status}")
            ```
        """
        return self._workflow_api.test_workflow(body=test_request, **kwargs)

    def search(
        self,
        start: int = 0,
        size: int = 100,
        free_text: str = "*",
        query: Optional[str] = None,
        query_id: Optional[str] = None,
        skip_cache: bool = False,
        **kwargs,
    ) -> ScrollableSearchResultWorkflowSummary:
        """Search for workflows.

        Args:
            start: Start index for pagination
            size: Number of results to return
            free_text: Free text search query
            query: Structured query string
            query_id: Optional query ID for cached searches
            skip_cache: If True, skip cache and fetch fresh results
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ScrollableSearchResultWorkflowSummary with search results

        Example:
            ```python
            results = workflow_client.search(
                start=0,
                size=20,
                free_text="order_processing",
                query="status='FAILED'"
            )

            print(f"Total: {results.total_hits}")
            for workflow in results.results:
                print(f"Workflow: {workflow.workflow_id}, Status: {workflow.status}")
            ```
        """
        if start is not None:
            kwargs.update({"start": start})
        if size is not None:
            kwargs.update({"size": size})
        if free_text is not None:
            kwargs.update({"free_text": free_text})
        if query is not None:
            kwargs.update({"query": query})
        if query_id is not None:
            kwargs.update({"query_id": query_id})
        if skip_cache is not None:
            kwargs.update({"skip_cache": skip_cache})

        return self._workflow_api.search(**kwargs)

    def get_by_correlation_ids_in_batch(
        self,
        batch_request: CorrelationIdsSearchRequest,
        include_completed: bool = False,
        include_tasks: bool = False,
        **kwargs,
    ) -> Dict[str, List[Workflow]]:
        """Get workflows by correlation IDs in batch.

        Given the list of correlation ids and list of workflow names, find and return workflows.
        Returns a map with key as correlationId and value as a list of Workflows.
        When include_completed is set to true, the return value also includes workflows that are
        completed otherwise only running workflows are returned.

        Args:
            batch_request: Correlation IDs search request
            include_completed: If True, include completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping correlation IDs to lists of Workflow instances

        Example:
            ```python
            from conductor.client.http.models.correlation_ids_search_request import CorrelationIdsSearchRequest

            batch_request = CorrelationIdsSearchRequest(
                workflow_names=["order_processing"],
                correlation_ids=["batch-001", "batch-002"]
            )

            workflows = workflow_client.get_by_correlation_ids_in_batch(
                batch_request,
                include_completed=True
            )

            for corr_id, wf_list in workflows.items():
                print(f"Correlation: {corr_id}, Workflows: {len(wf_list)}")
            ```
        """
        if include_tasks:
            kwargs.update({"include_tasks": include_tasks})
        if include_completed:
            kwargs.update({"include_closed": include_completed})
        return self._workflow_api.get_workflows1(body=batch_request, **kwargs)

    def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: bool = False,
        include_tasks: bool = False,
        **kwargs,
    ) -> Dict[str, List[Workflow]]:
        """Get workflows by correlation IDs.

        Lists workflows for the given correlation id list.

        Args:
            workflow_name: Name of the workflow
            correlation_ids: List of correlation IDs to search for
            include_completed: If True, include completed workflows
            include_tasks: If True, include task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping correlation IDs to lists of Workflow instances

        Example:
            ```python
            workflows = workflow_client.get_by_correlation_ids(
                "order_processing",
                ["batch-001", "batch-002"],
                include_completed=True
            )

            for corr_id, wf_list in workflows.items():
                print(f"Correlation: {corr_id}, Count: {len(wf_list)}")
            ```
        """
        if include_tasks:
            kwargs.update({"include_tasks": include_tasks})
        if include_completed:
            kwargs.update({"include_closed": include_completed})

        return self._workflow_api.get_workflows(body=correlation_ids, name=workflow_name, **kwargs)

    def remove_workflow(self, workflow_id: str, **kwargs):
        """Remove a workflow from the system.

        Args:
            workflow_id: ID of the workflow to remove
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.remove_workflow("workflow-123")
            ```
        """
        self._workflow_api.delete1(workflow_id=workflow_id, **kwargs)

    def update_variables(
        self, workflow_id: str, variables: Optional[Dict[str, object]] = None, **kwargs
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
            workflow_client.update_variables(
                "workflow-123",
                {"status": "in_progress", "count": 5}
            )
            ```
        """
        variables = variables or {}
        self._workflow_api.update_workflow_state(body=variables, workflow_id=workflow_id, **kwargs)

    def update_state(
        self,
        workflow_id: str,
        update_request: WorkflowStateUpdate,
        wait_until_task_ref_names: Optional[List[str]] = None,
        wait_for_seconds: Optional[int] = None,
        **kwargs,
    ) -> WorkflowRun:
        """Update workflow and task state.

        Args:
            workflow_id: ID of the workflow
            update_request: State update request
            wait_until_task_ref_names: Wait until these task references are reached
            wait_for_seconds: How long to wait for completion
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowRun with updated state

        Example:
            ```python
            from conductor.client.http.models.workflow_state_update import WorkflowStateUpdate

            update_request = WorkflowStateUpdate(
                variables={"status": "updated"},
                task_ref_to_update_input={"task1": {"input": "new_value"}}
            )

            result = workflow_client.update_state(
                "workflow-123",
                update_request,
                wait_for_seconds=30
            )
            ```
        """
        request_id = str(uuid.uuid4())
        if wait_until_task_ref_names is not None:
            kwargs.update({"wait_until_task_ref": ",".join(wait_until_task_ref_names)})
        if wait_for_seconds is not None:
            kwargs.update({"wait_for_seconds": wait_for_seconds})

        return self._workflow_api.update_workflow_and_task_state(
            body=update_request, workflow_id=workflow_id, request_id=request_id, **kwargs
        )

    def decide(self, workflow_id: str, **kwargs) -> None:
        """Trigger workflow decision making.

        Args:
            workflow_id: ID of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.decide("workflow-123")
            ```
        """
        self._workflow_api.decide(workflow_id=workflow_id, **kwargs)

    def execute_workflow_as_api(
        self, body: Dict[str, object], name: str, **kwargs
    ) -> Dict[str, Any]:
        """Execute a workflow as an API call.

        Args:
            body: Input data for the workflow
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary with execution result

        Example:
            ```python
            result = workflow_client.execute_workflow_as_api(
                {"order_id": "12345"},
                "order_processing"
            )
            print(f"Result: {result}")
            ```
        """
        return self._workflow_api.execute_workflow_as_api(body=body, name=name, **kwargs)

    def execute_workflow_as_get_api(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a workflow as a GET API call.

        Args:
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary with execution result

        Example:
            ```python
            result = workflow_client.execute_workflow_as_get_api("status_check")
            print(f"Result: {result}")
            ```
        """
        return self._workflow_api.execute_workflow_as_get_api(name=name, **kwargs)

    def get_execution_status_task_list(
        self, workflow_id: str, **kwargs
    ) -> TaskListSearchResultSummary:
        """Get task list for a workflow execution.

        Args:
            workflow_id: ID of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            TaskListSearchResultSummary with task list

        Example:
            ```python
            tasks = workflow_client.get_execution_status_task_list("workflow-123")
            print(f"Total tasks: {tasks.total_hits}")
            ```
        """
        return self._workflow_api.get_execution_status_task_list(workflow_id=workflow_id, **kwargs)

    def get_running_workflow(self, name: str, **kwargs) -> List[str]:
        """Get running workflow IDs for a workflow name.

        Args:
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of running workflow IDs

        Example:
            ```python
            running = workflow_client.get_running_workflow("order_processing")
            print(f"{len(running)} workflows currently running")
            ```
        """
        return self._workflow_api.get_running_workflow(name=name, **kwargs)

    def get_workflows_by_correlation_id(
        self, name: str, correlation_id: str, **kwargs
    ) -> List[Workflow]:
        """Get workflows by correlation ID.

        Args:
            name: Name of the workflow
            correlation_id: Correlation ID to search for
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Workflow instances

        Example:
            ```python
            workflows = workflow_client.get_workflows_by_correlation_id(
                "order_processing",
                "batch-001"
            )

            for workflow in workflows:
                print(f"Workflow: {workflow.workflow_id}, Status: {workflow.status}")
            ```
        """
        return self._workflow_api.get_workflows2(name=name, correlation_id=correlation_id, **kwargs)

    def jump_to_task(
        self, body: Dict[str, object], workflow_id: str, task_reference_name: str, **kwargs
    ) -> None:
        """Jump to a specific task in a workflow.

        Args:
            body: Input data for the task
            workflow_id: ID of the workflow
            task_reference_name: Reference name of the task to jump to
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.jump_to_task(
                {"skip_validation": True},
                "workflow-123",
                "process_payment"
            )
            ```
        """
        if task_reference_name is not None:
            kwargs.update({"task_reference_name": task_reference_name})

        return self._workflow_api.jump_to_task(body=body, workflow_id=workflow_id, **kwargs)

    def reset_workflow(self, workflow_id: str, **kwargs) -> None:
        """Reset a workflow to initial state.

        Args:
            workflow_id: ID of the workflow to reset
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_client.reset_workflow("workflow-123")
            ```
        """
        self._workflow_api.reset_workflow(workflow_id=workflow_id, **kwargs)

    def upgrade_running_workflow_to_version(
        self, body: UpgradeWorkflowRequest, workflow_id: str, **kwargs
    ) -> None:
        """Upgrade a running workflow to a new version.

        Args:
            body: Upgrade workflow request
            workflow_id: ID of the workflow to upgrade
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.upgrade_workflow_request import UpgradeWorkflowRequest

            upgrade_request = UpgradeWorkflowRequest(
                version=2,
                name="order_processing"
            )

            workflow_client.upgrade_running_workflow_to_version(upgrade_request, "workflow-123")
            ```
        """
        return self._workflow_api.upgrade_running_workflow_to_version(
            body=body, workflow_id=workflow_id, **kwargs
        )
