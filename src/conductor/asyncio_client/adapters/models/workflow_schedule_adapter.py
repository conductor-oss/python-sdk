from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import WorkflowSchedule


class WorkflowScheduleAdapter(WorkflowSchedule):
    start_workflow_request: Optional["StartWorkflowRequestAdapter"] = Field(default=None, alias="startWorkflowRequest")
    tags: Optional[List["TagAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkflowSchedule from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "cronExpression": obj.get("cronExpression"),
                "description": obj.get("description"),
                "name": obj.get("name"),
                "paused": obj.get("paused"),
                "pausedReason": obj.get("pausedReason"),
                "runCatchupScheduleInstances": obj.get("runCatchupScheduleInstances"),
                "scheduleEndTime": obj.get("scheduleEndTime"),
                "scheduleStartTime": obj.get("scheduleStartTime"),
                "startWorkflowRequest": (
                    StartWorkflowRequestAdapter.from_dict(obj["startWorkflowRequest"])
                    if obj.get("startWorkflowRequest") is not None
                    else None
                ),
                "tags": (
                    [TagAdapter.from_dict(_item) for _item in obj["tags"]] if obj.get("tags") is not None else None
                ),
                "updatedBy": obj.get("updatedBy"),
                "updatedTime": obj.get("updatedTime"),
                "zoneId": obj.get("zoneId"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import (  # noqa: E402
    StartWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter  # noqa: E402

WorkflowScheduleAdapter.model_rebuild(raise_errors=False)
