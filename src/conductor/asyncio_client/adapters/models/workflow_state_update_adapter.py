from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.adapters.models.task_result_adapter import \
    TaskResultAdapter
from conductor.asyncio_client.http.models import WorkflowStateUpdate


class WorkflowStateUpdateAdapter(WorkflowStateUpdate):
    variables: Optional[Dict[str, Any]] = None
    task_result: Optional[TaskResultAdapter] = Field(default=None, alias="taskResult")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkflowStateUpdate from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "taskReferenceName": obj.get("taskReferenceName"),
                "taskResult": (
                    TaskResultAdapter.from_dict(obj["taskResult"])
                    if obj.get("taskResult") is not None
                    else None
                ),
                "variables": obj.get("variables"),
            }
        )
        return _obj
