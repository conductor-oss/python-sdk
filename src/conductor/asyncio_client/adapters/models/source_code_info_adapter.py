from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.descriptor_adapter import \
    DescriptorAdapter
from conductor.asyncio_client.adapters.models.location_adapter import \
    LocationAdapter
from conductor.asyncio_client.adapters.models.location_or_builder_adapter import \
    LocationOrBuilderAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import \
    UnknownFieldSetAdapter
from conductor.asyncio_client.http.models import SourceCodeInfo


class SourceCodeInfoAdapter(SourceCodeInfo):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional[SourceCodeInfoAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    location_list: Optional[List[LocationAdapter]] = Field(
        default=None, alias="locationList"
    )
    location_or_builder_list: Optional[List[LocationOrBuilderAdapter]] = Field(
        default=None, alias="locationOrBuilderList"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of SourceCodeInfo from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    SourceCodeInfo.from_dict(obj["defaultInstanceForType"])
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
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "parserForType": obj.get("parserForType"),
                "serializedSize": obj.get("serializedSize"),
                "unknownFields": (
                    UnknownFieldSetAdapter.from_dict(obj["unknownFields"])
                    if obj.get("unknownFields") is not None
                    else None
                ),
            }
        )
        return _obj
