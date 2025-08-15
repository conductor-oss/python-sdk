from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import OneofDescriptor


class OneofDescriptorAdapter(OneofDescriptor):
    containing_type: Optional["DescriptorAdapter"] = Field(
        default=None, alias="containingType"
    )
    file: Optional["FileDescriptorAdapter"] = None
    options: Optional["OneofOptionsAdapter"] = None
    proto: Optional["OneofDescriptorProtoAdapter"] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of OneofDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "containingType": (
                    DescriptorAdapter.from_dict(obj["containingType"])
                    if obj.get("containingType") is not None
                    else None
                ),
                "fieldCount": obj.get("fieldCount"),
                "file": (
                    FileDescriptorAdapter.from_dict(obj["file"])
                    if obj.get("file") is not None
                    else None
                ),
                "fullName": obj.get("fullName"),
                "index": obj.get("index"),
                "name": obj.get("name"),
                "options": (
                    OneofOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "proto": (
                    OneofDescriptorProtoAdapter.from_dict(obj["proto"])
                    if obj.get("proto") is not None
                    else None
                ),
                "synthetic": obj.get("synthetic"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (
    FileDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.oneof_descriptor_proto_adapter import (
    OneofDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.oneof_options_adapter import (
    OneofOptionsAdapter,
)

OneofDescriptorAdapter.model_rebuild(raise_errors=False)
