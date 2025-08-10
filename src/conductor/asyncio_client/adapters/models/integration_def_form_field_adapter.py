from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.option_adapter import \
    OptionAdapter
from conductor.asyncio_client.http.models import IntegrationDefFormField


class IntegrationDefFormFieldAdapter(IntegrationDefFormField):
    value_options: Optional[List[OptionAdapter]] = Field(
        default=None, alias="valueOptions"
    )
    depends_on: Optional[List[IntegrationDefFormFieldAdapter]] = Field(
        default=None, alias="dependsOn"
    )
    __properties: ClassVar[List[str]] = [
        "defaultValue",
        "description",
        "fieldName",
        "fieldType",
        "label",
        "optional",
        "value",
        "valueOptions",
        "dependsOn",
    ]

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IntegrationDefFormField from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "defaultValue": obj.get("defaultValue"),
                "description": obj.get("description"),
                "fieldName": obj.get("fieldName"),
                "fieldType": obj.get("fieldType"),
                "label": obj.get("label"),
                "optional": obj.get("optional"),
                "value": obj.get("value"),
                "valueOptions": (
                    [OptionAdapter.from_dict(_item) for _item in obj["valueOptions"]]
                    if obj.get("valueOptions") is not None
                    else None
                ),
                "dependsOn": (
                    [
                        IntegrationDefFormFieldAdapter.from_dict(_item)
                        for _item in obj["dependsOn"]
                    ]
                    if obj.get("dependsOn") is not None
                    else None
                ),
            }
        )
        return _obj
