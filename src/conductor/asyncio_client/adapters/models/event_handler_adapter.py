from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.adapters.models.action_adapter import ActionAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import EventHandler


class EventHandlerAdapter(EventHandler):
    actions: Optional[List[ActionAdapter]] = None
    tags: Optional[List[TagAdapter]] = None
