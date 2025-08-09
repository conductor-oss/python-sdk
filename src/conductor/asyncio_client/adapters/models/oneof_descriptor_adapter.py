from __future__ import annotations

from typing import Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (
    FileDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.oneof_descriptor_proto_adapter import (
    OneofDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.oneof_options_adapter import (
    OneofOptionsAdapter,
)
from conductor.asyncio_client.http.models import OneofDescriptor


class OneofDescriptorAdapter(OneofDescriptor):
    containing_type: Optional[DescriptorAdapter] = Field(
        default=None, alias="containingType"
    )
    file: Optional[FileDescriptorAdapter] = None
    options: Optional[OneofOptionsAdapter] = None
    proto: Optional[OneofDescriptorProtoAdapter] = None
