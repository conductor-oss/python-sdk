from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from conductor.asyncio_client.http.models import TaskExecLog


class TaskExecLogAdapter(TaskExecLog):
    created_time: Optional[Any] = Field(default=None, alias="createdTime")
