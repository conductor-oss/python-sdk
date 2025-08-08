from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.http.models import ServiceDescriptor
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import FileDescriptorAdapter
from conductor.asyncio_client.adapters.models.method_descriptor_adapter import MethodDescriptorAdapter
from conductor.asyncio_client.adapters.models.service_options_adapter import ServiceOptionsAdapter
from conductor.asyncio_client.adapters.models.service_descriptor_proto_adapter import ServiceDescriptorProtoAdapter

class ServiceDescriptorAdapter(ServiceDescriptor):
    file: Optional[FileDescriptorAdapter] = None
    methods: Optional[List[MethodDescriptorAdapter]] = None
    options: Optional[ServiceOptionsAdapter] = None
    proto: Optional[ServiceDescriptorProtoAdapter] = None
