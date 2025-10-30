from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import Task


class TaskAdapter(Task):
    input_data: Optional[Dict[str, Any]] = Field(default=None, alias="inputData")
    output_data: Optional[Dict[str, Any]] = Field(default=None, alias="outputData")
    task_definition: Optional["TaskDefAdapter"] = Field(default=None, alias="taskDefinition")
    workflow_task: Optional["WorkflowTaskAdapter"] = Field(default=None, alias="workflowTask")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Task from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "callbackAfterSeconds": obj.get("callbackAfterSeconds"),
                "callbackFromWorker": obj.get("callbackFromWorker"),
                "correlationId": obj.get("correlationId"),
                "domain": obj.get("domain"),
                "endTime": obj.get("endTime"),
                "executed": obj.get("executed"),
                "executionNameSpace": obj.get("executionNameSpace"),
                "externalInputPayloadStoragePath": obj.get("externalInputPayloadStoragePath"),
                "externalOutputPayloadStoragePath": obj.get("externalOutputPayloadStoragePath"),
                "firstStartTime": obj.get("firstStartTime"),
                "inputData": obj.get("inputData"),
                "isolationGroupId": obj.get("isolationGroupId"),
                "iteration": obj.get("iteration"),
                "loopOverTask": obj.get("loopOverTask"),
                "outputData": obj.get("outputData"),
                "parentTaskId": obj.get("parentTaskId"),
                "pollCount": obj.get("pollCount"),
                "queueWaitTime": obj.get("queueWaitTime"),
                "rateLimitFrequencyInSeconds": obj.get("rateLimitFrequencyInSeconds"),
                "rateLimitPerFrequency": obj.get("rateLimitPerFrequency"),
                "reasonForIncompletion": obj.get("reasonForIncompletion"),
                "referenceTaskName": obj.get("referenceTaskName"),
                "responseTimeoutSeconds": obj.get("responseTimeoutSeconds"),
                "retried": obj.get("retried"),
                "retriedTaskId": obj.get("retriedTaskId"),
                "retryCount": obj.get("retryCount"),
                "scheduledTime": obj.get("scheduledTime"),
                "seq": obj.get("seq"),
                "startDelayInSeconds": obj.get("startDelayInSeconds"),
                "startTime": obj.get("startTime"),
                "status": obj.get("status"),
                "subWorkflowId": obj.get("subWorkflowId"),
                "subworkflowChanged": obj.get("subworkflowChanged"),
                "taskDefName": obj.get("taskDefName"),
                "taskDefinition": (
                    TaskDefAdapter.from_dict(obj["taskDefinition"])
                    if obj.get("taskDefinition") is not None
                    else None
                ),
                "taskId": obj.get("taskId"),
                "taskType": obj.get("taskType"),
                "updateTime": obj.get("updateTime"),
                "workerId": obj.get("workerId"),
                "workflowInstanceId": obj.get("workflowInstanceId"),
                "workflowPriority": obj.get("workflowPriority"),
                "workflowTask": (
                    WorkflowTaskAdapter.from_dict(obj["workflowTask"])
                    if obj.get("workflowTask") is not None
                    else None
                ),
                "workflowType": obj.get("workflowType"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.task_def_adapter import (  # noqa: E402
    TaskDefAdapter,
)
from conductor.asyncio_client.adapters.models.workflow_task_adapter import (  # noqa: E402
    WorkflowTaskAdapter,
)

TaskAdapter.model_rebuild(raise_errors=False)
