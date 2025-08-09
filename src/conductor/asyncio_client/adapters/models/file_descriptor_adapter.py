from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.descriptor_adapter import (
    DescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.enum_descriptor_adapter import (
    EnumDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.field_descriptor_adapter import (
    FieldDescriptorAdapter,
)
from conductor.asyncio_client.adapters.models.file_descriptor_proto_adapter import (
    FileDescriptorProtoAdapter,
)
from conductor.asyncio_client.adapters.models.file_options_adapter import (
    FileOptionsAdapter,
)
from conductor.asyncio_client.adapters.models.service_descriptor_adapter import (
    ServiceDescriptorAdapter,
)
from conductor.asyncio_client.http.models import FileDescriptor


class FileDescriptorAdapter(FileDescriptor):
    dependencies: Optional[List[FileDescriptorAdapter]] = None
    enum_types: Optional[List[EnumDescriptorAdapter]] = Field(
        default=None, alias="enumTypes"
    )
    extensions: Optional[List[FieldDescriptorAdapter]] = None
    file: Optional[FileDescriptorAdapter] = None
    message_types: Optional[List[DescriptorAdapter]] = Field(
        default=None, alias="messageTypes"
    )
    options: Optional[FileOptionsAdapter] = None
    proto: Optional[FileDescriptorProtoAdapter] = None
    public_dependencies: Optional[List[FileDescriptorAdapter]] = Field(
        default=None, alias="publicDependencies"
    )
    services: Optional[List[ServiceDescriptorAdapter]] = None
