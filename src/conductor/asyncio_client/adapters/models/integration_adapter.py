from __future__ import annotations

from typing import Dict, Any, Optional, List

from conductor.asyncio_client.adapters.models.integration_api_adapter import IntegrationApiAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import Integration


class IntegrationAdapter(Integration):
    apis: Optional[List[IntegrationApiAdapter]] = None
    configuration: Optional[Dict[str, Any]] = None
    tags: Optional[List[TagAdapter]] = None
