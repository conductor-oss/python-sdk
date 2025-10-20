from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import SourceCodeInfoOrBuilder


class SourceCodeInfoOrBuilderAdapter(SourceCodeInfoOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["MessageAdapter"] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(
        default=None, alias="descriptorForType"
    )
    location_list: Optional[List["LocationAdapter"]] = Field(default=None, alias="locationList")
    location_or_builder_list: Optional[List["LocationOrBuilderAdapter"]] = Field(
        default=None, alias="locationOrBuilderList"
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(default=None, alias="unknownFields")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of SourceCodeInfoOrBuilder from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    MessageAdapter.from_dict(obj["defaultInstanceForType"])
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
                "locationCount": obj.get("locationCount"),
                "locationList": (
                    [LocationAdapter.from_dict(_item) for _item in obj["locationList"]]
                    if obj.get("locationList") is not None
                    else None
                ),
                "locationOrBuilderList": (
                    [
                        LocationOrBuilderAdapter.from_dict(_item)
                        for _item in obj["locationOrBuilderList"]
                    ]
                    if obj.get("locationOrBuilderList") is not None
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


from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.location_adapter import (  # noqa: E402
    LocationAdapter,
)
from conductor.asyncio_client.adapters.models.location_or_builder_adapter import (  # noqa: E402
    LocationOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import (  # noqa: E402
    MessageAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

SourceCodeInfoOrBuilderAdapter.model_rebuild(raise_errors=False)
