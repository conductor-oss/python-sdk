from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.models import ExtendedTaskDef


class ExtendedTaskDefAdapter(ExtendedTaskDef):
    input_schema: Optional[SchemaDefAdapter] = Field(default=None, alias="inputSchema")
    input_template: Optional[Dict[str, Any]] = Field(
        default=None, alias="inputTemplate"
    )
    output_schema: Optional[SchemaDefAdapter] = Field(
        default=None, alias="outputSchema"
    )
    tags: Optional[List[TagAdapter]] = None
