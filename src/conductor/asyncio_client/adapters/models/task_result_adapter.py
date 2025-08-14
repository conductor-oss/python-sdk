from __future__ import annotations

from typing import Any, Dict, List, Optional, Self

from pydantic import Field

from conductor.asyncio_client.http.models import TaskResult


class TaskResultAdapter(TaskResult):
    logs: Optional[List["TaskExecLogAdapter"]] = None
    output_data: Optional[Dict[str, Any]] = Field(default=None, alias="outputData")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of TaskResult from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.task_exec_log_adapter import (
            TaskExecLogAdapter,
        )

        _obj = cls.model_validate(
            {
                "callbackAfterSeconds": obj.get("callbackAfterSeconds"),
                "extendLease": obj.get("extendLease"),
                "externalOutputPayloadStoragePath": obj.get(
                    "externalOutputPayloadStoragePath"
                ),
                "logs": (
                    [TaskExecLogAdapter.from_dict(_item) for _item in obj["logs"]]
                    if obj.get("logs") is not None
                    else None
                ),
                "outputData": obj.get("outputData"),
                "reasonForIncompletion": obj.get("reasonForIncompletion"),
                "status": obj.get("status"),
                "subWorkflowId": obj.get("subWorkflowId"),
                "taskId": obj.get("taskId"),
                "workerId": obj.get("workerId"),
                "workflowInstanceId": obj.get("workflowInstanceId"),
            }
        )
        return _obj
