from __future__ import annotations

from typing import Dict, Any, Optional

from conductor.asyncio_client.http.models import StateChangeEvent


class StateChangeEventAdapter(StateChangeEvent):
    payload: Optional[Dict[str, Any]] = None
