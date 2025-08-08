from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import Field
from conductor.asyncio_client.http.models import TaskDef
from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter


class TaskDefAdapter(TaskDef):
    input_schema: Optional[SchemaDefAdapter] = Field(default=None, alias="inputSchema")
    input_template: Optional[Dict[str, Any]] = Field(default=None, alias="inputTemplate")
    output_schema: Optional[SchemaDefAdapter] = Field(default=None, alias="outputSchema")
