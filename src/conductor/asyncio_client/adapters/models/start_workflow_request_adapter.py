from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import Field
from conductor.asyncio_client.http.models import StartWorkflowRequest
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter


class StartWorkflowRequestAdapter(StartWorkflowRequest):
    input: Optional[Dict[str, Any]] = None
    workflow_def: Optional[WorkflowDefAdapter] = Field(default=None, alias="workflowDef")
