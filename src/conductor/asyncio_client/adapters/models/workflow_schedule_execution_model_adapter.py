from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import WorkflowScheduleExecutionModel


class WorkflowScheduleExecutionModelAdapter(WorkflowScheduleExecutionModel):
    start_workflow_request: Optional["StartWorkflowRequestAdapter"] = Field(
        default=None, alias="startWorkflowRequest"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkflowScheduleExecutionModel from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "executionId": obj.get("executionId"),
                "executionTime": obj.get("executionTime"),
                "orgId": obj.get("orgId"),
                "queueMsgId": obj.get("queueMsgId"),
                "reason": obj.get("reason"),
                "scheduleName": obj.get("scheduleName"),
                "scheduledTime": obj.get("scheduledTime"),
                "stackTrace": obj.get("stackTrace"),
                "startWorkflowRequest": (
                    StartWorkflowRequestAdapter.from_dict(obj["startWorkflowRequest"])
                    if obj.get("startWorkflowRequest") is not None
                    else None
                ),
                "state": obj.get("state"),
                "workflowId": obj.get("workflowId"),
                "workflowName": obj.get("workflowName"),
                "zoneId": obj.get("zoneId"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import (
    StartWorkflowRequestAdapter,
)

WorkflowScheduleExecutionModelAdapter.model_rebuild(raise_errors=False)
