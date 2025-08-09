from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import MessageTemplate


class MessageTemplateAdapter(MessageTemplate):
    tags: Optional[List[TagAdapter]] = None
