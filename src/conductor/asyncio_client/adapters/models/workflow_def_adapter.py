from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import WorkflowDef


class WorkflowDefAdapter(WorkflowDef):
    input_template: Optional[Dict[str, Any]] = Field(default=None, alias="inputTemplate")
    output_parameters: Optional[Dict[str, Any]] = Field(default=None, alias="outputParameters")
    variables: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    tasks: List["WorkflowTaskAdapter"]
    schema_version: Optional[int] = Field(default=None, alias="schemaVersion")
    output_schema: Optional["SchemaDefAdapter"] = Field(default=None, alias="outputSchema")
    input_schema: Optional["SchemaDefAdapter"] = Field(default=None, alias="inputSchema")
    rate_limit_config: Optional["RateLimitConfigAdapter"] = Field(
        default=None, alias="rateLimitConfig"
    )
    timeout_seconds: Optional[int] = Field(default=None, alias="timeoutSeconds")

    __properties: ClassVar[List[str]] = [
        "createTime",
        "createdBy",
        "description",
        "enforceSchema",
        "failureWorkflow",
        "inputParameters",
        "inputSchema",
        "inputTemplate",
        "name",
        "outputParameters",
        "outputSchema",
        "ownerApp",
        "ownerEmail",
        "rateLimitConfig",
        "restartable",
        "schemaVersion",
        "tasks",
        "timeoutPolicy",
        "timeoutSeconds",
        "updateTime",
        "updatedBy",
        "variables",
        "version",
        "workflowStatusListenerEnabled",
        "workflowStatusListenerSink",
        "metadata",
    ]

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
                "metadata": obj.get("metadata"),
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
                "workflowStatusListenerEnabled": obj.get("workflowStatusListenerEnabled"),
                "workflowStatusListenerSink": obj.get("workflowStatusListenerSink"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.rate_limit_config_adapter import (  # noqa: E402
    RateLimitConfigAdapter,
)
from conductor.asyncio_client.adapters.models.schema_def_adapter import (  # noqa: E402
    SchemaDefAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_task_adapter import (  # noqa: E402
    WorkflowTaskAdapter,
)

WorkflowDefAdapter.model_rebuild(raise_errors=False)
