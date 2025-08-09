from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import MessageAdapter
from conductor.asyncio_client.adapters.models.method_descriptor_proto_adapter import (
    MethodDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.method_descriptor_proto_or_builder_adapter import (
    MethodDescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.service_options_adapter import (
    ServiceOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.service_options_or_builder_adapter import (
    ServiceOptionsOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
from conductor.asyncio_client.http.models import ServiceDescriptorProtoOrBuilder


class ServiceDescriptorProtoOrBuilderAdapter(ServiceDescriptorProtoOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[MessageAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    method_list: Optional[List[MethodDescriptorProtoAdapter]] = Field(
        default=None, alias="methodList"
    )
    method_or_builder_list: Optional[List[MethodDescriptorProtoOrBuilderAdapter]] = (
        Field(default=None, alias="methodOrBuilderList")
    )
    options: Optional[ServiceOptionsAdapter] = None
    options_or_builder: Optional[ServiceOptionsOrBuilderAdapter] = Field(
        default=None, alias="optionsOrBuilder"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )
