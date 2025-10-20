from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import FieldDescriptorProtoOrBuilder


class FieldDescriptorProtoOrBuilderAdapter(FieldDescriptorProtoOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["MessageAdapter"] = Field(default=None, alias="defaultInstanceForType")
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(default=None, alias="descriptorForType")
    options: Optional["FieldOptionsAdapter"] = None
    options_or_builder: Optional["FieldOptionsOrBuilderAdapter"] = Field(default=None, alias="optionsOrBuilder")
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(default=None, alias="unknownFields")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FieldDescriptorProtoOrBuilder from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    MessageAdapter.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "defaultValue": obj.get("defaultValue"),
                "defaultValueBytes": (
                    ByteStringAdapter.from_dict(obj["defaultValueBytes"])
                    if obj.get("defaultValueBytes") is not None
                    else None
                ),
                "descriptorForType": (
                    DescriptorAdapter.from_dict(obj["descriptorForType"])
                    if obj.get("descriptorForType") is not None
                    else None
                ),
                "extendee": obj.get("extendee"),
                "extendeeBytes": (
                    ByteStringAdapter.from_dict(obj["extendeeBytes"]) if obj.get("extendeeBytes") is not None else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "jsonName": obj.get("jsonName"),
                "jsonNameBytes": (
                    ByteStringAdapter.from_dict(obj["jsonNameBytes"]) if obj.get("jsonNameBytes") is not None else None
                ),
                "label": obj.get("label"),
                "name": obj.get("name"),
                "nameBytes": (
                    ByteStringAdapter.from_dict(obj["nameBytes"]) if obj.get("nameBytes") is not None else None
                ),
                "number": obj.get("number"),
                "oneofIndex": obj.get("oneofIndex"),
                "options": (FieldOptionsAdapter.from_dict(obj["options"]) if obj.get("options") is not None else None),
                "optionsOrBuilder": (
                    FieldOptionsOrBuilderAdapter.from_dict(obj["optionsOrBuilder"])
                    if obj.get("optionsOrBuilder") is not None
                    else None
                ),
                "proto3Optional": obj.get("proto3Optional"),
                "type": obj.get("type"),
                "typeName": obj.get("typeName"),
                "typeNameBytes": (
                    ByteStringAdapter.from_dict(obj["typeNameBytes"]) if obj.get("typeNameBytes") is not None else None
                ),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.byte_string_adapter import (  # noqa: E402
    ByteStringAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.field_options_adapter import (  # noqa: E402
    FieldOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.field_options_or_builder_adapter import (  # noqa: E402
    FieldOptionsOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import (  # noqa: E402
    MessageAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

FieldDescriptorProtoOrBuilderAdapter.model_rebuild(raise_errors=False)
