from __future__ import annotations

from typing import Any, Dict, Optional

from conductor.asyncio_client.http.models import TaskDetails


class TaskDetailsAdapter(TaskDetails):
    output: Optional[Dict[str, Any]] = None
