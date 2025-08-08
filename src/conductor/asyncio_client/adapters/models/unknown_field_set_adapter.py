from __future__ import annotations

from typing import Optional
from pydantic import Field
from conductor.asyncio_client.http.models import UnknownFieldSet


class UnknownFieldSetAdapter(UnknownFieldSet):
    default_instance_for_type: Optional[UnknownFieldSetAdapter] = Field(default=None, alias="defaultInstanceForType")
