from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import WorkflowRun


class WorkflowRunAdapter(WorkflowRun):
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    tasks: Optional[List["TaskAdapter"]] = None
    variables: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkflowRun from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "correlationId": obj.get("correlationId"),
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "input": obj.get("input"),
                "output": obj.get("output"),
                "priority": obj.get("priority"),
                "requestId": obj.get("requestId"),
                "status": obj.get("status"),
                "tasks": (
                    [TaskAdapter.from_dict(_item) for _item in obj["tasks"]]
                    if obj.get("tasks") is not None
                    else None
                ),
                "updateTime": obj.get("updateTime"),
                "variables": obj.get("variables"),
                "workflowId": obj.get("workflowId"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter

WorkflowRunAdapter.model_rebuild(raise_errors=False)
