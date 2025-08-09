from __future__ import annotations

from typing import Any as AnyType
from typing import Dict, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.unknown_field_set_adapter import (
    UnknownFieldSetAdapter,
)
from conductor.asyncio_client.http.models import Any


class AnyAdapter(Any):
    all_fields: Optional[Dict[str, AnyType]] = Field(default=None, alias="allFields")
    descriptor_for_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="descriptorForType"
    )
    unknown_fields: Optional[UnknownFieldSetAdapter] = Field(
        default=None, alias="unknownFields"
    )
