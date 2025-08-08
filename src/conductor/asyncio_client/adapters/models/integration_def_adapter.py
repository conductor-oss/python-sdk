from __future__ import annotations

from typing import Optional, List
from pydantic import Field

from conductor.asyncio_client.adapters.models.option_adapter import OptionAdapter
from conductor.asyncio_client.http.models import IntegrationDef


class IntegrationDefAdapter(IntegrationDef):
    value_options: Optional[List[OptionAdapter]] = Field(default=None, alias="valueOptions")
