from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import Workflow


class WorkflowAdapter(Workflow):
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    workflow_definition: Optional["WorkflowDefAdapter"] = Field(
        default=None, alias="workflowDefinition"
    )
    tasks: Optional[List["TaskAdapter"]] = None
    history: Optional[List["WorkflowAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Workflow from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter
        from conductor.asyncio_client.adapters.models.workflow_def_adapter import (
            WorkflowDefAdapter,
        )

        _obj = cls.model_validate(
            {
                "correlationId": obj.get("correlationId"),
                "createTime": obj.get("createTime"),
                "createdBy": obj.get("createdBy"),
                "endTime": obj.get("endTime"),
                "event": obj.get("event"),
                "externalInputPayloadStoragePath": obj.get(
                    "externalInputPayloadStoragePath"
                ),
                "externalOutputPayloadStoragePath": obj.get(
                    "externalOutputPayloadStoragePath"
                ),
                "failedReferenceTaskNames": obj.get("failedReferenceTaskNames"),
                "failedTaskNames": obj.get("failedTaskNames"),
                "history": (
                    [WorkflowAdapter.from_dict(_item) for _item in obj["history"]]
                    if obj.get("history") is not None
                    else None
                ),
                "idempotencyKey": obj.get("idempotencyKey"),
                "input": obj.get("input"),
                "lastRetriedTime": obj.get("lastRetriedTime"),
                "output": obj.get("output"),
                "ownerApp": obj.get("ownerApp"),
                "parentWorkflowId": obj.get("parentWorkflowId"),
                "parentWorkflowTaskId": obj.get("parentWorkflowTaskId"),
                "priority": obj.get("priority"),
                "rateLimitKey": obj.get("rateLimitKey"),
                "rateLimited": obj.get("rateLimited"),
                "reRunFromWorkflowId": obj.get("reRunFromWorkflowId"),
                "reasonForIncompletion": obj.get("reasonForIncompletion"),
                "startTime": obj.get("startTime"),
                "status": obj.get("status"),
                "taskToDomain": obj.get("taskToDomain"),
                "tasks": (
                    [TaskAdapter.from_dict(_item) for _item in obj["tasks"]]
                    if obj.get("tasks") is not None
                    else None
                ),
                "updateTime": obj.get("updateTime"),
                "updatedBy": obj.get("updatedBy"),
                "variables": obj.get("variables"),
                "workflowDefinition": (
                    WorkflowDefAdapter.from_dict(obj["workflowDefinition"])
                    if obj.get("workflowDefinition") is not None
                    else None
                ),
                "workflowId": obj.get("workflowId"),
                "workflowName": obj.get("workflowName"),
                "workflowVersion": obj.get("workflowVersion"),
            }
        )
        return _obj
