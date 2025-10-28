from __future__ import annotations

from typing import Annotated, Any, Dict, Optional, Tuple, Union

from pydantic import Field, StrictFloat, StrictInt, StrictStr

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.http.api import IncomingWebhookResourceApi


class IncomingWebhookResourceApiAdapter:
    def __init__(self, api_client: ApiClient):
        self._api = IncomingWebhookResourceApi(api_client)

    async def handle_webhook(
        self,
        id: StrictStr,
        request_params: Dict[str, Dict[str, Any]],
        body: StrictStr,
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
        """Handle webhook"""
        return await self._api.handle_webhook(
            id,
            request_params,
            body,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def handle_webhook1(
        self,
        id: StrictStr,
        request_params: Dict[str, Dict[str, Any]],
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
        """Handle webhook"""
        return await self._api.handle_webhook1(
            id,
            request_params,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
