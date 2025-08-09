from __future__ import annotations

from typing import Any, Dict, List, Optional

from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import IntegrationApi


class IntegrationApiAdapter(IntegrationApi):
    configuration: Optional[Dict[str, Any]] = None
    tags: Optional[List[TagAdapter]] = None
