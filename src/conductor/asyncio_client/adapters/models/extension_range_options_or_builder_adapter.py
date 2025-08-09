from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.declaration_adapter import (
    DeclarationAdapter,
)
from conductor.asyncio_client.adapters.models.declaration_or_builder_adapter import (
    DeclarationOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.feature_set_adapter import (
    FeatureSetAdapter,
)
from conductor.asyncio_client.adapters.models.feature_set_or_builder_adapter import (
    FeatureSetOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.message_adapter import MessageAdapter
from conductor.asyncio_client.adapters.models.uninterpreted_option_adapter import (
    UninterpretedOptionAdapter,
)
from conductor.asyncio_client.adapters.models.uninterpreted_option_or_builder_adapter import (
    UninterpretedOptionOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
from conductor.asyncio_client.http.models import ExtensionRangeOptionsOrBuilder


class ExtensionRangeOptionsOrBuilderAdapter(ExtensionRangeOptionsOrBuilder):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    declaration_list: Optional[List[DeclarationAdapter]] = Field(
        default=None, alias="declarationList"
    )
    declaration_or_builder_list: Optional[List[DeclarationOrBuilderAdapter]] = Field(
        default=None, alias="declarationOrBuilderList"
    )
    default_instance_for_type: Optional[MessageAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    features: Optional[FeatureSetAdapter] = None
    features_or_builder: Optional[FeatureSetOrBuilderAdapter] = Field(
        default=None, alias="featuresOrBuilder"
    )
    uninterpreted_option_list: Optional[List[UninterpretedOptionAdapter]] = Field(
        default=None, alias="uninterpretedOptionList"
    )
    uninterpreted_option_or_builder_list: Optional[
        List[UninterpretedOptionOrBuilderAdapter]
    ] = Field(default=None, alias="uninterpretedOptionOrBuilderList")
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )
