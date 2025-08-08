from __future__ import annotations

from typing import Optional
from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import DescriptorAdapter
from conductor.asyncio_client.adapters.models.field_options_adapter import FieldOptionsAdapter
from conductor.asyncio_client.adapters.models.field_descriptor_proto_adapter import FieldDescriptorProtoAdapter
from conductor.asyncio_client.http.models import FieldDescriptor
from conductor.asyncio_client.adapters.models.oneof_descriptor_adapter import OneofDescriptorAdapter
from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import EnumDescriptorAdapter
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import FileDescriptorAdapter


class FieldDescriptorAdapter(FieldDescriptor):
    containing_oneof: Optional[OneofDescriptorAdapter] = Field(default=None, alias="containingOneof")
    containing_type: Optional[DescriptorAdapter] = Field(default=None, alias="containingType")
    enum_type: Optional[EnumDescriptorAdapter] = Field(default=None, alias="enumType")
    extension_scope: Optional[DescriptorAdapter] = Field(default=None, alias="extensionScope")
    file: Optional[FileDescriptorAdapter] = None
    message_type: Optional[DescriptorAdapter] = Field(default=None, alias="messageType")
    options: Optional[FieldOptionsAdapter] = None
    proto: Optional[FieldDescriptorProtoAdapter] = None
    real_containing_oneof: Optional[OneofDescriptorAdapter] = Field(default=None, alias="realContainingOneof")
