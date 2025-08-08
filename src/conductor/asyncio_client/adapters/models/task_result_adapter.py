from typing import List, Optional, Dict, Any
from pydantic import Field
from conductor.asyncio_client.http.models import TaskResult
from conductor.asyncio_client.adapters.models.task_exec_log_adapter import TaskExecLogAdapter


class TaskResultAdapter(TaskResult):
    logs: Optional[List[TaskExecLogAdapter]] = None
    output_data: Optional[Dict[str, Any]] = Field(default=None, alias="outputData")
