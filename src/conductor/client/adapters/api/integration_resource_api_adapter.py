from typing import List, Dict

from conductor.client.codegen.api.integration_resource_api import IntegrationResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.integration import Integration
from conductor.client.http.models.integration_api import IntegrationApi
from conductor.client.http.models.integration_def import IntegrationDef
from conductor.client.http.models.message_template import MessageTemplate
from conductor.client.http.models.event_log import EventLog
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.http.models.integration_update import IntegrationUpdate


class IntegrationResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = IntegrationResourceApi(api_client)

    def associate_prompt_with_integration(
        self, integration_provider: str, integration_name: str, prompt_name: str, **kwargs
    ) -> None:
        """Associate a Prompt Template with an Integration"""
        return self._api.associate_prompt_with_integration(
            integration_provider, integration_name, prompt_name, **kwargs
        )

    def delete_integration_api(self, name: str, integration_name: str, **kwargs) -> None:
        """Delete an Integration"""
        return self._api.delete_integration_api(name, integration_name, **kwargs)

    def delete_integration_provider(self, name: str, **kwargs) -> None:
        """Delete an Integration Provider"""
        return self._api.delete_integration_provider(name, **kwargs)

    def delete_tag_for_integration(
        self, body: List[Tag], name: str, integration_name: str, **kwargs
    ) -> None:
        """Delete a Tag for an Integration"""
        return self._api.delete_tag_for_integration(body, name, integration_name, **kwargs)

    def delete_tag_for_integration_provider(self, body: List[Tag], name: str, **kwargs) -> None:
        """Delete a Tag for an Integration Provider"""
        return self._api.delete_tag_for_integration_provider(body, name, **kwargs)

    def get_all_integrations(self, **kwargs) -> List[Integration]:
        """Get all Integrations"""
        return self._api.get_all_integrations(**kwargs)

    def get_integration_api(self, name: str, integration_name: str, **kwargs) -> IntegrationApi:
        """Get an Integration API"""
        return self._api.get_integration_api(name, integration_name, **kwargs)

    def get_integration_apis(self, name: str, **kwargs) -> List[IntegrationApi]:
        """Get Integrations of an Integration Provider"""
        return self._api.get_integration_apis(name, **kwargs)

    def get_integration_available_apis(self, name: str, **kwargs) -> List[str]:
        """Get Integrations Available for an Integration Provider"""
        return self._api.get_integration_available_apis(name, **kwargs)

    def get_integration_provider(self, name: str, **kwargs) -> Integration:
        """Get an Integration Provider"""
        return self._api.get_integration_provider(name, **kwargs)

    def get_integration_provider_defs(self, **kwargs) -> List[IntegrationDef]:
        """Get Integration provider definitions"""
        return self._api.get_integration_provider_defs(**kwargs)

    def get_integration_providers(self, **kwargs) -> List[Integration]:
        """Get all Integration Providers"""
        return self._api.get_integration_providers(**kwargs)

    def get_prompts_with_integration(
        self, integration_provider: str, integration_name: str, **kwargs
    ) -> List[MessageTemplate]:
        """Get the list of prompt templates associated with an integration"""
        return self._api.get_prompts_with_integration(
            integration_provider, integration_name, **kwargs
        )

    def get_providers_and_integrations(self, **kwargs) -> List[str]:
        """Get Integrations Providers and Integrations combo"""
        return self._api.get_providers_and_integrations(**kwargs)

    def get_tags_for_integration(self, name: str, integration_name: str, **kwargs) -> List[Tag]:
        """Get tags for an Integration"""
        return self._api.get_tags_for_integration(name, integration_name, **kwargs)

    def get_tags_for_integration_provider(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for an Integration Provider"""
        return self._api.get_tags_for_integration_provider(name, **kwargs)

    def get_token_usage_for_integration(self, name: str, integration_name: str, **kwargs) -> int:
        """Get Token Usage by Integration"""
        return self._api.get_token_usage_for_integration(name, integration_name, **kwargs)

    def get_token_usage_for_integration_provider(self, name: str, **kwargs) -> Dict[str, str]:
        """Get Token Usage by Integration Provider"""
        return self._api.get_token_usage_for_integration_provider(name, **kwargs)

    def put_tag_for_integration(
        self, body: List[Tag], name: str, integration_name: str, **kwargs
    ) -> None:
        """Put a Tag for an Integration"""
        return self._api.put_tag_for_integration(body, name, integration_name, **kwargs)

    def put_tag_for_integration_provider(self, body: List[Tag], name: str, **kwargs) -> None:
        """Put a Tag for an Integration Provider"""
        return self._api.put_tag_for_integration_provider(body, name, **kwargs)

    def record_event_stats(self, body: List[EventLog], type: str, **kwargs) -> None:
        """Record Event Stats"""
        return self._api.record_event_stats(body, type, **kwargs)

    def register_token_usage(self, body: int, name: str, integration_name: str, **kwargs) -> None:
        """Register Token Usage"""
        return self._api.register_token_usage(body, name, integration_name, **kwargs)

    def save_all_integrations(self, body: List[Integration], **kwargs) -> None:
        """Save all Integrations"""
        return self._api.save_all_integrations(body, **kwargs)

    def save_integration_api(
        self, body: IntegrationApiUpdate, name: str, integration_name: str, **kwargs
    ) -> None:
        """Save an Integration API"""
        return self._api.save_integration_api(body, name, integration_name, **kwargs)

    def save_integration_provider(self, body: IntegrationUpdate, name: str, **kwargs) -> None:
        """Save an Integration Provider"""
        return self._api.save_integration_provider(body, name, **kwargs)
