from __future__ import annotations

from typing import Dict, Any, Optional
from pydantic import Field

from conductor.asyncio_client.adapters.models.event_handler_adapter import EventHandlerAdapter
from conductor.asyncio_client.http.models import ExtendedEventExecution


class ExtendedEventExecutionAdapter(ExtendedEventExecution):
    event_handler: Optional[EventHandlerAdapter] = Field(default=None, alias="eventHandler")
    full_message_payload: Optional[Dict[str, Any]] = Field(default=None, alias="fullMessagePayload")
    output: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
