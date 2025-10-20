from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import ServiceDescriptorProto


class ServiceDescriptorProtoAdapter(ServiceDescriptorProto):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["ServiceDescriptorProtoAdapter"] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(default=None, alias="descriptorForType")
    method_list: Optional[List["MethodDescriptorProtoAdapter"]] = Field(default=None, alias="methodList")
    method_or_builder_list: Optional[List["MethodDescriptorProtoOrBuilderAdapter"]] = Field(
        default=None, alias="methodOrBuilderList"
    )
    options: Optional["ServiceOptionsAdapter"] = None
    options_or_builder: Optional["ServiceOptionsOrBuilderAdapter"] = Field(default=None, alias="optionsOrBuilder")
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(default=None, alias="unknownFields")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ServiceDescriptorProto from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    ServiceDescriptorProto.from_dict(obj["defaultInstanceForType"])
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
                "methodCount": obj.get("methodCount"),
                "methodList": (
                    [MethodDescriptorProtoAdapter.from_dict(_item) for _item in obj["methodList"]]
                    if obj.get("methodList") is not None
                    else None
                ),
                "methodOrBuilderList": (
                    [MethodDescriptorProtoOrBuilderAdapter.from_dict(_item) for _item in obj["methodOrBuilderList"]]
                    if obj.get("methodOrBuilderList") is not None
                    else None
                ),
                "name": obj.get("name"),
                "nameBytes": (
                    ByteStringAdapter.from_dict(obj["nameBytes"]) if obj.get("nameBytes") is not None else None
                ),
                "options": (
                    ServiceOptionsAdapter.from_dict(obj["options"]) if obj.get("options") is not None else None
                ),
                "optionsOrBuilder": (
                    ServiceOptionsOrBuilderAdapter.from_dict(obj["optionsOrBuilder"])
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


from conductor.asyncio_client.adapters.models.byte_string_adapter import (  # noqa: E402
    ByteStringAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.method_descriptor_proto_adapter import (  # noqa: E402
    MethodDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.method_descriptor_proto_or_builder_adapter import (  # noqa: E402
    MethodDescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.service_options_adapter import (  # noqa: E402
    ServiceOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.service_options_or_builder_adapter import (  # noqa: E402
    ServiceOptionsOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

ServiceDescriptorProtoAdapter.model_rebuild(raise_errors=False)
