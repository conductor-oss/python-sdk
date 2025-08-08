from __future__ import annotations

from typing import Any, Dict, Optional, List
from pydantic import Field
from conductor.asyncio_client.http.models import WorkflowDef
from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter


class WorkflowDefAdapter(WorkflowDef):
    input_template: Optional[Dict[str, Any]] = Field(default=None, alias="inputTemplate")
    output_parameters: Optional[Dict[str, Any]] = Field(default=None, alias="outputParameters")
    variables: Optional[Dict[str, Any]] = None
    tasks: List[WorkflowTaskAdapter]
