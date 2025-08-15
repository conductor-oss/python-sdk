from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import IntegrationDef


class IntegrationDefAdapter(IntegrationDef):
    configuration: Optional[List["IntegrationDefFormFieldAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IntegrationDef from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "category": obj.get("category"),
                "categoryLabel": obj.get("categoryLabel"),
                "configuration": (
                    [
                        IntegrationDefFormFieldAdapter.from_dict(_item)
                        for _item in obj["configuration"]
                    ]
                    if obj.get("configuration") is not None
                    else None
                ),
                "description": obj.get("description"),
                "enabled": obj.get("enabled"),
                "iconName": obj.get("iconName"),
                "name": obj.get("name"),
                "tags": obj.get("tags"),
                "type": obj.get("type"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.integration_def_form_field_adapter import (
    IntegrationDefFormFieldAdapter,
)

IntegrationDefAdapter.model_rebuild(raise_errors=False)
