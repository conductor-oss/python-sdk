from __future__ import annotations

from typing import Any, Dict, Optional, List
from pydantic import Field
from conductor.asyncio_client.http.models import WorkflowTestRequest
from conductor.asyncio_client.adapters.models.task_mock_adapter import TaskMockAdapter
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter


class WorkflowTestRequestAdapter(WorkflowTestRequest):
    input: Optional[Dict[str, Any]] = None
    sub_workflow_test_request: Optional[Dict[str, WorkflowTestRequestAdapter]] = Field(default=None, alias="subWorkflowTestRequest")
    task_ref_to_mock_output: Optional[Dict[str, List[TaskMockAdapter]]] = Field(default=None, alias="taskRefToMockOutput")
    workflow_def: Optional[WorkflowDefAdapter] = Field(default=None, alias="workflowDef")
