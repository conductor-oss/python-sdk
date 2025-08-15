from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import StartWorkflowRequest


class StartWorkflowRequestAdapter(StartWorkflowRequest):
    input: Optional[Dict[str, Any]] = None
    workflow_def: Optional["WorkflowDefAdapter"] = Field(
        default=None, alias="workflowDef"
    )
    priority: Optional[int] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of StartWorkflowRequest from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "correlationId": obj.get("correlationId"),
                "createdBy": obj.get("createdBy"),
                "externalInputPayloadStoragePath": obj.get(
                    "externalInputPayloadStoragePath"
                ),
                "idempotencyKey": obj.get("idempotencyKey"),
                "idempotencyStrategy": obj.get("idempotencyStrategy"),
                "input": obj.get("input"),
                "name": obj.get("name"),
                "priority": obj.get("priority"),
                "taskToDomain": obj.get("taskToDomain"),
                "version": obj.get("version"),
                "workflowDef": (
                    WorkflowDefAdapter.from_dict(obj["workflowDef"])
                    if obj.get("workflowDef") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.workflow_def_adapter import (
    WorkflowDefAdapter,
)

StartWorkflowRequestAdapter.model_rebuild(raise_errors=False)
