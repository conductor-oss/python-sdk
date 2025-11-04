from typing import Dict

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.incoming_webhook_resource_api import IncomingWebhookResourceApi


class IncomingWebhookResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = IncomingWebhookResourceApi(api_client)

    def handle_webhook(self, id: str, request_params: Dict[str, object], **kwargs) -> str:
        """Handle a webhook"""
        return self._api.handle_webhook(id, request_params, **kwargs)

    def handle_webhook1(
        self, body: str, request_params: Dict[str, object], id: str, **kwargs
    ) -> str:
        """Handle a webhook"""
        return self._api.handle_webhook1(body, request_params, id, **kwargs)
