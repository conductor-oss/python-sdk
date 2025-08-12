from __future__ import annotations

from conductor.asyncio_client.http.models import TaskExecLog
from typing import Optional, Any
from pydantic import Field


class TaskExecLogAdapter(TaskExecLog):
    created_time: Optional[Any] = Field(default=None, alias="createdTime")
