from __future__ import annotations

from typing import Optional, List
from pydantic import Field

from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import EnumDescriptorAdapter
from conductor.asyncio_client.adapters.models.field_descriptor_adapter import FieldDescriptorAdapter
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import FileDescriptorAdapter
from conductor.asyncio_client.adapters.models.oneof_descriptor_adapter import OneofDescriptorAdapter
from conductor.asyncio_client.adapters.models.message_options_adapter import MessageOptionsAdapter
from conductor.asyncio_client.adapters.models.descriptor_proto_adapter import DescriptorProtoAdapter
from conductor.asyncio_client.http.models import Descriptor


class DescriptorAdapter(Descriptor):
    containing_type: Optional[DescriptorAdapter] = Field(default=None, alias="containingType")
    enum_types: Optional[List[EnumDescriptorAdapter]] = Field(default=None, alias="enumTypes")
    extensions: Optional[List[FieldDescriptorAdapter]] = None
    fields: Optional[List[FieldDescriptorAdapter]] = None
    file: Optional[FileDescriptorAdapter] = None
    nested_types: Optional[List[DescriptorAdapter]] = Field(default=None, alias="nestedTypes")
    oneofs: Optional[List[OneofDescriptorAdapter]] = None
    options: Optional[MessageOptionsAdapter] = None
    proto: Optional[DescriptorProtoAdapter] = None
    real_oneofs: Optional[List[OneofDescriptorAdapter]] = Field(default=None, alias="realOneofs")
