from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import Location


class LocationAdapter(Location):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["LocationAdapter"] = Field(default=None, alias="defaultInstanceForType")
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(default=None, alias="descriptorForType")
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(default=None, alias="unknownFields")
    leading_comments_bytes: Optional["ByteStringAdapter"] = Field(default=None, alias="leadingCommentsBytes")
    trailing_comments_bytes: Optional["ByteStringAdapter"] = Field(default=None, alias="trailingCommentsBytes")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Location from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    LocationAdapter.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "descriptorForType": (
                    DescriptorAdapter.from_dict(obj["descriptorForType"])
                    if obj.get("descriptorForType") is not None
                    else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "leadingComments": obj.get("leadingComments"),
                "leadingCommentsBytes": (
                    ByteStringAdapter.from_dict(obj["leadingCommentsBytes"])
                    if obj.get("leadingCommentsBytes") is not None
                    else None
                ),
                "leadingDetachedCommentsCount": obj.get("leadingDetachedCommentsCount"),
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "parserForType": obj.get("parserForType"),
                "pathCount": obj.get("pathCount"),
                "pathList": obj.get("pathList"),
                "serializedSize": obj.get("serializedSize"),
                "spanCount": obj.get("spanCount"),
                "spanList": obj.get("spanList"),
                "trailingComments": obj.get("trailingComments"),
                "trailingCommentsBytes": (
                    ByteStringAdapter.from_dict(obj["trailingCommentsBytes"])
                    if obj.get("trailingCommentsBytes") is not None
                    else None
                ),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.byte_string_adapter import (  # noqa: E402
    ByteStringAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

LocationAdapter.model_rebuild(raise_errors=False)
