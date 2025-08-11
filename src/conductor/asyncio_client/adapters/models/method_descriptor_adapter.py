from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.descriptor_adapter import \
    DescriptorAdapter
from conductor.asyncio_client.adapters.models.file_descriptor_adapter import \
    FileDescriptorAdapter
from conductor.asyncio_client.adapters.models.method_descriptor_proto_adapter import \
    MethodDescriptorProtoAdapter
from conductor.asyncio_client.adapters.models.method_options_adapter import \
    MethodOptionsAdapter
from conductor.asyncio_client.adapters.models.service_descriptor_adapter import \
    ServiceDescriptorAdapter
from conductor.asyncio_client.http.models import MethodDescriptor


class MethodDescriptorAdapter(MethodDescriptor):
    file: Optional[FileDescriptorAdapter] = None
    input_type: Optional[DescriptorAdapter] = Field(default=None, alias="inputType")
    options: Optional[MethodOptionsAdapter] = None
    output_type: Optional[DescriptorAdapter] = Field(default=None, alias="outputType")
    proto: Optional[MethodDescriptorProtoAdapter] = None
    service: Optional[ServiceDescriptorAdapter] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of MethodDescriptor from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "clientStreaming": obj.get("clientStreaming"),
                "file": (
                    FileDescriptorAdapter.from_dict(obj["file"])
                    if obj.get("file") is not None
                    else None
                ),
                "fullName": obj.get("fullName"),
                "index": obj.get("index"),
                "inputType": (
                    DescriptorAdapter.from_dict(obj["inputType"])
                    if obj.get("inputType") is not None
                    else None
                ),
                "name": obj.get("name"),
                "options": (
                    MethodOptionsAdapter.from_dict(obj["options"])
                    if obj.get("options") is not None
                    else None
                ),
                "outputType": (
                    DescriptorAdapter.from_dict(obj["outputType"])
                    if obj.get("outputType") is not None
                    else None
                ),
                "proto": (
                    MethodDescriptorProtoAdapter.from_dict(obj["proto"])
                    if obj.get("proto") is not None
                    else None
                ),
                "serverStreaming": obj.get("serverStreaming"),
                "service": (
                    ServiceDescriptorAdapter.from_dict(obj["service"])
                    if obj.get("service") is not None
                    else None
                ),
            }
        )
        return _obj
