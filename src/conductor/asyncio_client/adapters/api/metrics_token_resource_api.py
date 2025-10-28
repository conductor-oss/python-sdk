from __future__ import annotations

from typing import Annotated, Any, Dict, Optional, Tuple, Union

from pydantic import Field, StrictFloat, StrictInt, StrictStr

from conductor.asyncio_client.http.api import MetricsTokenResourceApi
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.metrics_token_adapter import MetricsTokenAdapter
from conductor.asyncio_client.adapters.utils import convert_to_adapter


class MetricsTokenResourceApiAdapter:
    def __init__(self, api_client: ApiClient):
        self._api = MetricsTokenResourceApi(api_client)

    async def token(
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
    ) -> MetricsTokenAdapter:
        """Get metrics token"""
        result = await self._api.token(
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return convert_to_adapter(result, MetricsTokenAdapter)
