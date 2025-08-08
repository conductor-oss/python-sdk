from __future__ import annotations

from typing import Dict, Any, Optional, List
from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import DescriptorAdapter
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_adapter import EnumDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_or_builder_adapter import EnumDescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.field_descriptor_proto_adapter import FieldDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.field_descriptor_proto_or_builder_adapter import FieldDescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.extension_range_adapter import ExtensionRangeAdapter
from conductor.asyncio_client.adapters.models.extension_range_or_builder_adapter import ExtensionRangeOrBuilderAdapter
from conductor.asyncio_client.adapters.models.oneof_descriptor_proto_adapter import OneofDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.oneof_descriptor_proto_or_builder_adapter import OneofDescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.adapters.models.reserved_range_adapter import ReservedRangeAdapter
from conductor.asyncio_client.adapters.models.reserved_range_or_builder_adapter import ReservedRangeOrBuilderAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import UnknownFieldSetAdapter
from conductor.asyncio_client.adapters.models.message_options_adapter import MessageOptionsAdapter
from conductor.asyncio_client.adapters.models.message_options_or_builder_adapter import MessageOptionsOrBuilderAdapter
from conductor.asyncio_client.adapters.models.descriptor_proto_or_builder_adapter import DescriptorProtoOrBuilderAdapter
from conductor.asyncio_client.http.models import DescriptorProto


class DescriptorProtoAdapter(DescriptorProto):
    all_fields: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[DescriptorProto] = Field(default=None, alias="defaultInstanceForType")
    descriptor_for_type: Optional[DescriptorAdapter] = Field(default=None, alias="descriptorForType")    
    enum_type_list: Optional[List[EnumDescriptorProtoAdapter]] = Field(default=None, alias="enumTypeList")
    enum_type_or_builder_list: Optional[List[EnumDescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="enumTypeOrBuilderList")
    extension_list: Optional[List[FieldDescriptorProtoAdapter]] = Field(default=None, alias="extensionList")
    extension_or_builder_list: Optional[List[FieldDescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="extensionOrBuilderList")
    extension_range_list: Optional[List[ExtensionRangeAdapter]] = Field(default=None, alias="extensionRangeList")
    extension_range_or_builder_list: Optional[List[ExtensionRangeOrBuilderAdapter]] = Field(default=None, alias="extensionRangeOrBuilderList")
    field_list: Optional[List[FieldDescriptorProtoAdapter]] = Field(default=None, alias="fieldList")
    field_or_builder_list: Optional[List[FieldDescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="fieldOrBuilderList")
    nested_type_list: Optional[List[DescriptorProtoAdapter]] = Field(default=None, alias="nestedTypeList")
    nested_type_or_builder_list: Optional[List[DescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="nestedTypeOrBuilderList")
    oneof_decl_list: Optional[List[OneofDescriptorProtoAdapter]] = Field(default=None, alias="oneofDeclList")
    oneof_decl_or_builder_list: Optional[List[OneofDescriptorProtoOrBuilderAdapter]] = Field(default=None, alias="oneofDeclOrBuilderList")
    options: Optional[MessageOptionsAdapter] = None
    options_or_builder: Optional[MessageOptionsOrBuilderAdapter] = Field(default=None, alias="optionsOrBuilder")
    reserved_range_list: Optional[List[ReservedRangeAdapter]] = Field(default=None, alias="reservedRangeList")
    reserved_range_or_builder_list: Optional[List[ReservedRangeOrBuilderAdapter]] = Field(default=None, alias="reservedRangeOrBuilderList")
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(default=None, alias="unknownFields")
