from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

from pydantic import Field, StrictBool, StrictFloat, StrictInt, StrictStr, validate_call

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
from conductor.asyncio_client.adapters.utils import (
    convert_dict_to_adapter,
    convert_list_to_adapter,
    convert_to_adapter,
)
from conductor.asyncio_client.http.api import WorkflowResourceApi


class WorkflowResourceApiAdapter:
    def __init__(self, api_client: ApiClient):
        self._api = WorkflowResourceApi(api_client)

    async def decide(
        self,
        workflow_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Starts the decision task for a workflow"""
        await self._api.decide(
            workflow_id,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def delete1(
        self,
        workflow_id: StrictStr,
        archive_workflow: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Removes the workflow from the system"""
        await self._api.delete1(
            workflow_id,
            archive_workflow,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def execute_workflow(
        self,
        name: StrictStr,
        version: StrictInt,
        request_id: StrictStr,
        start_workflow_request: StartWorkflowRequestAdapter,
        wait_until_task_ref: Optional[StrictStr] = None,
        wait_for_seconds: Optional[StrictInt] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> WorkflowRunAdapter:
        """Execute a workflow synchronously"""
        result = await self._api.execute_workflow(
            name,
            version,
            request_id,
            start_workflow_request,
            wait_until_task_ref,
            wait_for_seconds,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, WorkflowRunAdapter)

    async def execute_workflow_as_api(
        self,
        name: StrictStr,
        request_body: Dict[str, Dict[str, Any]],
        version: Optional[StrictInt] = None,
        request_id: Optional[StrictStr] = None,
        wait_until_task_ref: Optional[StrictStr] = None,
        wait_for_seconds: Optional[StrictInt] = None,
        x_idempotency_key: Optional[StrictStr] = None,
        x_on_conflict: Optional[StrictStr] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> Dict[str, object]:
        """Execute a workflow synchronously with input and outputs"""
        return await self._api.execute_workflow_as_api(
            name,
            request_body,
            version,
            request_id,
            wait_until_task_ref,
            wait_for_seconds,
            x_idempotency_key,
            x_on_conflict,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def execute_workflow_as_get_api(
        self,
        name: StrictStr,
        version: Optional[StrictInt] = None,
        request_id: Optional[StrictStr] = None,
        wait_until_task_ref: Optional[StrictStr] = None,
        wait_for_seconds: Optional[StrictInt] = None,
        x_idempotency_key: Optional[StrictStr] = None,
        x_on_conflict: Optional[StrictStr] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> Dict[str, object]:
        """(Deprecated) Execute a workflow synchronously with input and outputs using get api"""
        return await self._api.execute_workflow_as_get_api(
            name,
            version,
            request_id,
            wait_until_task_ref,
            wait_for_seconds,
            x_idempotency_key,
            x_on_conflict,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def get_execution_status(
        self,
        workflow_id: StrictStr,
        include_tasks: Optional[StrictBool] = None,
        summarize: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> WorkflowAdapter:
        """Get the execution status of a workflow"""
        result = await self._api.get_execution_status(
            workflow_id,
            include_tasks,
            summarize,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, WorkflowAdapter)

    async def get_execution_status_task_list(
        self,
        workflow_id: StrictStr,
        start: Optional[StrictInt] = None,
        count: Optional[StrictInt] = None,
        status: Optional[List[StrictStr]] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> TaskListSearchResultSummaryAdapter:
        """Get the execution status of a workflow's task list"""
        result = await self._api.get_execution_status_task_list(
            workflow_id,
            start,
            count,
            status,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, TaskListSearchResultSummaryAdapter)

    async def get_workflow_status_summary(
        self,
        workflow_id: StrictStr,
        include_output: Optional[StrictBool] = None,
        include_variables: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> WorkflowStatusAdapter:
        """Get the status summary of a workflow"""
        result = await self._api.get_workflow_status_summary(
            workflow_id,
            include_output,
            include_variables,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, WorkflowStatusAdapter)

    async def get_running_workflow(
        self,
        name: StrictStr,
        version: Optional[StrictInt] = None,
        start_time: Optional[StrictInt] = None,
        end_time: Optional[StrictInt] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> List[str]:
        """Get the running workflows"""
        return await self._api.get_running_workflow(
            name,
            version,
            start_time,
            end_time,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def get_workflows(
        self,
        name: StrictStr,
        request_body: List[StrictStr],
        include_closed: Optional[StrictBool] = None,
        include_tasks: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get the workflows"""
        result = await self._api.get_workflows(
            name,
            request_body,
            include_closed,
            include_tasks,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_dict_to_adapter(result, WorkflowAdapter)

    async def get_workflows1(
        self,
        correlation_ids_search_request: CorrelationIdsSearchRequestAdapter,
        include_closed: Optional[StrictBool] = None,
        include_tasks: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> Dict[str, List[WorkflowAdapter]]:
        """Get the workflows"""
        result = await self._api.get_workflows1(
            correlation_ids_search_request,
            include_closed,
            include_tasks,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_dict_to_adapter(result, WorkflowAdapter)

    async def get_workflows2(
        self,
        name: StrictStr,
        correlation_id: StrictStr,
        include_closed: Optional[StrictBool] = None,
        include_tasks: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> List[WorkflowAdapter]:
        """Get the workflows"""
        result = await self._api.get_workflows2(
            name,
            correlation_id,
            include_closed,
            include_tasks,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_list_to_adapter(result, WorkflowAdapter)

    async def jump_to_task(
        self,
        workflow_id: StrictStr,
        task_reference_name: StrictStr,
        request_body: Dict[str, Dict[str, Any]],
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Jump to task"""
        await self._api.jump_to_task(
            workflow_id,
            task_reference_name,
            request_body,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def pause_workflow(
        self,
        workflow_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Pauses the workflow"""
        await self._api.pause_workflow(
            workflow_id,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def search(
        self,
        start: Optional[StrictInt] = None,
        size: Optional[StrictInt] = None,
        sort: Optional[StrictStr] = None,
        free_text: Optional[StrictStr] = None,
        query: Optional[StrictStr] = None,
        skip_cache: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ScrollableSearchResultWorkflowSummaryAdapter:
        """Search for workflows"""
        result = await self._api.search(
            start,
            size,
            sort,
            free_text,
            query,
            skip_cache,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, ScrollableSearchResultWorkflowSummaryAdapter)

    async def skip_task_from_workflow(
        self,
        workflow_id: StrictStr,
        task_reference_name: StrictStr,
        skip_task_request: SkipTaskRequestAdapter,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Skips a given task from a current running workflow"""
        await self._api.skip_task_from_workflow(
            workflow_id,
            task_reference_name,
            skip_task_request,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def start_workflow(
        self,
        start_workflow_request: StartWorkflowRequestAdapter,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> str:
        """Start a new workflow with StartWorkflowRequest, which allows task to be executed in a domain"""
        return await self._api.start_workflow(
            start_workflow_request,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def rerun(
        self,
        workflow_id: StrictStr,
        rerun_workflow_request: RerunWorkflowRequestAdapter,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> str:
        """Rerun a workflow"""
        return await self._api.rerun(
            workflow_id,
            rerun_workflow_request,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def reset_workflow(
        self,
        workflow_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Resets callback times of all non-terminal SIMPLE tasks to 0"""
        await self._api.reset_workflow(
            workflow_id,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def restart(
        self,
        workflow_id: StrictStr,
        use_latest_definitions: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Restart a workflow"""
        await self._api.restart(
            workflow_id,
            use_latest_definitions,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def resume_workflow(
        self,
        workflow_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Resumes the workflow"""
        await self._api.resume_workflow(
            workflow_id,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def retry(
        self,
        workflow_id: StrictStr,
        resume_subworkflow_tasks: Optional[StrictBool] = None,
        retry_if_retried_by_parent: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Retries the last failed task"""
        await self._api.retry(
            workflow_id,
            resume_subworkflow_tasks,
            retry_if_retried_by_parent,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def update_workflow_and_task_state(
        self,
        workflow_id: StrictStr,
        request_id: StrictStr,
        workflow_state_update: WorkflowStateUpdateAdapter,
        wait_until_task_ref: Optional[StrictStr] = None,
        wait_for_seconds: Optional[StrictInt] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> WorkflowRunAdapter:
        """Update the workflow and task state"""
        result = await self._api.update_workflow_and_task_state(
            workflow_id,
            request_id,
            workflow_state_update,
            wait_until_task_ref,
            wait_for_seconds,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, WorkflowRunAdapter)

    async def test_workflow(
        self,
        workflow_test_request: WorkflowTestRequestAdapter,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> WorkflowAdapter:
        """Test a workflow"""
        result = await self._api.test_workflow(
            workflow_test_request,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, WorkflowAdapter)

    async def update_workflow_state(
        self,
        workflow_id: StrictStr,
        request_body: Dict[str, Dict[str, Any]],
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> WorkflowAdapter:
        """Update the workflow state"""
        result = await self._api.update_workflow_state(
            workflow_id,
            request_body,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, WorkflowAdapter)

    async def upgrade_running_workflow_to_version(
        self,
        workflow_id: StrictStr,
        upgrade_workflow_request: UpgradeWorkflowRequestAdapter,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Upgrade running workflow to newer version"""
        await self._api.upgrade_running_workflow_to_version(
            workflow_id,
            upgrade_workflow_request,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    @validate_call
    async def start_workflow1(
        self,
        name: StrictStr,
        request_body: Dict[str, Any],
        version: Optional[StrictInt] = None,
        correlation_id: Optional[StrictStr] = None,
        priority: Optional[StrictInt] = None,
        x_idempotency_key: Optional[StrictStr] = None,
        x_on_conflict: Optional[StrictStr] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> str:
        """Start a new workflow. Returns the ID of the workflow instance that can be later used for tracking


        :param name: (required)
        :type name: str
        :param request_body: (required)
        :type request_body: Dict[str, Any]
        :param version:
        :type version: int
        :param correlation_id:
        :type correlation_id: str
        :param priority:
        :type priority: int
        :param x_idempotency_key:
        :type x_idempotency_key: str
        :param x_on_conflict:
        :type x_on_conflict: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """

        _param = self._api._start_workflow1_serialize(
            name=name,
            request_body=request_body,
            version=version,
            correlation_id=correlation_id,
            priority=priority,
            x_idempotency_key=x_idempotency_key,
            x_on_conflict=x_on_conflict,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "str",
        }
        response_data = await self._api.api_client.call_api(
            *_param, _request_timeout=_request_timeout
        )
        await response_data.read()
        return self._api.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    async def terminate1(
        self,
        workflow_id: StrictStr,
        reason: Optional[StrictStr] = None,
        trigger_failure_workflow: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Terminate workflow execution"""
        await self._api.terminate1(
            workflow_id,
            reason,
            trigger_failure_workflow,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
