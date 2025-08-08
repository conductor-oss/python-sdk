from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import Field
from conductor.asyncio_client.http.models import Task
from conductor.asyncio_client.adapters.models.task_def_adapter import TaskDefAdapter
from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter


class TaskAdapter(Task):
    input_data: Optional[Dict[str, Any]] = Field(default=None, alias="inputData")
    output_data: Optional[Dict[str, Any]] = Field(default=None, alias="outputData")
    task_definition: Optional[TaskDefAdapter] = Field(default=None, alias="taskDefinition")
    workflow_task: Optional[WorkflowTaskAdapter] = Field(default=None, alias="workflowTask")
