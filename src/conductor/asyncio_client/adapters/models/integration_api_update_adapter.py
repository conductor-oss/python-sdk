from __future__ import annotations

from typing import Any, Dict, Optional

from conductor.asyncio_client.http.models import IntegrationApiUpdate


class IntegrationApiUpdateAdapter(IntegrationApiUpdate):
    configuration: Optional[Dict[str, Any]] = None
