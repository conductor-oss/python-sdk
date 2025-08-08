from __future__ import annotations

from typing import Optional
from pydantic import Field
from conductor.asyncio_client.http.models import WorkflowScheduleExecutionModel
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter


class WorkflowScheduleExecutionModelAdapter(WorkflowScheduleExecutionModel):
    start_workflow_request: Optional[StartWorkflowRequestAdapter] = Field(default=None, alias="startWorkflowRequest")
