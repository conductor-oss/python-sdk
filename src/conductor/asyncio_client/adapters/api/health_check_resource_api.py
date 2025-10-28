from __future__ import annotations

from typing import Annotated, Any, Dict, Optional, Tuple, Union

from pydantic import Field, StrictFloat, StrictInt, StrictStr
from conductor.asyncio_client.adapters import ApiClient

from conductor.asyncio_client.http.api import HealthCheckResourceApi


class HealthCheckResourceApiAdapter:
    def __init__(self, api_client: ApiClient):
        self._api = HealthCheckResourceApi(api_client)

    async def do_check(
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
    ) -> Dict[str, object]:
        """Check the health of the API"""
        return await self._api.do_check(
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
