from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.byte_string_adapter import \
    ByteStringAdapter
from conductor.asyncio_client.adapters.models.descriptor_adapter import \
    DescriptorAdapter
from conductor.asyncio_client.adapters.models.method_options_adapter import \
    MethodOptionsAdapter
from conductor.asyncio_client.adapters.models.method_options_or_builder_adapter import \
    MethodOptionsOrBuilderAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import \
    UnknownFieldSetAdapter
from conductor.asyncio_client.http.models import MethodDescriptorProto


class MethodDescriptorProtoAdapter(MethodDescriptorProto):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[MethodDescriptorProtoAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    options: Optional[MethodOptionsAdapter] = None
    options_or_builder: Optional[MethodOptionsOrBuilderAdapter] = Field(
        default=None, alias="optionsOrBuilder"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of MethodDescriptorProto from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "clientStreaming": obj.get("clientStreaming"),
                "defaultInstanceForType": (
                    MethodDescriptorProto.from_dict(obj["defaultInstanceForType"])
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
                "inputType": obj.get("inputType"),
                "inputTypeBytes": (
                    ByteStringAdapter.from_dict(obj["inputTypeBytes"])
                    if obj.get("inputTypeBytes") is not None
                    else None
                ),
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "name": obj.get("name"),
                "nameBytes": (
                    ByteStringAdapter.from_dict(obj["nameBytes"])
                    if obj.get("nameBytes") is not None
                    else None
                ),
                "options": (
                    MethodOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "optionsOrBuilder": (
                    MethodOptionsOrBuilderAdapter.from_dict(obj["optionsOrBuilder"])
                    if obj.get("optionsOrBuilder") is not None
                    else None
                ),
                "outputType": obj.get("outputType"),
                "outputTypeBytes": (
                    ByteStringAdapter.from_dict(obj["outputTypeBytes"])
                    if obj.get("outputTypeBytes") is not None
                    else None
                ),
                "parserForType": obj.get("parserForType"),
                "serializedSize": obj.get("serializedSize"),
                "serverStreaming": obj.get("serverStreaming"),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
            }
        )
        return _obj
