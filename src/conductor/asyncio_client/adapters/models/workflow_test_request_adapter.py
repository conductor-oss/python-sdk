from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import WorkflowTestRequest


class WorkflowTestRequestAdapter(WorkflowTestRequest):
    input: Optional[Dict[str, Any]] = None
    sub_workflow_test_request: Optional[Dict[str, "WorkflowTestRequestAdapter"]] = (
        Field(default=None, alias="subWorkflowTestRequest")
    )
    task_ref_to_mock_output: Optional[Dict[str, List["TaskMockAdapter"]]] = Field(
        default=None, alias="taskRefToMockOutput"
    )
    workflow_def: Optional["WorkflowDefAdapter"] = Field(
        default=None, alias="workflowDef"
    )
    priority: Optional[int] = Field(default=None, alias="priority")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkflowTestRequest from a dict"""
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
                "subWorkflowTestRequest": (
                    {
                        _k: WorkflowTestRequestAdapter.from_dict(_v)
                        for _k, _v in obj["subWorkflowTestRequest"].items()
                    }
                    if obj.get("subWorkflowTestRequest") is not None
                    else None
                ),
                "taskRefToMockOutput": {
                    _k: (
                        [TaskMockAdapter.from_dict(_item) for _item in _v]
                        if _v is not None
                        else None
                    )
                    for _k, _v in obj.get("taskRefToMockOutput", {}).items()
                },
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


from conductor.asyncio_client.adapters.models.task_mock_adapter import (  # noqa: E402
    TaskMockAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_def_adapter import (  # noqa: E402
    WorkflowDefAdapter,
)

WorkflowTestRequestAdapter.model_rebuild(raise_errors=False)
