from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import MessageAdapter
from conductor.asyncio_client.adapters.models.name_part_adapter import NamePartAdapter
from conductor.asyncio_client.adapters.models.name_part_or_builder_adapter import (
    NamePartOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
from conductor.asyncio_client.http.models import UninterpretedOptionOrBuilder


class UninterpretedOptionOrBuilderAdapter(UninterpretedOptionOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[MessageAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    name_list: Optional[List[NamePartAdapter]] = Field(default=None, alias="nameList")
    name_or_builder_list: Optional[List[NamePartOrBuilderAdapter]] = Field(
        default=None, alias="nameOrBuilderList"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )
