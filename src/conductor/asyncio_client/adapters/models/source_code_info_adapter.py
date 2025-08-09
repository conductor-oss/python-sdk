from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.location_adapter import LocationAdapter
from conductor.asyncio_client.adapters.models.location_or_builder_adapter import (
    LocationOrBuilderAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
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
