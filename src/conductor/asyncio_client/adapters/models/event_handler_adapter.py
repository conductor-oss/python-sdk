from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.action_adapter import ActionAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import EventHandler


class EventHandlerAdapter(EventHandler):
    actions: Optional[List[ActionAdapter]] = None
    tags: Optional[List[TagAdapter]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of EventHandler from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "actions": [ActionAdapter.from_dict(_item) for _item in obj["actions"]] if obj.get("actions") is not None else None,
            "active": obj.get("active"),
            "condition": obj.get("condition"),
            "createdBy": obj.get("createdBy"),
            "description": obj.get("description"),
            "evaluatorType": obj.get("evaluatorType"),
            "event": obj.get("event"),
            "name": obj.get("name"),
            "orgId": obj.get("orgId"),
            "tags": [TagAdapter.from_dict(_item) for _item in obj["tags"]] if obj.get("tags") is not None else None
        })
        return _obj
