from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.enum_options_adapter import (
    EnumOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.enum_options_or_builder_adapter import (
    EnumOptionsOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.enum_reserved_range_adapter import (
    EnumReservedRangeAdapter,
)
from conductor.asyncio_client.adapters.models.enum_reserved_range_or_builder_adapter import (
    EnumReservedRangeOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_descriptor_proto_adapter import (
    EnumValueDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_descriptor_proto_or_builder_adapter import (
    EnumValueDescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
from conductor.asyncio_client.http.models import EnumDescriptorProto


class EnumDescriptorProtoAdapter(EnumDescriptorProto):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[EnumDescriptorProtoAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    options: Optional[EnumOptionsAdapter] = None
    options_or_builder: Optional[EnumOptionsOrBuilderAdapter] = Field(
        default=None, alias="optionsOrBuilder"
    )
    reserved_range_list: Optional[List[EnumReservedRangeAdapter]] = Field(
        default=None, alias="reservedRangeList"
    )
    reserved_range_or_builder_list: Optional[
        List[EnumReservedRangeOrBuilderAdapter]
    ] = Field(default=None, alias="reservedRangeOrBuilderList")
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )
    value_list: Optional[List[EnumValueDescriptorProtoAdapter]] = Field(
        default=None, alias="valueList"
    )
    value_or_builder_list: Optional[List[EnumValueDescriptorProtoOrBuilderAdapter]] = (
        Field(default=None, alias="valueOrBuilderList")
    )
