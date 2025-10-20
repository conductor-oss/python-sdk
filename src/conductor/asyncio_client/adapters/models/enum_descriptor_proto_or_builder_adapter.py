from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import EnumDescriptorProtoOrBuilder


class EnumDescriptorProtoOrBuilderAdapter(EnumDescriptorProtoOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["MessageAdapter"] = Field(default=None, alias="defaultInstanceForType")
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(default=None, alias="descriptorForType")
    options: Optional["EnumOptionsAdapter"] = None
    options_or_builder: Optional["EnumOptionsOrBuilderAdapter"] = Field(default=None, alias="optionsOrBuilder")
    reserved_range_list: Optional[List["EnumReservedRangeAdapter"]] = Field(default=None, alias="reservedRangeList")
    reserved_range_or_builder_list: Optional[List["EnumReservedRangeOrBuilderAdapter"]] = Field(
        default=None, alias="reservedRangeOrBuilderList"
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(default=None, alias="unknownFields")
    value_list: Optional[List["EnumValueDescriptorProtoAdapter"]] = Field(default=None, alias="valueList")
    value_or_builder_list: Optional[List["EnumValueDescriptorProtoOrBuilderAdapter"]] = Field(
        default=None, alias="valueOrBuilderList"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of EnumDescriptorProtoOrBuilder from a dict"""
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
                "descriptorForType": (
                    DescriptorAdapter.from_dict(obj["descriptorForType"])
                    if obj.get("descriptorForType") is not None
                    else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "name": obj.get("name"),
                "nameBytes": (
                    ByteStringAdapter.from_dict(obj["nameBytes"]) if obj.get("nameBytes") is not None else None
                ),
                "options": (EnumOptionsAdapter.from_dict(obj["options"]) if obj.get("options") is not None else None),
                "optionsOrBuilder": (
                    EnumOptionsOrBuilderAdapter.from_dict(obj["optionsOrBuilder"])
                    if obj.get("optionsOrBuilder") is not None
                    else None
                ),
                "reservedNameCount": obj.get("reservedNameCount"),
                "reservedNameList": obj.get("reservedNameList"),
                "reservedRangeCount": obj.get("reservedRangeCount"),
                "reservedRangeList": (
                    [EnumReservedRangeAdapter.from_dict(_item) for _item in obj["reservedRangeList"]]
                    if obj.get("reservedRangeList") is not None
                    else None
                ),
                "reservedRangeOrBuilderList": (
                    [EnumReservedRangeOrBuilderAdapter.from_dict(_item) for _item in obj["reservedRangeOrBuilderList"]]
                    if obj.get("reservedRangeOrBuilderList") is not None
                    else None
                ),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
                "valueCount": obj.get("valueCount"),
                "valueList": (
                    [EnumValueDescriptorProtoAdapter.from_dict(_item) for _item in obj["valueList"]]
                    if obj.get("valueList") is not None
                    else None
                ),
                "valueOrBuilderList": (
                    [EnumValueDescriptorProtoOrBuilderAdapter.from_dict(_item) for _item in obj["valueOrBuilderList"]]
                    if obj.get("valueOrBuilderList") is not None
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
from conductor.asyncio_client.adapters.models.enum_options_adapter import (  # noqa: E402
    EnumOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.enum_options_or_builder_adapter import (  # noqa: E402
    EnumOptionsOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.enum_reserved_range_adapter import (  # noqa: E402
    EnumReservedRangeAdapter,
)
from conductor.asyncio_client.adapters.models.enum_reserved_range_or_builder_adapter import (  # noqa: E402
    EnumReservedRangeOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_descriptor_proto_adapter import (  # noqa: E402
    EnumValueDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_descriptor_proto_or_builder_adapter import (  # noqa: E402
    EnumValueDescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import (  # noqa: E402
    MessageAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

EnumDescriptorProtoOrBuilderAdapter.model_rebuild(raise_errors=False)
