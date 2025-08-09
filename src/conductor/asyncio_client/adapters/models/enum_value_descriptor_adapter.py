from __future__ import annotations

from typing import Optional

from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import (
    EnumDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_descriptor_proto_adapter import (
    EnumValueDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.enum_value_options_adapter import (
    EnumValueOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (
    FileDescriptorAdapter,
)
from conductor.asyncio_client.http.models import EnumValueDescriptor


class EnumValueDescriptorAdapter(EnumValueDescriptor):
    file: Optional[FileDescriptorAdapter] = None
    options: Optional[EnumValueOptionsAdapter] = None
    proto: Optional[EnumValueDescriptorProtoAdapter] = None
    type: Optional[EnumDescriptorAdapter] = None
