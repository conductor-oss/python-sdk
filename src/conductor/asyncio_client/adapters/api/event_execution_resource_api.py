from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

from pydantic import Field, StrictFloat, StrictInt, StrictStr

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.extended_event_execution_adapter import (
    ExtendedEventExecutionAdapter,
)
from conductor.asyncio_client.adapters.models.search_result_handled_event_response_adapter import (
    SearchResultHandledEventResponseAdapter,
)
from conductor.asyncio_client.adapters.utils import convert_list_to_adapter, convert_to_adapter
from conductor.asyncio_client.http.api import EventExecutionResourceApi


class EventExecutionResourceApiAdapter:
    def __init__(self, api_client: ApiClient):
        self._api = EventExecutionResourceApi(api_client)

    async def get_event_handlers_for_event1(
        self,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> SearchResultHandledEventResponseAdapter:
        """Get All active Event Handlers for the last 24 hours"""
        result = await self.get_event_handlers_for_event1(
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        return convert_to_adapter(result, SearchResultHandledEventResponseAdapter)

    async def get_event_handlers_for_event2(
        self,
        event: StrictStr,
        var_from: StrictInt,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> List[ExtendedEventExecutionAdapter]:
        """Get event handlers for a given event"""
        result = await self.get_event_handlers_for_event2(
            event=event,
            var_from=var_from,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        return convert_list_to_adapter(result, ExtendedEventExecutionAdapter)
