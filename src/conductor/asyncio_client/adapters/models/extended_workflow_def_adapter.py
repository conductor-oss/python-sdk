from __future__ import annotations

from typing import Dict, Any, Optional, List
from pydantic import Field

from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.asyncio_client.adapters.models.rate_limit_config_adapter import RateLimitConfigAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.http.models import ExtendedWorkflowDef

class ExtendedWorkflowDefAdapter(ExtendedWorkflowDef):
    input_schema: Optional[SchemaDefAdapter] = Field(default=None, alias="inputSchema")
    input_template: Optional[Dict[str, Any]] = Field(default=None, alias="inputTemplate")
    output_parameters: Optional[Dict[str, Any]] = Field(default=None, alias="outputParameters")
    output_schema: Optional[SchemaDefAdapter] = Field(default=None, alias="outputSchema")
    rate_limit_config: Optional[RateLimitConfigAdapter] = Field(default=None, alias="rateLimitConfig")
    tags: Optional[List[TagAdapter]] = None
    tasks: List[WorkflowTaskAdapter]
    variables: Optional[Dict[str, Any]] = None
