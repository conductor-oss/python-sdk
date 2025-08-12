from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class KafkaPublishInput(BaseModel):
    bootstrap_servers: Optional[str] = Field(None, alias="bootStrapServers")
    key: Optional[str] = Field(None, alias="key")
    key_serializer: Optional[str] = Field(None, alias="keySerializer")
    value: Optional[str] = Field(None, alias="value")
    request_timeout_ms: Optional[str] = Field(None, alias="requestTimeoutMs")
    max_block_ms: Optional[str] = Field(None, alias="maxBlockMs")
    headers: Optional[Dict[str, Any]] = Field(None, alias="headers")
    topic: Optional[str] = Field(None, alias="topic")

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
