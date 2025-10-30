from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import field_validator
from typing_extensions import Self

from conductor.asyncio_client.http.models import Integration


class IntegrationAdapter(Integration):
    apis: Optional[List["IntegrationApiAdapter"]] = None
    configuration: Optional[Dict[str, Any]] = None
    tags: Optional[List["TagAdapter"]] = None

    @field_validator("category")
    def category_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in {
            "API",
            "AI_MODEL",
            "VECTOR_DB",
            "RELATIONAL_DB",
            "MESSAGE_BROKER",
            "GIT",
            "EMAIL",
            "MCP",
            "CLOUD",
        }:
            raise ValueError(
                "must be one of enum values ('API', 'AI_MODEL', 'VECTOR_DB', 'RELATIONAL_DB', 'MESSAGE_BROKER', 'GIT', 'EMAIL', 'MCP', 'CLOUD')"
            )
        return value

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Integration from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

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


from conductor.asyncio_client.adapters.models.integration_api_adapter import (  # noqa: E402
    IntegrationApiAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import (  # noqa: E402
    TagAdapter,
)

IntegrationAdapter.model_rebuild(raise_errors=False)
