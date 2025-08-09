from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.descriptor_proto_adapter import (
    DescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import (
    EnumDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.field_descriptor_adapter import (
    FieldDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (
    FileDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.message_options_adapter import (
    MessageOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.oneof_descriptor_adapter import (
    OneofDescriptorAdapter,
)
from conductor.asyncio_client.http.models import Descriptor


class DescriptorAdapter(Descriptor):
    containing_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="containingType"
    )
    enum_types: Optional[List[EnumDescriptorAdapter]] = Field(
        default=None, alias="enumTypes"
    )
    extensions: Optional[List[FieldDescriptorAdapter]] = None
    fields: Optional[List[FieldDescriptorAdapter]] = None
    file: Optional[FileDescriptorAdapter] = None
    nested_types: Optional[List[DescriptorAdapter]] = Field(
        default=None, alias="nestedTypes"
    )
    oneofs: Optional[List[OneofDescriptorAdapter]] = None
    options: Optional[MessageOptionsAdapter] = None
    proto: Optional[DescriptorProtoAdapter] = None
    real_oneofs: Optional[List[OneofDescriptorAdapter]] = Field(
        default=None, alias="realOneofs"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Descriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "containingType": (
                    Descriptor.from_dict(obj["containingType"])
                    if obj.get("containingType") is not None
                    else None
                ),
                "enumTypes": (
                    [
                        EnumDescriptorAdapter.from_dict(_item)
                        for _item in obj["enumTypes"]
                    ]
                    if obj.get("enumTypes") is not None
                    else None
                ),
                "extendable": obj.get("extendable"),
                "extensions": (
                    [
                        FieldDescriptorAdapter.from_dict(_item)
                        for _item in obj["extensions"]
                    ]
                    if obj.get("extensions") is not None
                    else None
                ),
                "fields": (
                    [FieldDescriptorAdapter.from_dict(_item) for _item in obj["fields"]]
                    if obj.get("fields") is not None
                    else None
                ),
                "file": (
                    FileDescriptorAdapter.from_dict(obj["file"])
                    if obj.get("file") is not None
                    else None
                ),
                "fullName": obj.get("fullName"),
                "index": obj.get("index"),
                "name": obj.get("name"),
                "nestedTypes": (
                    [Descriptor.from_dict(_item) for _item in obj["nestedTypes"]]
                    if obj.get("nestedTypes") is not None
                    else None
                ),
                "oneofs": (
                    [OneofDescriptorAdapter.from_dict(_item) for _item in obj["oneofs"]]
                    if obj.get("oneofs") is not None
                    else None
                ),
                "options": (
                    MessageOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "proto": (
                    DescriptorProtoAdapter.from_dict(obj["proto"])
                    if obj.get("proto") is not None
                    else None
                ),
                "realOneofs": (
                    [
                        OneofDescriptorAdapter.from_dict(_item)
                        for _item in obj["realOneofs"]
                    ]
                    if obj.get("realOneofs") is not None
                    else None
                ),
            }
        )
        return _obj
