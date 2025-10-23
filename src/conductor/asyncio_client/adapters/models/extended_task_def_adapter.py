from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import ExtendedTaskDef


class ExtendedTaskDefAdapter(ExtendedTaskDef):
    input_schema: Optional["SchemaDefAdapter"] = Field(default=None, alias="inputSchema")  # type: ignore[assignment]
    input_template: Optional[Dict[str, Any]] = Field(default=None, alias="inputTemplate")
    output_schema: Optional["SchemaDefAdapter"] = Field(default=None, alias="outputSchema")  # type: ignore[assignment]
    tags: Optional[List["TagAdapter"]] = None  # type: ignore[assignment]
    timeout_seconds: Optional[int] = Field(alias="timeoutSeconds", default=None)  # type: ignore[assignment]
    total_timeout_seconds: Optional[int] = Field(alias="totalTimeoutSeconds", default=None)  # type: ignore[assignment]

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ExtendedTaskDef from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "backoffScaleFactor": obj.get("backoffScaleFactor"),
                "baseType": obj.get("baseType"),
                "concurrentExecLimit": obj.get("concurrentExecLimit"),
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "description": obj.get("description"),
                "enforceSchema": obj.get("enforceSchema"),
                "executionNameSpace": obj.get("executionNameSpace"),
                "inputKeys": obj.get("inputKeys"),
                "inputSchema": (
                    SchemaDefAdapter.from_dict(obj["inputSchema"])
                    if obj.get("inputSchema") is not None
                    else None
                ),
                "inputTemplate": obj.get("inputTemplate"),
                "isolationGroupId": obj.get("isolationGroupId"),
                "name": obj.get("name"),
                "outputKeys": obj.get("outputKeys"),
                "outputSchema": (
                    SchemaDefAdapter.from_dict(obj["outputSchema"])
                    if obj.get("outputSchema") is not None
                    else None
                ),
                "overwriteTags": obj.get("overwriteTags"),
                "ownerApp": obj.get("ownerApp"),
                "ownerEmail": obj.get("ownerEmail"),
                "pollTimeoutSeconds": obj.get("pollTimeoutSeconds"),
                "rateLimitFrequencyInSeconds": obj.get("rateLimitFrequencyInSeconds"),
                "rateLimitPerFrequency": obj.get("rateLimitPerFrequency"),
                "responseTimeoutSeconds": obj.get("responseTimeoutSeconds"),
                "retryCount": obj.get("retryCount"),
                "retryDelaySeconds": obj.get("retryDelaySeconds"),
                "retryLogic": obj.get("retryLogic"),
                "tags": (
                    [TagAdapter.from_dict(_item) for _item in obj["tags"]]
                    if obj.get("tags") is not None
                    else None
                ),
                "timeoutPolicy": obj.get("timeoutPolicy"),
                "timeoutSeconds": obj.get("timeoutSeconds"),
                "totalTimeoutSeconds": obj.get("totalTimeoutSeconds"),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.schema_def_adapter import (  # noqa: E402
    SchemaDefAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter  # noqa: E402

ExtendedTaskDefAdapter.model_rebuild(raise_errors=False)
