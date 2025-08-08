from __future__ import annotations

from typing import Optional, List
from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import DescriptorAdapter
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import FileDescriptorAdapter
from conductor.asyncio_client.adapters.models.enum_options_adapter import EnumOptionsAdapter
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_adapter import EnumDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.enum_value_descriptor_adapter import EnumValueDescriptorAdapter
from conductor.asyncio_client.http.models import EnumDescriptor

class EnumDescriptorAdapter(EnumDescriptor):
    containing_type: Optional[DescriptorAdapter] = Field(default=None, alias="containingType")
    file: Optional[FileDescriptorAdapter] = None
    options: Optional[EnumOptionsAdapter] = None
    proto: Optional[EnumDescriptorProtoAdapter] = None
    values: Optional[List[EnumValueDescriptorAdapter]] = None
