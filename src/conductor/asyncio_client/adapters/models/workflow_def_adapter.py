from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.rate_limit_config_adapter import (
    RateLimitConfigAdapter,
)
from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.asyncio_client.adapters.models.workflow_task_adapter import (
    WorkflowTaskAdapter,
)
from conductor.asyncio_client.http.models import WorkflowDef


class WorkflowDefAdapter(WorkflowDef):
    input_template: Optional[Dict[str, Any]] = Field(
        default=None, alias="inputTemplate"
    )
    output_parameters: Optional[Dict[str, Any]] = Field(
        default=None, alias="outputParameters"
    )
    variables: Optional[Dict[str, Any]] = None
    tasks: List[WorkflowTaskAdapter]
    schema_version: Optional[int] = Field(default=None, alias="schemaVersion")
    output_schema: Optional[SchemaDefAdapter] = Field(
        default=None, alias="outputSchema"
    )
    input_schema: Optional[SchemaDefAdapter] = Field(default=None, alias="inputSchema")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkflowDef from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "description": obj.get("description"),
                "enforceSchema": obj.get("enforceSchema"),
                "failureWorkflow": obj.get("failureWorkflow"),
                "inputParameters": obj.get("inputParameters"),
                "inputSchema": (
                    SchemaDefAdapter.from_dict(obj["inputSchema"])
                    if obj.get("inputSchema") is not None
                    else None
                ),
                "inputTemplate": obj.get("inputTemplate"),
                "name": obj.get("name"),
                "outputParameters": obj.get("outputParameters"),
                "outputSchema": (
                    SchemaDefAdapter.from_dict(obj["outputSchema"])
                    if obj.get("outputSchema") is not None
                    else None
                ),
                "ownerApp": obj.get("ownerApp"),
                "ownerEmail": obj.get("ownerEmail"),
                "rateLimitConfig": (
                    RateLimitConfigAdapter.from_dict(obj["rateLimitConfig"])
                    if obj.get("rateLimitConfig") is not None
                    else None
                ),
                "restartable": obj.get("restartable"),
                "schemaVersion": obj.get("schemaVersion"),
                "tasks": (
                    [WorkflowTaskAdapter.from_dict(_item) for _item in obj["tasks"]]
                    if obj.get("tasks") is not None
                    else None
                ),
                "timeoutPolicy": obj.get("timeoutPolicy"),
                "timeoutSeconds": obj.get("timeoutSeconds"),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
                "variables": obj.get("variables"),
                "version": obj.get("version"),
                "workflowStatusListenerEnabled": obj.get(
                    "workflowStatusListenerEnabled"
                ),
                "workflowStatusListenerSink": obj.get("workflowStatusListenerSink"),
            }
        )
        return _obj
