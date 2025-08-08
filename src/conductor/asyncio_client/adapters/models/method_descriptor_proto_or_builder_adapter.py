from __future__ import annotations

from typing import Dict, Any, Optional
from pydantic import Field

from conductor.asyncio_client.http.models import MethodDescriptorProtoOrBuilder
from conductor.asyncio_client.adapters.models.message_adapter import MessageAdapter
from conductor.asyncio_client.adapters.models.descriptor_adapter import DescriptorAdapter
from conductor.asyncio_client.adapters.models.method_options_adapter import MethodOptionsAdapter
from conductor.asyncio_client.adapters.models.method_options_or_builder_adapter import MethodOptionsOrBuilderAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import UnknownFieldSetAdapter


class MethodDescriptorProtoOrBuilderAdapter(MethodDescriptorProtoOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[MessageAdapter] = Field(default=None, alias="defaultInstanceForType")
    descriptor_for_type: Optional[DescriptorAdapter] = Field(default=None, alias="descriptorForType")
    options: Optional[MethodOptionsAdapter] = None
    options_or_builder: Optional[MethodOptionsOrBuilderAdapter] = Field(default=None, alias="optionsOrBuilder")
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(default=None, alias="unknownFields")
