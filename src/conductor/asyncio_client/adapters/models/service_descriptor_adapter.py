from __future__ import annotations

from typing import Any, Dict, List, Optional, Self

from conductor.asyncio_client.http.models import ServiceDescriptor


class ServiceDescriptorAdapter(ServiceDescriptor):
    file: Optional["FileDescriptorAdapter"] = None
    methods: Optional[List["MethodDescriptorAdapter"]] = None
    options: Optional["ServiceOptionsAdapter"] = None
    proto: Optional["ServiceDescriptorProtoAdapter"] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ServiceDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "file": (FileDescriptorAdapter.from_dict(obj["file"]) if obj.get("file") is not None else None),
                "fullName": obj.get("fullName"),
                "index": obj.get("index"),
                "methods": (
                    [MethodDescriptorAdapter.from_dict(_item) for _item in obj["methods"]]
                    if obj.get("methods") is not None
                    else None
                ),
                "name": obj.get("name"),
                "options": (
                    ServiceOptionsAdapter.from_dict(obj["options"]) if obj.get("options") is not None else None
                ),
                "proto": (
                    ServiceDescriptorProtoAdapter.from_dict(obj["proto"]) if obj.get("proto") is not None else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (  # noqa: E402
    FileDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.method_descriptor_adapter import (  # noqa: E402
    MethodDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.service_descriptor_proto_adapter import (  # noqa: E402
    ServiceDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.service_options_adapter import (  # noqa: E402
    ServiceOptionsAdapter,
)

ServiceDescriptorAdapter.model_rebuild(raise_errors=False)
