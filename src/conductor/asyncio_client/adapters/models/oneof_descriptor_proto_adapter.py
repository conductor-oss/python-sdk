from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import \
    DescriptorAdapter
from conductor.asyncio_client.adapters.models.oneof_options_adapter import \
    OneofOptionsAdapter
from conductor.asyncio_client.adapters.models.oneof_options_or_builder_adapter import \
    OneofOptionsOrBuilderAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import \
    UnknownFieldSetAdapter
from conductor.asyncio_client.http.models import OneofDescriptorProto


class OneofDescriptorProtoAdapter(OneofDescriptorProto):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[OneofDescriptorProtoAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    options: Optional[OneofOptionsAdapter] = None
    options_or_builder: Optional[OneofOptionsOrBuilderAdapter] = Field(
        default=None, alias="optionsOrBuilder"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )
