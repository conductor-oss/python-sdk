from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import SubWorkflowParams


class SubWorkflowParamsAdapter(SubWorkflowParams):
    priority: Optional[Any] = None
    workflow_definition: Optional[Any] = Field(default=None, alias="workflowDefinition")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of SubWorkflowParams from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "idempotencyKey": obj.get("idempotencyKey"),
                "idempotencyStrategy": obj.get("idempotencyStrategy"),
                "name": obj.get("name"),
                "priority": obj.get("priority"),
                "taskToDomain": obj.get("taskToDomain"),
                "version": obj.get("version"),
                "workflowDefinition": obj.get("workflowDefinition"),
            }
        )
        return _obj
