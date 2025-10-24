from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import FileDescriptorProto


class FileDescriptorProtoAdapter(FileDescriptorProto):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["FileDescriptorProtoAdapter"] = Field(  # type: ignore[assignment]
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(  # type: ignore[assignment]
        default=None, alias="descriptorForType"
    )
    enum_type_list: Optional[List["EnumDescriptorProtoAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="enumTypeList"
    )
    enum_type_or_builder_list: Optional[List["EnumDescriptorProtoOrBuilderAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="enumTypeOrBuilderList"
    )
    extension_list: Optional[List["FieldDescriptorProtoAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="extensionList"
    )
    extension_or_builder_list: Optional[List["FieldDescriptorProtoOrBuilderAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="extensionOrBuilderList"
    )
    message_type_list: Optional[List["DescriptorProtoAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="messageTypeList"
    )
    message_type_or_builder_list: Optional[List["DescriptorProtoOrBuilderAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="messageTypeOrBuilderList"
    )
    options: Optional["FileOptionsAdapter"] = None  # type: ignore[assignment]
    options_or_builder: Optional["FileOptionsOrBuilderAdapter"] = Field(  # type: ignore[assignment]
        default=None, alias="optionsOrBuilder"
    )
    service_list: Optional[List["ServiceDescriptorProtoAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="serviceList"
    )
    service_or_builder_list: Optional[List["ServiceDescriptorProtoOrBuilderAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="serviceOrBuilderList"
    )
    source_code_info: Optional["SourceCodeInfoAdapter"] = Field(  # type: ignore[assignment]
        default=None, alias="sourceCodeInfo"
    )
    source_code_info_or_builder: Optional["SourceCodeInfoOrBuilderAdapter"] = Field(  # type: ignore[assignment]
        default=None, alias="sourceCodeInfoOrBuilder"
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(default=None, alias="unknownFields")  # type: ignore[assignment]

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FileDescriptorProto from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    FileDescriptorProtoAdapter.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "dependencyCount": obj.get("dependencyCount"),
                "descriptorForType": (
                    DescriptorAdapter.from_dict(obj["descriptorForType"])
                    if obj.get("descriptorForType") is not None
                    else None
                ),
                "edition": obj.get("edition"),
                "enumTypeCount": obj.get("enumTypeCount"),
                "enumTypeList": (
                    [EnumDescriptorProtoAdapter.from_dict(_item) for _item in obj["enumTypeList"]]
                    if obj.get("enumTypeList") is not None
                    else None
                ),
                "enumTypeOrBuilderList": (
                    [
                        EnumDescriptorProtoOrBuilderAdapter.from_dict(_item)
                        for _item in obj["enumTypeOrBuilderList"]
                    ]
                    if obj.get("enumTypeOrBuilderList") is not None
                    else None
                ),
                "extensionCount": obj.get("extensionCount"),
                "extensionList": (
                    [FieldDescriptorProtoAdapter.from_dict(_item) for _item in obj["extensionList"]]
                    if obj.get("extensionList") is not None
                    else None
                ),
                "extensionOrBuilderList": (
                    [
                        FieldDescriptorProtoOrBuilderAdapter.from_dict(_item)
                        for _item in obj["extensionOrBuilderList"]
                    ]
                    if obj.get("extensionOrBuilderList") is not None
                    else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "messageTypeCount": obj.get("messageTypeCount"),
                "messageTypeList": (
                    [DescriptorProtoAdapter.from_dict(_item) for _item in obj["messageTypeList"]]
                    if obj.get("messageTypeList") is not None
                    else None
                ),
                "messageTypeOrBuilderList": (
                    [
                        DescriptorProtoOrBuilderAdapter.from_dict(_item)
                        for _item in obj["messageTypeOrBuilderList"]
                    ]
                    if obj.get("messageTypeOrBuilderList") is not None
                    else None
                ),
                "name": obj.get("name"),
                "nameBytes": (
                    ByteStringAdapter.from_dict(obj["nameBytes"])
                    if obj.get("nameBytes") is not None
                    else None
                ),
                "options": (
                    FileOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "optionsOrBuilder": (
                    FileOptionsOrBuilderAdapter.from_dict(obj["optionsOrBuilder"])
                    if obj.get("optionsOrBuilder") is not None
                    else None
                ),
                "package": obj.get("package"),
                "packageBytes": (
                    ByteStringAdapter.from_dict(obj["packageBytes"])
                    if obj.get("packageBytes") is not None
                    else None
                ),
                "parserForType": obj.get("parserForType"),
                "publicDependencyCount": obj.get("publicDependencyCount"),
                "publicDependencyList": obj.get("publicDependencyList"),
                "serializedSize": obj.get("serializedSize"),
                "serviceCount": obj.get("serviceCount"),
                "serviceList": (
                    [ServiceDescriptorProtoAdapter.from_dict(_item) for _item in obj["serviceList"]]
                    if obj.get("serviceList") is not None
                    else None
                ),
                "serviceOrBuilderList": (
                    [
                        ServiceDescriptorProtoOrBuilderAdapter.from_dict(_item)
                        for _item in obj["serviceOrBuilderList"]
                    ]
                    if obj.get("serviceOrBuilderList") is not None
                    else None
                ),
                "sourceCodeInfo": (
                    SourceCodeInfoAdapter.from_dict(obj["sourceCodeInfo"])
                    if obj.get("sourceCodeInfo") is not None
                    else None
                ),
                "sourceCodeInfoOrBuilder": (
                    SourceCodeInfoOrBuilderAdapter.from_dict(obj["sourceCodeInfoOrBuilder"])
                    if obj.get("sourceCodeInfoOrBuilder") is not None
                    else None
                ),
                "syntax": obj.get("syntax"),
                "syntaxBytes": (
                    ByteStringAdapter.from_dict(obj["syntaxBytes"])
                    if obj.get("syntaxBytes") is not None
                    else None
                ),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
                "weakDependencyCount": obj.get("weakDependencyCount"),
                "weakDependencyList": obj.get("weakDependencyList"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.byte_string_adapter import (  # noqa: E402
    ByteStringAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_proto_adapter import (  # noqa: E402
    DescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_proto_or_builder_adapter import (  # noqa: E402
    DescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_adapter import (  # noqa: E402
    EnumDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_or_builder_adapter import (  # noqa: E402
    EnumDescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.field_descriptor_proto_adapter import (  # noqa: E402
    FieldDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.field_descriptor_proto_or_builder_adapter import (  # noqa: E402
    FieldDescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.file_options_adapter import (  # noqa: E402
    FileOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.file_options_or_builder_adapter import (  # noqa: E402
    FileOptionsOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.service_descriptor_proto_adapter import (  # noqa: E402
    ServiceDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.service_descriptor_proto_or_builder_adapter import (  # noqa: E402
    ServiceDescriptorProtoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.source_code_info_adapter import (  # noqa: E402
    SourceCodeInfoAdapter,
)
from conductor.asyncio_client.adapters.models.source_code_info_or_builder_adapter import (  # noqa: E402
    SourceCodeInfoOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

FileDescriptorProtoAdapter.model_rebuild(raise_errors=False)
