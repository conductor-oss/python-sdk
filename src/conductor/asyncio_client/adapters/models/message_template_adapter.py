from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.http.models import MessageTemplate
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter


class MessageTemplateAdapter(MessageTemplate):
    tags: Optional[List[TagAdapter]] = None
