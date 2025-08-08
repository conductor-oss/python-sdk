from __future__ import annotations

from typing import Any, Dict, Optional, List
from conductor.asyncio_client.http.models import WorkflowRun
from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter


class WorkflowRunAdapter(WorkflowRun):
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    tasks: Optional[List[TaskAdapter]] = None
    variables: Optional[Dict[str, Any]] = None
