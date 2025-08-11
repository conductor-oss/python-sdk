from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import ExtendedConductorApplication


class ExtendedConductorApplicationAdapter(ExtendedConductorApplication):
    tags: Optional[List[TagAdapter]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ExtendedConductorApplication from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "id": obj.get("id"),
                "name": obj.get("name"),
                "tags": (
                    [TagAdapter.from_dict(_item) for _item in obj["tags"]]
                    if obj.get("tags") is not None
                    else None
                ),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
            }
        )
        return _obj
