from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional

from pydantic import StrictStr
from typing_extensions import Self

from conductor.asyncio_client.http.models import TaskSummary


class TaskSummaryAdapter(TaskSummary):
    domain: Optional[StrictStr] = None
    __properties: ClassVar[List[str]] = [
        "correlationId",
        "endTime",
        "executionTime",
        "externalInputPayloadStoragePath",
        "externalOutputPayloadStoragePath",
        "input",
        "output",
        "queueWaitTime",
        "reasonForIncompletion",
        "scheduledTime",
        "startTime",
        "status",
        "taskDefName",
        "taskId",
        "taskReferenceName",
        "taskType",
        "updateTime",
        "workflowId",
        "workflowPriority",
        "workflowType",
        "domain",
    ]

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of TaskSummary from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "correlationId": obj.get("correlationId"),
                "endTime": obj.get("endTime"),
                "executionTime": obj.get("executionTime"),
                "externalInputPayloadStoragePath": obj.get("externalInputPayloadStoragePath"),
                "externalOutputPayloadStoragePath": obj.get("externalOutputPayloadStoragePath"),
                "input": obj.get("input"),
                "output": obj.get("output"),
                "queueWaitTime": obj.get("queueWaitTime"),
                "reasonForIncompletion": obj.get("reasonForIncompletion"),
                "scheduledTime": obj.get("scheduledTime"),
                "startTime": obj.get("startTime"),
                "status": obj.get("status"),
                "taskDefName": obj.get("taskDefName"),
                "taskId": obj.get("taskId"),
                "taskReferenceName": obj.get("taskReferenceName"),
                "taskType": obj.get("taskType"),
                "updateTime": obj.get("updateTime"),
                "workflowId": obj.get("workflowId"),
                "workflowPriority": obj.get("workflowPriority"),
                "workflowType": obj.get("workflowType"),
                "domain": obj.get("domain"),
            }
        )
        return _obj
