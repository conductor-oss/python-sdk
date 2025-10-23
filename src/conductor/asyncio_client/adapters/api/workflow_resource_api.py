from __future__ import annotations

from typing import Dict, Any, Union, Optional, Annotated, Tuple, List
from pydantic import validate_call, Field, StrictStr, StrictFloat, StrictInt, StrictBool
from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter
from conductor.asyncio_client.adapters.models.workflow_run_adapter import WorkflowRunAdapter
from conductor.asyncio_client.adapters.models.workflow_status_adapter import WorkflowStatusAdapter
from conductor.asyncio_client.adapters.models.scrollable_search_result_workflow_summary_adapter import (
    ScrollableSearchResultWorkflowSummaryAdapter,
)
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import (
    StartWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_test_request_adapter import (
    WorkflowTestRequestAdapter,
)
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import (
    RerunWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_state_update_adapter import (
    WorkflowStateUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.correlation_ids_search_request_adapter import (
    CorrelationIdsSearchRequestAdapter,
)
from conductor.asyncio_client.http.api import WorkflowResourceApi


class WorkflowResourceApiAdapter(WorkflowResourceApi):
    async def execute_workflow(  # type: ignore[override]
        self,
        name: StrictStr,
        version: StrictInt,
        request_id: StrictStr,
        start_workflow_request: StartWorkflowRequestAdapter,  # type: ignore[override]
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
        result = await super().execute_workflow(
            name,
            version,
            request_id,
            start_workflow_request,  # type: ignore[override]
            wait_until_task_ref,
            wait_for_seconds,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]

    async def get_execution_status(  # type: ignore[override]
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
        result = await super().get_execution_status(
            workflow_id,
            include_tasks,
            summarize,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]

    async def get_workflow_status_summary(  # type: ignore[override]
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
    ) -> WorkflowStatusAdapter:  # type: ignore[override]
        result = await super().get_workflow_status_summary(
            workflow_id,
            include_output,
            include_variables,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]

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
        return await super().get_running_workflow(
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

    async def get_workflows(  # type: ignore[override]
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
        result = await super().get_workflows(
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
        return result  # type: ignore[return-value]

    async def get_workflows1(  # type: ignore[override]
        self,
        correlation_ids_search_request: CorrelationIdsSearchRequestAdapter,  # type: ignore[override]
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
        result = await super().get_workflows1(
            correlation_ids_search_request,
            include_closed,
            include_tasks,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]

    async def search(  # type: ignore[override]
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
        result = await super().search(
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
        return result  # type: ignore[return-value]

    async def rerun(
        self,
        workflow_id: StrictStr,
        rerun_workflow_request: RerunWorkflowRequestAdapter,  # type: ignore[override]
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
        return await super().rerun(
            workflow_id,
            rerun_workflow_request,  # type: ignore[override]
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
        await super().restart(
            workflow_id,
            use_latest_definitions,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def update_workflow_and_task_state(  # type: ignore[override]
        self,
        workflow_id: StrictStr,
        request_id: StrictStr,
        workflow_state_update: WorkflowStateUpdateAdapter,  # type: ignore[override]
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
        result = await super().update_workflow_and_task_state(
            workflow_id,
            request_id,
            workflow_state_update,  # type: ignore[override]
            wait_until_task_ref,
            wait_for_seconds,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]

    async def test_workflow(  # type: ignore[override]
        self,
        workflow_test_request: WorkflowTestRequestAdapter,  # type: ignore[override]
        _request_timeout: Union[  # noqa: PT019
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,  # noqa: PT019
        _content_type: Optional[StrictStr] = None,  # noqa: PT019
        _headers: Optional[Dict[StrictStr, Any]] = None,  # noqa: PT019
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,  # noqa: PT019
    ) -> WorkflowAdapter:
        result = await super().test_workflow(
            workflow_test_request,  # type: ignore[override]
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]

    @validate_call
    async def update_workflow_state(
        self,
        workflow_id: StrictStr,
        request_body: Dict[str, Any],
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
        """Update workflow variables

        Updates the workflow variables and triggers evaluation.

        :param workflow_id: (required)
        :type workflow_id: str
        :param request_body: (required)
        :type request_body: Dict[str, object]
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

        _param = self._update_workflow_state_serialize(
            workflow_id=workflow_id,
            request_body=request_body,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "Workflow",
        }
        response_data = await self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        await response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

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
        :type request_body: Dict[str, object]
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

        _param = self._start_workflow1_serialize(
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
        response_data = await self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        await response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data
