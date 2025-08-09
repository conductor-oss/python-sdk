from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.field_options_adapter import (
    FieldOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.field_options_or_builder_adapter import (
    FieldOptionsOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import MessageAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
from conductor.asyncio_client.http.models import FieldDescriptorProtoOrBuilder


class FieldDescriptorProtoOrBuilderAdapter(FieldDescriptorProtoOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[MessageAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    options: Optional[FieldOptionsAdapter] = None
    options_or_builder: Optional[FieldOptionsOrBuilderAdapter] = Field(
        default=None, alias="optionsOrBuilder"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )
