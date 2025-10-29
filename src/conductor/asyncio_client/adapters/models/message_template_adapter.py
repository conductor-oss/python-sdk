from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import MessageTemplate


class MessageTemplateAdapter(MessageTemplate):
    tags: Optional[List["TagAdapter"]] = None  # type: ignore[assignment]

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of MessageTemplate from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "description": obj.get("description"),
                "integrations": obj.get("integrations"),
                "name": obj.get("name"),
                "ownerApp": obj.get("ownerApp"),
                "tags": (
                    [TagAdapter.from_dict(_item) for _item in obj["tags"]]
                    if obj.get("tags") is not None
                    else None
                ),
                "template": obj.get("template"),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
                "variables": obj.get("variables"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter  # noqa: E402

MessageTemplateAdapter.model_rebuild(raise_errors=False)
