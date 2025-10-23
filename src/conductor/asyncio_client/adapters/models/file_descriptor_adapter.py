from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import FileDescriptor


class FileDescriptorAdapter(FileDescriptor):
    dependencies: Optional[List["FileDescriptorAdapter"]] = None  # type: ignore[assignment]
    enum_types: Optional[List["EnumDescriptorAdapter"]] = Field(default=None, alias="enumTypes")  # type: ignore[assignment]
    extensions: Optional[List["FieldDescriptorAdapter"]] = None  # type: ignore[assignment]
    file: Optional["FileDescriptorAdapter"] = None  # type: ignore[assignment]
    message_types: Optional[List["DescriptorAdapter"]] = Field(default=None, alias="messageTypes")  # type: ignore[assignment]
    options: Optional["FileOptionsAdapter"] = None  # type: ignore[assignment]
    proto: Optional["FileDescriptorProtoAdapter"] = None  # type: ignore[assignment]
    public_dependencies: Optional[List["FileDescriptorAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="publicDependencies"
    )
    services: Optional[List["ServiceDescriptorAdapter"]] = None  # type: ignore[assignment]

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FileDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "dependencies": (
                    [FileDescriptorAdapter.from_dict(_item) for _item in obj["dependencies"]]
                    if obj.get("dependencies") is not None
                    else None
                ),
                "edition": obj.get("edition"),
                "editionName": obj.get("editionName"),
                "enumTypes": (
                    [EnumDescriptorAdapter.from_dict(_item) for _item in obj["enumTypes"]]
                    if obj.get("enumTypes") is not None
                    else None
                ),
                "extensions": (
                    [FieldDescriptorAdapter.from_dict(_item) for _item in obj["extensions"]]
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
                    [DescriptorAdapter.from_dict(_item) for _item in obj["messageTypes"]]
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
                    [FileDescriptorAdapter.from_dict(_item) for _item in obj["publicDependencies"]]
                    if obj.get("publicDependencies") is not None
                    else None
                ),
                "services": (
                    [ServiceDescriptorAdapter.from_dict(_item) for _item in obj["services"]]
                    if obj.get("services") is not None
                    else None
                ),
                "syntax": obj.get("syntax"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import (  # noqa: E402
    EnumDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.field_descriptor_adapter import (  # noqa: E402
    FieldDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_proto_adapter import (  # noqa: E402
    FileDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.file_options_adapter import (  # noqa: E402
    FileOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.service_descriptor_adapter import (  # noqa: E402
    ServiceDescriptorAdapter,
)

FileDescriptorAdapter.model_rebuild(raise_errors=False)
