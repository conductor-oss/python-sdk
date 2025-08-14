from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import OneofDescriptorProto


class OneofDescriptorProtoAdapter(OneofDescriptorProto):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["OneofDescriptorProtoAdapter"] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(
        default=None, alias="descriptorForType"
    )
    options: Optional["OneofOptionsAdapter"] = None
    options_or_builder: Optional["OneofOptionsOrBuilderAdapter"] = Field(
        default=None, alias="optionsOrBuilder"
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(
        default=None, alias="unknownFields"
    )
    name_bytes: Optional["ByteStringAdapter"] = Field(default=None, alias="nameBytes")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of OneofDescriptorProto from a dict"""
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
        from conductor.asyncio_client.adapters.models.oneof_options_adapter import (
            OneofOptionsAdapter,
        )
        from conductor.asyncio_client.adapters.models.oneof_options_or_builder_adapter import (
            OneofOptionsOrBuilderAdapter,
        )
        from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
            UnknownFieldSetAdapter,
        )

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    OneofDescriptorProto.from_dict(obj["defaultInstanceForType"])
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
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "name": obj.get("name"),
                "nameBytes": (
                    ByteStringAdapter.from_dict(obj["nameBytes"])
                    if obj.get("nameBytes") is not None
                    else None
                ),
                "options": (
                    OneofOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "optionsOrBuilder": (
                    OneofOptionsOrBuilderAdapter.from_dict(obj["optionsOrBuilder"])
                    if obj.get("optionsOrBuilder") is not None
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
