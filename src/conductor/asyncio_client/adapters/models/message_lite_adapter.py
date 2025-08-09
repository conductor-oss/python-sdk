from __future__ import annotations

from typing import Optional

from pydantic import Field

from conductor.asyncio_client.http.models import MessageLite


class MessageLiteAdapter(MessageLite):
    default_instance_for_type: Optional[MessageLiteAdapter] = Field(
        default=None, alias="defaultInstanceForType"
    )
