from __future__ import annotations

from typing import Any, Dict, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import EnumValueDescriptor


class EnumValueDescriptorAdapter(EnumValueDescriptor):
    file: Optional["FileDescriptorAdapter"] = None
    options: Optional["EnumValueOptionsAdapter"] = None
    proto: Optional["EnumValueDescriptorProtoAdapter"] = None
    type: Optional["EnumDescriptorAdapter"] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of EnumValueDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "file": (
                    FileDescriptorAdapter.from_dict(obj["file"])
                    if obj.get("file") is not None
                    else None
                ),
                "fullName": obj.get("fullName"),
                "index": obj.get("index"),
                "name": obj.get("name"),
                "number": obj.get("number"),
                "options": (
                    EnumValueOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "proto": (
                    EnumValueDescriptorProtoAdapter.from_dict(obj["proto"])
                    if obj.get("proto") is not None
                    else None
                ),
                "type": (
                    EnumDescriptorAdapter.from_dict(obj["type"])
                    if obj.get("type") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import (
    EnumDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_descriptor_proto_adapter import (
    EnumValueDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_options_adapter import (
    EnumValueOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (
    FileDescriptorAdapter,
)

EnumValueDescriptorAdapter.model_rebuild(raise_errors=False)
