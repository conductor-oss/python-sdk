from __future__ import annotations

from typing import Optional, List
from pydantic import Field
from conductor.asyncio_client.http.models import WorkflowSchedule
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter


class WorkflowScheduleAdapter(WorkflowSchedule):
    start_workflow_request: Optional[StartWorkflowRequestAdapter] = Field(default=None, alias="startWorkflowRequest")
    tags: Optional[List[TagAdapter]] = None
