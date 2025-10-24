from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import WebhookConfig


class WebhookConfigAdapter(WebhookConfig):
    tags: Optional[List["TagAdapter"]] = None  # type: ignore[assignment]
    webhook_execution_history: Optional[List["WebhookExecutionHistoryAdapter"]] = Field(  # type: ignore[assignment]
        default=None, alias="webhookExecutionHistory"
    )
    workflows_to_start: Optional[Dict[str, Any]] = Field(default=None, alias="workflowsToStart")

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WebhookConfig from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "createdBy": obj.get("createdBy"),
                "headerKey": obj.get("headerKey"),
                "headers": obj.get("headers"),
                "id": obj.get("id"),
                "name": obj.get("name"),
                "receiverWorkflowNamesToVersions": obj.get("receiverWorkflowNamesToVersions"),
                "secretKey": obj.get("secretKey"),
                "secretValue": obj.get("secretValue"),
                "sourcePlatform": obj.get("sourcePlatform"),
                "tags": (
                    [TagAdapter.from_dict(_item) for _item in obj["tags"]]
                    if obj.get("tags") is not None
                    else None
                ),
                "urlVerified": obj.get("urlVerified"),
                "verifier": obj.get("verifier"),
                "webhookExecutionHistory": (
                    [
                        WebhookExecutionHistoryAdapter.from_dict(_item)
                        for _item in obj["webhookExecutionHistory"]
                    ]
                    if obj.get("webhookExecutionHistory") is not None
                    else None
                ),
                "workflowsToStart": obj.get("workflowsToStart"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter  # noqa: E402
from conductor.asyncio_client.adapters.models.webhook_execution_history_adapter import (  # noqa: E402
    WebhookExecutionHistoryAdapter,
)

WebhookConfigAdapter.model_rebuild(raise_errors=False)
