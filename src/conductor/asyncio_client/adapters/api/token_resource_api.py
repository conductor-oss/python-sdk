from __future__ import annotations

from typing import Annotated, Any, Dict, Optional, Tuple, Union

from pydantic import Field, StrictBool, StrictFloat, StrictInt, StrictStr
from conductor.asyncio_client.adapters.models.generate_token_request_adapter import (
    GenerateTokenRequestAdapter,
)
from conductor.asyncio_client.http.api import TokenResourceApi
from conductor.asyncio_client.adapters import ApiClient


class TokenResourceApiAdapter:
    def __init__(self, api_client: ApiClient):
        self._api = TokenResourceApi(api_client)

    async def generate_token(
        self,
        generate_token_request: GenerateTokenRequestAdapter,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Generate JWT with the given access key"""
        return await self._api.generate_token(
            generate_token_request,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def get_user_info(
        self,
        claims: Optional[StrictBool] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Get the user info from the token"""
        return await self._api.get_user_info(
            claims,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
