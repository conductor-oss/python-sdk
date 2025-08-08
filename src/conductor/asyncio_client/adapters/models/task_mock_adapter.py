from typing import Dict, Any, Optional
from conductor.asyncio_client.http.models import TaskMock


class TaskMockAdapter(TaskMock):
    output: Optional[Dict[str, Any]] = None
