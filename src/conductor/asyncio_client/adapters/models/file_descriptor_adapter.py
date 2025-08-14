from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import FileDescriptor


class FileDescriptorAdapter(FileDescriptor):
    dependencies: Optional[List["FileDescriptorAdapter"]] = None
    enum_types: Optional[List["EnumDescriptorAdapter"]] = Field(
        default=None, alias="enumTypes"
    )
    extensions: Optional[List["FieldDescriptorAdapter"]] = None
    file: Optional["FileDescriptorAdapter"] = None
    message_types: Optional[List["DescriptorAdapter"]] = Field(
        default=None, alias="messageTypes"
    )
    options: Optional["FileOptionsAdapter"] = None
    proto: Optional["FileDescriptorProtoAdapter"] = None
    public_dependencies: Optional[List["FileDescriptorAdapter"]] = Field(
        default=None, alias="publicDependencies"
    )
    services: Optional[List["ServiceDescriptorAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FileDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.descriptor_adapter import \
            DescriptorAdapter
        from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import \
            EnumDescriptorAdapter
        from conductor.asyncio_client.adapters.models.field_descriptor_adapter import \
            FieldDescriptorAdapter
        from conductor.asyncio_client.adapters.models.file_descriptor_proto_adapter import \
            FileDescriptorProtoAdapter
        from conductor.asyncio_client.adapters.models.file_options_adapter import \
            FileOptionsAdapter
        from conductor.asyncio_client.adapters.models.service_descriptor_adapter import \
            ServiceDescriptorAdapter

        _obj = cls.model_validate(
            {
                "dependencies": (
                    [
                        FileDescriptorAdapter.from_dict(_item)
                        for _item in obj["dependencies"]
                    ]
                    if obj.get("dependencies") is not None
                    else None
                ),
                "edition": obj.get("edition"),
                "editionName": obj.get("editionName"),
                "enumTypes": (
                    [
                        EnumDescriptorAdapter.from_dict(_item)
                        for _item in obj["enumTypes"]
                    ]
                    if obj.get("enumTypes") is not None
                    else None
                ),
                "extensions": (
                    [
                        FieldDescriptorAdapter.from_dict(_item)
                        for _item in obj["extensions"]
                    ]
                    if obj.get("extensions") is not None
                    else None
                ),
                "file": (
                    FileDescriptorAdapter.from_dict(obj["file"])
                    if obj.get("file") is not None
                    else None
                ),
                "fullName": obj.get("fullName"),
                "messageTypes": (
                    [
                        DescriptorAdapter.from_dict(_item)
                        for _item in obj["messageTypes"]
                    ]
                    if obj.get("messageTypes") is not None
                    else None
                ),
                "name": obj.get("name"),
                "options": (
                    FileOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "package": obj.get("package"),
                "proto": (
                    FileDescriptorProtoAdapter.from_dict(obj["proto"])
                    if obj.get("proto") is not None
                    else None
                ),
                "publicDependencies": (
                    [
                        FileDescriptorAdapter.from_dict(_item)
                        for _item in obj["publicDependencies"]
                    ]
                    if obj.get("publicDependencies") is not None
                    else None
                ),
                "services": (
                    [
                        ServiceDescriptorAdapter.from_dict(_item)
                        for _item in obj["services"]
                    ]
                    if obj.get("services") is not None
                    else None
                ),
                "syntax": obj.get("syntax"),
            }
        )
        return _obj
