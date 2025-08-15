from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import TaskDef


class TaskDefAdapter(TaskDef):
    input_schema: Optional["SchemaDefAdapter"] = Field(
        default=None, alias="inputSchema"
    )
    input_template: Optional[Dict[str, Any]] = Field(
        default=None, alias="inputTemplate"
    )
    output_schema: Optional["SchemaDefAdapter"] = Field(
        default=None, alias="outputSchema"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of TaskDef from a dict"""
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
                "ownerApp": obj.get("ownerApp"),
                "ownerEmail": obj.get("ownerEmail"),
                "pollTimeoutSeconds": obj.get("pollTimeoutSeconds"),
                "rateLimitFrequencyInSeconds": obj.get("rateLimitFrequencyInSeconds"),
                "rateLimitPerFrequency": obj.get("rateLimitPerFrequency"),
                "responseTimeoutSeconds": obj.get("responseTimeoutSeconds"),
                "retryCount": obj.get("retryCount"),
                "retryDelaySeconds": obj.get("retryDelaySeconds"),
                "retryLogic": obj.get("retryLogic"),
                "timeoutPolicy": obj.get("timeoutPolicy"),
                "timeoutSeconds": obj.get("timeoutSeconds"),
                "totalTimeoutSeconds": obj.get("totalTimeoutSeconds"),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.schema_def_adapter import (
    SchemaDefAdapter,
)

TaskDefAdapter.model_rebuild(raise_errors=False)
