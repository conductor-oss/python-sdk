from __future__ import annotations

from typing import Any, Dict, Optional
from conductor.asyncio_client.http.models import WorkflowStatus


class WorkflowStatusAdapter(WorkflowStatus):
    output: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
