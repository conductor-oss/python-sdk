from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import ExtendedSecret


class ExtendedSecretAdapter(ExtendedSecret):
    tags: Optional[List[TagAdapter]] = None
