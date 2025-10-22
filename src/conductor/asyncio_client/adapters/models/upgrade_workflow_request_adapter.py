from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field

from conductor.asyncio_client.http.models import UpgradeWorkflowRequest


class UpgradeWorkflowRequestAdapter(UpgradeWorkflowRequest):
    task_output: Optional[Dict[str, Any]] = Field(default=None, alias="taskOutput")
    workflow_input: Optional[Dict[str, Any]] = Field(default=None, alias="workflowInput")
