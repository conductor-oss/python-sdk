from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import Field
from conductor.asyncio_client.http.models import Workflow
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter


class WorkflowAdapter(Workflow):
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    workflow_definition: Optional[WorkflowDefAdapter] = Field(default=None, alias="workflowDefinition")
