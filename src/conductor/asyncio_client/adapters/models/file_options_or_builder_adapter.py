from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import FileOptionsOrBuilder


class FileOptionsOrBuilderAdapter(FileOptionsOrBuilder):
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
    uninterpreted_option_or_builder_list: Optional[List["UninterpretedOptionOrBuilderAdapter"]] = (
        Field(default=None, alias="uninterpretedOptionOrBuilderList")
    )
    unknown_fields: Optional["UnknownFieldSetAdapter"] = Field(default=None, alias="unknownFields")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of FileOptionsOrBuilder from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "allFields": obj.get("allFields"),
                "ccEnableArenas": obj.get("ccEnableArenas"),
                "ccGenericServices": obj.get("ccGenericServices"),
                "csharpNamespace": obj.get("csharpNamespace"),
                "csharpNamespaceBytes": (
                    ByteStringAdapter.from_dict(obj["csharpNamespaceBytes"])
                    if obj.get("csharpNamespaceBytes") is not None
                    else None
                ),
                "defaultInstanceForType": (
                    MessageAdapter.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "deprecated": obj.get("deprecated"),
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
                "goPackage": obj.get("goPackage"),
                "goPackageBytes": (
                    ByteStringAdapter.from_dict(obj["goPackageBytes"])
                    if obj.get("goPackageBytes") is not None
                    else None
                ),
                "initializationErrorString": obj.get("initializationErrorString"),
                "initialized": obj.get("initialized"),
                "javaGenerateEqualsAndHash": obj.get("javaGenerateEqualsAndHash"),
                "javaGenericServices": obj.get("javaGenericServices"),
                "javaMultipleFiles": obj.get("javaMultipleFiles"),
                "javaOuterClassname": obj.get("javaOuterClassname"),
                "javaOuterClassnameBytes": (
                    ByteStringAdapter.from_dict(obj["javaOuterClassnameBytes"])
                    if obj.get("javaOuterClassnameBytes") is not None
                    else None
                ),
                "javaPackage": obj.get("javaPackage"),
                "javaPackageBytes": (
                    ByteStringAdapter.from_dict(obj["javaPackageBytes"])
                    if obj.get("javaPackageBytes") is not None
                    else None
                ),
                "javaStringCheckUtf8": obj.get("javaStringCheckUtf8"),
                "objcClassPrefix": obj.get("objcClassPrefix"),
                "objcClassPrefixBytes": (
                    ByteStringAdapter.from_dict(obj["objcClassPrefixBytes"])
                    if obj.get("objcClassPrefixBytes") is not None
                    else None
                ),
                "optimizeFor": obj.get("optimizeFor"),
                "phpClassPrefix": obj.get("phpClassPrefix"),
                "phpClassPrefixBytes": (
                    ByteStringAdapter.from_dict(obj["phpClassPrefixBytes"])
                    if obj.get("phpClassPrefixBytes") is not None
                    else None
                ),
                "phpGenericServices": obj.get("phpGenericServices"),
                "phpMetadataNamespace": obj.get("phpMetadataNamespace"),
                "phpMetadataNamespaceBytes": (
                    ByteStringAdapter.from_dict(obj["phpMetadataNamespaceBytes"])
                    if obj.get("phpMetadataNamespaceBytes") is not None
                    else None
                ),
                "phpNamespace": obj.get("phpNamespace"),
                "phpNamespaceBytes": (
                    ByteStringAdapter.from_dict(obj["phpNamespaceBytes"])
                    if obj.get("phpNamespaceBytes") is not None
                    else None
                ),
                "pyGenericServices": obj.get("pyGenericServices"),
                "rubyPackage": obj.get("rubyPackage"),
                "rubyPackageBytes": (
                    ByteStringAdapter.from_dict(obj["rubyPackageBytes"])
                    if obj.get("rubyPackageBytes") is not None
                    else None
                ),
                "swiftPrefix": obj.get("swiftPrefix"),
                "swiftPrefixBytes": (
                    ByteStringAdapter.from_dict(obj["swiftPrefixBytes"])
                    if obj.get("swiftPrefixBytes") is not None
                    else None
                ),
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


from conductor.asyncio_client.adapters.models.byte_string_adapter import (  # noqa: E402
    ByteStringAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_adapter import (  # noqa: E402
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.feature_set_adapter import (  # noqa: E402
    FeatureSetAdapter,
)
from conductor.asyncio_client.adapters.models.feature_set_or_builder_adapter import (  # noqa: E402
    FeatureSetOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import (  # noqa: E402
    MessageAdapter,
)
from conductor.asyncio_client.adapters.models.uninterpreted_option_adapter import (  # noqa: E402
    UninterpretedOptionAdapter,
)
from conductor.asyncio_client.adapters.models.uninterpreted_option_or_builder_adapter import (  # noqa: E402
    UninterpretedOptionOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (  # noqa: E402
    UnknownFieldSetAdapter,
)

FileOptionsOrBuilderAdapter.model_rebuild(raise_errors=False)
