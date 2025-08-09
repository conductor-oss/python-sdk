from __future__ import annotations

from typing import Any, Optional

from conductor.asyncio_client.http.models import SubWorkflowParams


class SubWorkflowParamsAdapter(SubWorkflowParams):
    priority: Optional[Any] = None
