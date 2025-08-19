from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import UninterpretedOption


class UninterpretedOptionAdapter(UninterpretedOption):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["UninterpretedOptionAdapter"] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(
        default=None, alias="descriptorForType"
    )
    name_list: Optional[List["NamePartAdapter"]] = Field(default=None, alias="nameList")
    name_or_builder_list: Optional[List["NamePartOrBuilderAdapter"]] = Field(
        default=None, alias="nameOrBuilderList"
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(
        default=None, alias="unknownFields"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of UninterpretedOption from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "aggregateValue": obj.get("aggregateValue"),
                "aggregateValueBytes": (
                    ByteStringAdapter.from_dict(obj["aggregateValueBytes"])
                    if obj.get("aggregateValueBytes") is not None
                    else None
                ),
                "allFields": obj.get("allFields"),
                "defaultInstanceForType": (
                    UninterpretedOption.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "descriptorForType": (
                    DescriptorAdapter.from_dict(obj["descriptorForType"])
                    if obj.get("descriptorForType") is not None
                    else None
                ),
                "doubleValue": obj.get("doubleValue"),
                "identifierValue": obj.get("identifierValue"),
                "identifierValueBytes": (
                    ByteStringAdapter.from_dict(obj["identifierValueBytes"])
                    if obj.get("identifierValueBytes") is not None
                    else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "memoizedSerializedSize": obj.get("memoizedSerializedSize"),
                "nameCount": obj.get("nameCount"),
                "nameList": (
                    [NamePartAdapter.from_dict(_item) for _item in obj["nameList"]]
                    if obj.get("nameList") is not None
                    else None
                ),
                "nameOrBuilderList": (
                    [
                        NamePartOrBuilderAdapter.from_dict(_item)
                        for _item in obj["nameOrBuilderList"]
                    ]
                    if obj.get("nameOrBuilderList") is not None
                    else None
                ),
                "negativeIntValue": obj.get("negativeIntValue"),
                "parserForType": obj.get("parserForType"),
                "positiveIntValue": obj.get("positiveIntValue"),
                "serializedSize": obj.get("serializedSize"),
                "stringValue": (
                    ByteStringAdapter.from_dict(obj["stringValue"])
                    if obj.get("stringValue") is not None
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
from conductor.asyncio_client.adapters.models.name_part_adapter import (  # noqa: E402
    NamePartAdapter,
)
from conductor.asyncio_client.adapters.models.name_part_or_builder_adapter import (  # noqa: E402
    NamePartOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

UninterpretedOptionAdapter.model_rebuild(raise_errors=False)
