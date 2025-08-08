from __future__ import annotations

from pydantic import Field

from conductor.asyncio_client.http.models import SaveScheduleRequest
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter


class SaveScheduleRequestAdapter(SaveScheduleRequest):
    start_workflow_request: StartWorkflowRequestAdapter = Field(alias="startWorkflowRequest")
