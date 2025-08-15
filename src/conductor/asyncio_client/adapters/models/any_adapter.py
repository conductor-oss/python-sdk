from __future__ import annotations

from typing import Any as AnyType
from typing import Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import Any


class AnyAdapter(Any):
    all_fields: Optional[Dict[str, AnyType]] = Field(default=None, alias="allFields")
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(
        default=None, alias="descriptorForType"
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(
        default=None, alias="unknownFields"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Any from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    Any.from_dict(obj["defaultInstanceForType"])
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
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "parserForType": obj.get("parserForType"),
                "serializedSize": obj.get("serializedSize"),
                "typeUrl": obj.get("typeUrl"),
                "typeUrlBytes": (
                    ByteStringAdapter.from_dict(obj["typeUrlBytes"])
                    if obj.get("typeUrlBytes") is not None
                    else None
                ),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
                "value": (
                    ByteStringAdapter.from_dict(obj["value"])
                    if obj.get("value") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.byte_string_adapter import (
    ByteStringAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)

AnyAdapter.model_rebuild(raise_errors=False)
