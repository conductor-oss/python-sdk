from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

from pydantic import Field, StrictBool, StrictFloat, StrictInt, StrictStr

from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.asyncio_client.http.api import SchemaResourceApi


class SchemaResourceApiAdapter(SchemaResourceApi):
    async def save(
        self,
        schema_def: List[SchemaDefAdapter],  # type: ignore[override]
        new_version: Optional[StrictBool] = None,
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
        return await super().save(
            schema_def,  # type: ignore[arg-type]
            new_version,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

    async def get_schema_by_name_and_version(  # type: ignore[override]
        self,
        name: StrictStr,
        version: StrictInt,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> SchemaDefAdapter:
        result = await super().get_schema_by_name_and_version(
            name,
            version,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]

    async def get_all_schemas(  # type: ignore[override]
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
    ) -> List[SchemaDefAdapter]:
        result = await super().get_all_schemas(
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )
        return result  # type: ignore[return-value]
