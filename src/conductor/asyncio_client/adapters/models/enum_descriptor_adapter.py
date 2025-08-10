from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.enum_descriptor_proto_adapter import (
    EnumDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.enum_options_adapter import (
    EnumOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_descriptor_adapter import (
    EnumValueDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (
    FileDescriptorAdapter,
)
from conductor.asyncio_client.http.models import EnumDescriptor


class EnumDescriptorAdapter(EnumDescriptor):
    containing_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="containingType"
    )
    file: Optional[FileDescriptorAdapter] = None
    options: Optional[EnumOptionsAdapter] = None
    proto: Optional[EnumDescriptorProtoAdapter] = None
    values: Optional[List[EnumValueDescriptorAdapter]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of EnumDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "closed": obj.get("closed"),
            "containingType": DescriptorAdapter.from_dict(obj["containingType"]) if obj.get("containingType") is not None else None,
            "file": FileDescriptorAdapter.from_dict(obj["file"]) if obj.get("file") is not None else None,
            "fullName": obj.get("fullName"),
            "index": obj.get("index"),
            "name": obj.get("name"),
            "options": EnumOptionsAdapter.from_dict(obj["options"]) if obj.get("options") is not None else None,
            "proto": EnumDescriptorProtoAdapter.from_dict(obj["proto"]) if obj.get("proto") is not None else None,
            "values": [EnumValueDescriptorAdapter.from_dict(_item) for _item in obj["values"]] if obj.get("values") is not None else None
        })
        return _obj
