from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field

from conductor.asyncio_client.http.models import SkipTaskRequest


class SkipTaskRequestAdapter(SkipTaskRequest):
    task_input: Optional[Dict[str, Any]] = Field(default=None, alias="taskInput")
    task_output: Optional[Dict[str, Any]] = Field(default=None, alias="taskOutput")
