from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import IntegrationApi


class IntegrationApiAdapter(IntegrationApi):
    configuration: Optional[Dict[str, Any]] = None
    tags: Optional[List["TagAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IntegrationApi from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "api": obj.get("api"),
                "configuration": obj.get("configuration"),
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "description": obj.get("description"),
                "enabled": obj.get("enabled"),
                "integrationName": obj.get("integrationName"),
                "ownerApp": obj.get("ownerApp"),
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


from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

IntegrationApiAdapter.model_rebuild(raise_errors=False)
