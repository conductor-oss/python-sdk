from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field

from conductor.asyncio_client.http.models import RerunWorkflowRequest


class RerunWorkflowRequestAdapter(RerunWorkflowRequest):
    task_input: Optional[Dict[str, Any]] = Field(default=None, alias="taskInput")
    workflow_input: Optional[Dict[str, Any]] = Field(
        default=None, alias="workflowInput"
    )
