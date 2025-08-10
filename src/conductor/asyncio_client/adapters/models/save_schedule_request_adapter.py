from __future__ import annotations

from typing import Any, Dict, Optional

from typing_extensions import Self

from pydantic import Field

from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import (
    StartWorkflowRequestAdapter,
)
from conductor.asyncio_client.http.models import SaveScheduleRequest


class SaveScheduleRequestAdapter(SaveScheduleRequest):
    start_workflow_request: StartWorkflowRequestAdapter = Field(
        alias="startWorkflowRequest"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of SaveScheduleRequest from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "createdBy": obj.get("createdBy"),
            "cronExpression": obj.get("cronExpression"),
            "description": obj.get("description"),
            "name": obj.get("name"),
            "paused": obj.get("paused"),
            "runCatchupScheduleInstances": obj.get("runCatchupScheduleInstances"),
            "scheduleEndTime": obj.get("scheduleEndTime"),
            "scheduleStartTime": obj.get("scheduleStartTime"),
            "startWorkflowRequest": StartWorkflowRequestAdapter.from_dict(obj["startWorkflowRequest"]) if obj.get("startWorkflowRequest") is not None else None,
            "updatedBy": obj.get("updatedBy"),
            "zoneId": obj.get("zoneId")
        })
        return _obj
