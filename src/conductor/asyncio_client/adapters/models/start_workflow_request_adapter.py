from __future__ import annotations
from typing import Optional, Dict, Any

from conductor.asyncio_client.http.models import StartWorkflowRequest


class StartWorkflowRequestAdapter(StartWorkflowRequest):
    input: Optional[Dict[str, Any]] = None
