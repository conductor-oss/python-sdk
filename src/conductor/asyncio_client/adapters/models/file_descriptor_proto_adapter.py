from __future__ import annotations

from typing import Dict, Any, Optional, List
from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import DescriptorAdapter
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_adapter import EnumDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_or_builder_adapter import EnumDescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.field_descriptor_proto_adapter import FieldDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.field_descriptor_proto_or_builder_adapter import FieldDescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.descriptor_proto_adapter import DescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.descriptor_proto_or_builder_adapter import DescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.file_options_adapter import FileOptionsAdapter
from conductor.asyncio_client.adapters.models.file_options_or_builder_adapter import FileOptionsOrBuilderAdapter
from conductor.asyncio_client.adapters.models.service_descriptor_proto_adapter import ServiceDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.service_descriptor_proto_or_builder_adapter import ServiceDescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.source_code_info_adapter import SourceCodeInfoAdapter
from conductor.asyncio_client.adapters.models.source_code_info_or_builder_adapter import SourceCodeInfoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import UnknownFieldSetAdapter
from conductor.asyncio_client.http.models import FileDescriptorProto

class FileDescriptorProtoAdapter(FileDescriptorProto):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[FileDescriptorProtoAdapter] = Field(default=None, alias="defaultInstanceForType")
    descriptor_for_type: Optional[DescriptorAdapter] = Field(default=None, alias="descriptorForType")
    enum_type_list: Optional[List[EnumDescriptorProtoAdapter]] = Field(default=None, alias="enumTypeList")
    enum_type_or_builder_list: Optional[List[EnumDescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="enumTypeOrBuilderList")
    extension_list: Optional[List[FieldDescriptorProtoAdapter]] = Field(default=None, alias="extensionList")
    extension_or_builder_list: Optional[List[FieldDescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="extensionOrBuilderList")
    message_type_list: Optional[List[DescriptorProtoAdapter]] = Field(default=None, alias="messageTypeList")
    message_type_or_builder_list: Optional[List[DescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="messageTypeOrBuilderList")
    options: Optional[FileOptionsAdapter] = None
    options_or_builder: Optional[FileOptionsOrBuilderAdapter] = Field(default=None, alias="optionsOrBuilder")
    service_list: Optional[List[ServiceDescriptorProtoAdapter]] = Field(default=None, alias="serviceList")
    service_or_builder_list: Optional[List[ServiceDescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="serviceOrBuilderList")
    source_code_info: Optional[SourceCodeInfoAdapter] = Field(default=None, alias="sourceCodeInfo")
    source_code_info_or_builder: Optional[SourceCodeInfoOrBuilderAdapter] = Field(default=None, alias="sourceCodeInfoOrBuilder")
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(default=None, alias="unknownFields")
