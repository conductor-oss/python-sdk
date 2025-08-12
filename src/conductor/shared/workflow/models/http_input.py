from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from conductor.shared.workflow.enums.http_method import HttpMethod


class HttpInput(BaseModel):
    uri: Optional[str] = Field(None, alias="uri")
    method: HttpMethod = Field(HttpMethod.GET, alias="method")
    accept: Optional[List[str]] = Field(None, alias="accept")
    headers: Optional[Dict[str, List[str]]] = Field(None, alias="headers")
    content_type: Optional[str] = Field(None, alias="contentType")
    connection_time_out: Optional[int] = Field(None, alias="connectionTimeOut")
    read_timeout: Optional[int] = Field(None, alias="readTimeOut")
    body: Optional[Any] = Field(None, alias="body")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
        arbitrary_types_allowed = True
