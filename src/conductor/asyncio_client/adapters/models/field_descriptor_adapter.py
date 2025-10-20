from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import FieldDescriptor


class FieldDescriptorAdapter(FieldDescriptor):
    containing_oneof: Optional["OneofDescriptorAdapter"] = Field(default=None, alias="containingOneof")
    containing_type: Optional["DescriptorAdapter"] = Field(default=None, alias="containingType")
    enum_type: Optional["EnumDescriptorAdapter"] = Field(default=None, alias="enumType")
    extension_scope: Optional["DescriptorAdapter"] = Field(default=None, alias="extensionScope")
    file: Optional["FileDescriptorAdapter"] = None
    message_type: Optional["DescriptorAdapter"] = Field(default=None, alias="messageType")
    options: Optional["FieldOptionsAdapter"] = None
    proto: Optional["FieldDescriptorProtoAdapter"] = None
    real_containing_oneof: Optional["OneofDescriptorAdapter"] = Field(default=None, alias="realContainingOneof")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FieldDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "containingOneof": (
                    OneofDescriptorAdapter.from_dict(obj["containingOneof"])
                    if obj.get("containingOneof") is not None
                    else None
                ),
                "containingType": (
                    DescriptorAdapter.from_dict(obj["containingType"])
                    if obj.get("containingType") is not None
                    else None
                ),
                "defaultValue": obj.get("defaultValue"),
                "enumType": (
                    EnumDescriptorAdapter.from_dict(obj["enumType"]) if obj.get("enumType") is not None else None
                ),
                "extension": obj.get("extension"),
                "extensionScope": (
                    DescriptorAdapter.from_dict(obj["extensionScope"])
                    if obj.get("extensionScope") is not None
                    else None
                ),
                "file": (FileDescriptorAdapter.from_dict(obj["file"]) if obj.get("file") is not None else None),
                "fullName": obj.get("fullName"),
                "index": obj.get("index"),
                "javaType": obj.get("javaType"),
                "jsonName": obj.get("jsonName"),
                "liteJavaType": obj.get("liteJavaType"),
                "liteType": obj.get("liteType"),
                "mapField": obj.get("mapField"),
                "messageType": (
                    DescriptorAdapter.from_dict(obj["messageType"]) if obj.get("messageType") is not None else None
                ),
                "name": obj.get("name"),
                "number": obj.get("number"),
                "optional": obj.get("optional"),
                "options": (FieldOptionsAdapter.from_dict(obj["options"]) if obj.get("options") is not None else None),
                "packable": obj.get("packable"),
                "packed": obj.get("packed"),
                "proto": (
                    FieldDescriptorProtoAdapter.from_dict(obj["proto"]) if obj.get("proto") is not None else None
                ),
                "realContainingOneof": (
                    OneofDescriptorAdapter.from_dict(obj["realContainingOneof"])
                    if obj.get("realContainingOneof") is not None
                    else None
                ),
                "repeated": obj.get("repeated"),
                "required": obj.get("required"),
                "type": obj.get("type"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import (  # noqa: E402
    EnumDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.field_descriptor_proto_adapter import (  # noqa: E402
    FieldDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.field_options_adapter import (  # noqa: E402
    FieldOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (  # noqa: E402
    FileDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.oneof_descriptor_adapter import (  # noqa: E402
    OneofDescriptorAdapter,
)

FieldDescriptorAdapter.model_rebuild(raise_errors=False)
