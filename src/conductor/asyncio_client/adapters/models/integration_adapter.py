from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import Integration


class IntegrationAdapter(Integration):
    apis: Optional[List["IntegrationApiAdapter"]] = None
    configuration: Optional[Dict[str, Any]] = None
    tags: Optional[List["TagAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Integration from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.integration_api_adapter import (
            IntegrationApiAdapter,
        )
        from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

        _obj = cls.model_validate(
            {
                "apis": (
                    [IntegrationApiAdapter.from_dict(_item) for _item in obj["apis"]]
                    if obj.get("apis") is not None
                    else None
                ),
                "category": obj.get("category"),
                "configuration": obj.get("configuration"),
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "description": obj.get("description"),
                "enabled": obj.get("enabled"),
                "modelsCount": obj.get("modelsCount"),
                "name": obj.get("name"),
                "ownerApp": obj.get("ownerApp"),
                "tags": (
                    [TagAdapter.from_dict(_item) for _item in obj["tags"]]
                    if obj.get("tags") is not None
                    else None
                ),
                "type": obj.get("type"),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
            }
        )
        return _obj
