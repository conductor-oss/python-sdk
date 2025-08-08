from __future__ import annotations

from typing import Dict, Any, Optional, List
from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import DescriptorAdapter
from conductor.asyncio_client.adapters.models.feature_set_adapter import FeatureSetAdapter
from conductor.asyncio_client.adapters.models.feature_set_or_builder_adapter import FeatureSetOrBuilderAdapter
from conductor.asyncio_client.adapters.models.uninterpreted_option_adapter import UninterpretedOptionAdapter
from conductor.asyncio_client.adapters.models.uninterpreted_option_or_builder_adapter import UninterpretedOptionOrBuilderAdapter
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import UnknownFieldSetAdapter
from conductor.asyncio_client.adapters.models.edition_default_adapter import EditionDefaultAdapter
from conductor.asyncio_client.adapters.models.edition_default_or_builder_adapter import EditionDefaultOrBuilderAdapter
from conductor.asyncio_client.http.models import FieldOptions


class FieldOptionsAdapter(FieldOptions):
    all_fields: Optional[Dict[str, Any]] = Field(default=None, alias="allFields")
    all_fields_raw: Optional[Dict[str, Any]] = Field(default=None, alias="allFieldsRaw")
    default_instance_for_type: Optional[FieldOptionsAdapter] = Field(default=None, alias="defaultInstanceForType")
    descriptor_for_type: Optional[DescriptorAdapter] = Field(default=None, alias="descriptorForType")
    edition_defaults_list: Optional[List[EditionDefaultAdapter]] = Field(default=None, alias="editionDefaultsList")
    edition_defaults_or_builder_list: Optional[List[EditionDefaultOrBuilderAdapter]] = Field(default=None, alias="editionDefaultsOrBuilderList")
    features: Optional[FeatureSetAdapter] = None
    features_or_builder: Optional[FeatureSetOrBuilderAdapter] = Field(default=None, alias="featuresOrBuilder")
    uninterpreted_option_list: Optional[List[UninterpretedOptionAdapter]] = Field(default=None, alias="uninterpretedOptionList")
    uninterpreted_option_or_builder_list: Optional[List[UninterpretedOptionOrBuilderAdapter]] = Field(default=None, alias="uninterpretedOptionOrBuilderList")
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(default=None, alias="unknownFields")
