from __future__ import annotations

from typing import Any, Dict, Optional, Self

from conductor.asyncio_client.http.models import Action


class ActionAdapter(Action):
    complete_task: Optional["TaskDetailsAdapter"] = None
    fail_task: Optional["TaskDetailsAdapter"] = None
    start_workflow: Optional["StartWorkflowRequestAdapter"] = None
    terminate_workflow: Optional["TerminateWorkflowAdapter"] = None
    update_workflow_variables: Optional["UpdateWorkflowVariablesAdapter"] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Action from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "action": obj.get("action"),
                "complete_task": (
                    TaskDetailsAdapter.from_dict(obj["complete_task"])
                    if obj.get("complete_task") is not None
                    else None
                ),
                "expandInlineJSON": obj.get("expandInlineJSON"),
                "fail_task": (
                    TaskDetailsAdapter.from_dict(obj["fail_task"])
                    if obj.get("fail_task") is not None
                    else None
                ),
                "start_workflow": (
                    StartWorkflowRequestAdapter.from_dict(obj["start_workflow"])
                    if obj.get("start_workflow") is not None
                    else None
                ),
                "terminate_workflow": (
                    TerminateWorkflowAdapter.from_dict(obj["terminate_workflow"])
                    if obj.get("terminate_workflow") is not None
                    else None
                ),
                "update_workflow_variables": (
                    UpdateWorkflowVariablesAdapter.from_dict(
                        obj["update_workflow_variables"]
                    )
                    if obj.get("update_workflow_variables") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import (
    StartWorkflowRequestAdapter,
)
from conductor.asyncio_client.adapters.models.task_details_adapter import (
    TaskDetailsAdapter,
)
from conductor.asyncio_client.adapters.models.terminate_workflow_adapter import (
    TerminateWorkflowAdapter,
)
from conductor.asyncio_client.adapters.models.update_workflow_variables_adapter import (
    UpdateWorkflowVariablesAdapter,
)

ActionAdapter.model_rebuild(raise_errors=False)
