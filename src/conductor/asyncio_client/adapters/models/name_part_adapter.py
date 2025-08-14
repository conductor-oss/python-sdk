from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import NamePart


class NamePartAdapter(NamePart):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["NamePartAdapter"] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(
        default=None, alias="descriptorForType"
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(
        default=None, alias="unknownFields"
    )
    name_part_bytes: Optional["ByteStringAdapter"] = Field(
        default=None, alias="namePartBytes"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of NamePart from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.byte_string_adapter import (
            ByteStringAdapter,
        )
        from conductor.asyncio_client.adapters.models.descriptor_adapter import (
            DescriptorAdapter,
        )
        from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
            UnknownFieldSetAdapter,
        )

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    NamePartAdapter.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "descriptorForType": (
                    DescriptorAdapter.from_dict(obj["descriptorForType"])
                    if obj.get("descriptorForType") is not None
                    else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "isExtension": obj.get("isExtension"),
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "namePart": obj.get("namePart"),
                "namePartBytes": (
                    ByteStringAdapter.from_dict(obj["namePartBytes"])
                    if obj.get("namePartBytes") is not None
                    else None
                ),
                "parserForType": obj.get("parserForType"),
                "serializedSize": obj.get("serializedSize"),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
            }
        )
        return _obj
