from __future__ import annotations

from copy import deepcopy
from typing import Any, ClassVar, Dict, List, Optional, Type, Callable

from pydantic import BaseModel, Field

from conductor.shared.workflow.enums.http_method import HttpMethod


class HttpPollInput(BaseModel):
    uri: Optional[str] = Field(None, alias="uri")
    method: HttpMethod = Field(HttpMethod.GET, alias="method")
    accept: Optional[List[str]] = Field(None, alias="accept")
    headers: Optional[Dict[str, List[str]]] = Field(None, alias="headers")
    content_type: Optional[str] = Field(None, alias="contentType")
    connection_time_out: Optional[int] = Field(None, alias="connectionTimeOut")
    read_timeout: Optional[int] = Field(None, alias="readTimeOut")
    body: Optional[Any] = Field(None, alias="body")
    termination_condition: Optional[str] = Field(None, alias="terminationCondition")
    polling_interval: int = Field(100, alias="pollingInterval")
    max_poll_count: int = Field(100, alias="maxPollCount")
    polling_strategy: str = Field("FIXED", alias="pollingStrategy")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders: ClassVar[Dict[Type[Any], Callable[[Any], Any]]] = {HttpMethod: lambda v: v.value}

    def deep_copy(self) -> HttpPollInput:
        """Mimics deepcopy behavior in your original __init__."""
        return HttpPollInput(**deepcopy(self.model_dump(by_alias=True)))
