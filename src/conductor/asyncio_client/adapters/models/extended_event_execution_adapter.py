from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import ExtendedEventExecution


class ExtendedEventExecutionAdapter(ExtendedEventExecution):
    event_handler: Optional["EventHandlerAdapter"] = Field(
        default=None, alias="eventHandler"
    )
    full_message_payload: Optional[Dict[str, Any]] = Field(
        default=None, alias="fullMessagePayload"
    )
    output: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ExtendedEventExecution from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "action": obj.get("action"),
                "created": obj.get("created"),
                "event": obj.get("event"),
                "eventHandler": (
                    EventHandlerAdapter.from_dict(obj["eventHandler"])
                    if obj.get("eventHandler") is not None
                    else None
                ),
                "fullMessagePayload": obj.get("fullMessagePayload"),
                "id": obj.get("id"),
                "messageId": obj.get("messageId"),
                "name": obj.get("name"),
                "orgId": obj.get("orgId"),
                "output": obj.get("output"),
                "payload": obj.get("payload"),
                "status": obj.get("status"),
                "statusDescription": obj.get("statusDescription"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.event_handler_adapter import (
    EventHandlerAdapter,
)

ExtendedEventExecutionAdapter.model_rebuild(raise_errors=False)
