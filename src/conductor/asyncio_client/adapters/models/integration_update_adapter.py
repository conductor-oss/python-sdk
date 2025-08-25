from __future__ import annotations

from typing import Any, Dict, Optional

from conductor.asyncio_client.http.models import IntegrationUpdate


class IntegrationUpdateAdapter(IntegrationUpdate):
    configuration: Optional[Dict[str, Any]] = None
