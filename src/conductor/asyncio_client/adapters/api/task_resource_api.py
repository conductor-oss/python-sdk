from __future__ import annotations

from typing import Optional, Dict, Union, Annotated, Any, Tuple

from pydantic import validate_call, StrictStr, StrictFloat, Field, StrictInt

from conductor.asyncio_client.adapters.models.workflow_adapter import WorkflowAdapter
from conductor.asyncio_client.http.api import TaskResourceApi


class TaskResourceApiAdapter(TaskResourceApi):
    @validate_call
    async def update_task_sync(
            self,
            workflow_id: StrictStr,
            task_ref_name: StrictStr,
            status: StrictStr,
            request_body: Dict[str, Any],
            workerid: Optional[StrictStr] = None,
            _request_timeout: Union[
                None,
                Annotated[StrictFloat, Field(gt=0)],
                Tuple[
                    Annotated[StrictFloat, Field(gt=0)],
                    Annotated[StrictFloat, Field(gt=0)]
                ]
            ] = None,
            _request_auth: Optional[Dict[StrictStr, Any]] = None,
            _content_type: Optional[StrictStr] = None,
            _headers: Optional[Dict[StrictStr, Any]] = None,
            _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> WorkflowAdapter:
        """Update a task By Ref Name synchronously


        :param workflow_id: (required)
        :type workflow_id: str
        :param task_ref_name: (required)
        :type task_ref_name: str
        :param status: (required)
        :type status: str
        :param request_body: (required)
        :type request_body: Dict[str, object]
        :param workerid:
        :type workerid: str
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
        """  # noqa: E501

        _param = self._update_task_sync_serialize(
            workflow_id=workflow_id,
            task_ref_name=task_ref_name,
            status=status,
            request_body=request_body,
            workerid=workerid,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "Workflow",
        }
        response_data = await self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        await response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data
