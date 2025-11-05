from typing import List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.webhooks_config_resource_api import WebhooksConfigResourceApi
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.webhook_config import WebhookConfig


class WebhooksConfigResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = WebhooksConfigResourceApi(api_client)

    def create_webhook(self, body: WebhookConfig, **kwargs) -> WebhookConfig:
        """Create a webhook"""
        return self._api.create_webhook(body, **kwargs)

    def delete_tag_for_webhook(self, body: List[Tag], **kwargs) -> None:
        """Delete a tag for webhook id"""
        return self._api.delete_tag_for_webhook(body, **kwargs)

    def delete_webhook(self, id: str, **kwargs) -> None:
        """Delete a webhook"""
        return self._api.delete_webhook(id, **kwargs)

    def get_all_webhook(self, **kwargs) -> List[WebhookConfig]:
        """Get all webhooks"""
        return self._api.get_all_webhook(**kwargs)

    def get_tags_for_webhook(self, id: str, **kwargs) -> List[Tag]:
        """Get tags for webhook id"""
        return self._api.get_tags_for_webhook(id, **kwargs)

    def get_webhook(self, id: str, **kwargs) -> WebhookConfig:
        """Get a webhook by id"""
        return self._api.get_webhook(id, **kwargs)

    def put_tag_for_webhook(self, body: List[Tag], id: str, **kwargs) -> None:
        """Put a tag for webhook id"""
        return self._api.put_tag_for_webhook(body, id, **kwargs)

    def update_webhook(self, body: WebhookConfig, id: str, **kwargs) -> WebhookConfig:
        """Update a webhook"""
        return self._api.update_webhook(body, id, **kwargs)
