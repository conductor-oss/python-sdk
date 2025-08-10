from __future__ import annotations

from typing import Any, Dict, Optional
from typing_extensions import Self

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import MessageAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
from conductor.asyncio_client.http.models import FeatureSetOrBuilder


class FeatureSetOrBuilderAdapter(FeatureSetOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[MessageAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FeatureSetOrBuilder from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "allFields": obj.get("allFields"),
            "defaultInstanceForType": MessageAdapter.from_dict(obj["defaultInstanceForType"]) if obj.get("defaultInstanceForType") is not None else None,
            "descriptorForType": DescriptorAdapter.from_dict(obj["descriptorForType"]) if obj.get("descriptorForType") is not None else None,
            "enumType": obj.get("enumType"),
            "fieldPresence": obj.get("fieldPresence"),
            "initializationErrorString": obj.get("initializationErrorString"),
            "initialized": obj.get("initialized"),
            "jsonFormat": obj.get("jsonFormat"),
            "messageEncoding": obj.get("messageEncoding"),
            "repeatedFieldEncoding": obj.get("repeatedFieldEncoding"),
            "unknownFields": UnknownFieldSetAdapter.from_dict(obj["unknownFields"]) if obj.get("unknownFields") is not None else None,
            "utf8Validation": obj.get("utf8Validation")
        })
        return _obj
