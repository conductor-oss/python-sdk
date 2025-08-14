from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import EnumOptionsOrBuilder


class EnumOptionsOrBuilderAdapter(EnumOptionsOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    default_instance_for_type: Optional["MessageAdapter"] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional["DescriptorAdapter"] = Field(
        default=None, alias="descriptorForType"
    )
    features: Optional["FeatureSetAdapter"] = None
    features_or_builder: Optional["FeatureSetOrBuilderAdapter"] = Field(
        default=None, alias="featuresOrBuilder"
    )
    uninterpreted_option_list: Optional[List["UninterpretedOptionAdapter"]] = Field(
        default=None, alias="uninterpretedOptionList"
    )
    uninterpreted_option_or_builder_list: Optional[
        List["UninterpretedOptionOrBuilderAdapter"]
    ] = Field(default=None, alias="uninterpretedOptionOrBuilderList")
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(
        default=None, alias="unknownFields"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of EnumOptionsOrBuilder from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.descriptor_adapter import (
            DescriptorAdapter,
        )
        from conductor.asyncio_client.adapters.models.feature_set_adapter import (
            FeatureSetAdapter,
        )
        from conductor.asyncio_client.adapters.models.feature_set_or_builder_adapter import (
            FeatureSetOrBuilderAdapter,
        )
        from conductor.asyncio_client.adapters.models.message_adapter import (
            MessageAdapter,
        )
        from conductor.asyncio_client.adapters.models.uninterpreted_option_adapter import (
            UninterpretedOptionAdapter,
        )
        from conductor.asyncio_client.adapters.models.uninterpreted_option_or_builder_adapter import (
            UninterpretedOptionOrBuilderAdapter,
        )
        from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
            UnknownFieldSetAdapter,
        )

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "allowAlias": obj.get("allowAlias"),
                "defaultInstanceForType": (
                    MessageAdapter.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "deprecated": obj.get("deprecated"),
                "deprecatedLegacyJsonFieldConflicts": obj.get(
                    "deprecatedLegacyJsonFieldConflicts"
                ),
                "descriptorForType": (
                    DescriptorAdapter.from_dict(obj["descriptorForType"])
                    if obj.get("descriptorForType") is not None
                    else None
                ),
                "features": (
                    FeatureSetAdapter.from_dict(obj["features"])
                    if obj.get("features") is not None
                    else None
                ),
                "featuresOrBuilder": (
                    FeatureSetOrBuilderAdapter.from_dict(obj["featuresOrBuilder"])
                    if obj.get("featuresOrBuilder") is not None
                    else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "uninterpretedOptionCount": obj.get("uninterpretedOptionCount"),
                "uninterpretedOptionList": (
                    [
                        UninterpretedOptionAdapter.from_dict(_item)
                        for _item in obj["uninterpretedOptionList"]
                    ]
                    if obj.get("uninterpretedOptionList") is not None
                    else None
                ),
                "uninterpretedOptionOrBuilderList": (
                    [
                        UninterpretedOptionOrBuilderAdapter.from_dict(_item)
                        for _item in obj["uninterpretedOptionOrBuilderList"]
                    ]
                    if obj.get("uninterpretedOptionOrBuilderList") is not None
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
