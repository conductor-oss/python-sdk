from __future__ import annotations

from typing import Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import (
    FileDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.method_descriptor_proto_adapter import (
    MethodDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.method_options_adapter import (
    MethodOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.service_descriptor_adapter import (
    ServiceDescriptorAdapter,
)
from conductor.asyncio_client.http.models import MethodDescriptor


class MethodDescriptorAdapter(MethodDescriptor):
    file: Optional[FileDescriptorAdapter] = None
    input_type: Optional[DescriptorAdapter] = Field(default=None, alias="inputType")
    options: Optional[MethodOptionsAdapter] = None
    output_type: Optional[DescriptorAdapter] = Field(default=None, alias="outputType")
    proto: Optional[MethodDescriptorProtoAdapter] = None
    service: Optional[ServiceDescriptorAdapter] = None
