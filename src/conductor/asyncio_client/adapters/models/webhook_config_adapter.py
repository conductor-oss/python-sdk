from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import Field
from conductor.asyncio_client.http.models import WebhookConfig
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.webhook_execution_history_adapter import WebhookExecutionHistoryAdapter


class WebhookConfigAdapter(WebhookConfig):
    tags: Optional[List[TagAdapter]] = None
    webhook_execution_history: Optional[List[WebhookExecutionHistoryAdapter]] = Field(default=None, alias="webhookExecutionHistory")
    workflows_to_start: Optional[Dict[str, Any]] = Field(default=None, alias="workflowsToStart")
