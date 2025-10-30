from __future__ import absolute_import, annotations

from typing import List, Optional

from conductor.client.codegen.rest import ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import MessageTemplate
from conductor.client.http.models.integration import Integration
from conductor.client.http.models.integration_api import IntegrationApi
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.http.models.integration_def import IntegrationDef
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.integration_client import IntegrationClient
from conductor.client.orkes.orkes_base_client import OrkesBaseClient


class OrkesIntegrationClient(OrkesBaseClient, IntegrationClient):
    def __init__(self, configuration: Configuration):
        super(OrkesIntegrationClient, self).__init__(configuration)

    def associate_prompt_with_integration(
        self, ai_integration: str, model_name: str, prompt_name: str
    ):
        self._integration_api.associate_prompt_with_integration(
            ai_integration, model_name, prompt_name
        )

    def delete_integration_api(self, api_name: str, integration_name: str):
        self._integration_api.delete_integration_api(api_name, integration_name)

    def delete_integration(self, integration_name: str):
        self._integration_api.delete_integration_provider(integration_name)

    def get_integration_api(self, api_name: str, integration_name: str) -> Optional[IntegrationApi]:
        try:
            return self._integration_api.get_integration_api(api_name, integration_name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integration_apis(self, integration_name: str) -> List[IntegrationApi]:
        return self._integration_api.get_integration_apis(integration_name)

    def get_integration(self, integration_name: str) -> Optional[Integration]:
        try:
            return self._integration_api.get_integration_provider(integration_name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integrations(self) -> List[Integration]:
        return self._integration_api.get_integration_providers()

    def get_integration_provider(self, name: str) -> Optional[Integration]:
        """Get integration provider by name"""
        try:
            return self._integration_api.get_integration_provider(name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integration_providers(
        self, category: Optional[str] = None, active_only: Optional[bool] = None
    ) -> List[Integration]:
        """Get all integration providers with optional filtering"""
        kwargs = {}
        if category is not None:
            kwargs["category"] = category
        if active_only is not None:
            kwargs["active_only"] = active_only  # type: ignore[assignment]
        return self._integration_api.get_integration_providers(**kwargs)

    def get_integration_provider_defs(self) -> List[IntegrationDef]:
        """Get integration provider definitions"""
        return self._integration_api.get_integration_provider_defs()

    def get_prompts_with_integration(
        self, ai_integration: str, model_name: str
    ) -> List[MessageTemplate]:
        return self._integration_api.get_prompts_with_integration(ai_integration, model_name)

    def save_integration_api(self, integration_name, api_name, api_details: IntegrationApiUpdate):
        print(f"Saving integration API: {api_name} for integration: {integration_name}")
        self._integration_api.save_integration_api(
            body=api_details, name=api_name, integration_name=integration_name
        )

    def save_integration(self, integration_name, integration_details: IntegrationUpdate):
        self._integration_api.save_integration_provider(integration_details, integration_name)

    def save_integration_provider(self, name: str, integration_details: IntegrationUpdate) -> None:
        """Create or update an integration provider"""
        self._integration_api.save_integration_provider(integration_details, name)

    def get_token_usage_for_integration(self, name, integration_name) -> int:
        return self._integration_api.get_token_usage_for_integration(name, integration_name)

    def get_token_usage_for_integration_provider(self, name) -> dict:
        return self._integration_api.get_token_usage_for_integration_provider(name)

    def register_token_usage(self, body, name, integration_name):
        return self._integration_api.register_token_usage(body, name, integration_name)

    # Tags

    def delete_tag_for_integration(self, body, tag_name, integration_name):
        return self._integration_api.delete_tag_for_integration(body, tag_name, integration_name)

    def delete_tag_for_integration_provider(self, body, name):
        return self._integration_api.delete_tag_for_integration_provider(body, name)

    def put_tag_for_integration(self, body, name, integration_name):
        return self._integration_api.put_tag_for_integration(body, name, integration_name)

    def put_tag_for_integration_provider(self, body, name):
        return self._integration_api.put_tag_for_integration_provider(body, name)

    def get_tags_for_integration(self, name, integration_name):
        return self._integration_api.get_tags_for_integration(name, integration_name)

    def get_tags_for_integration_provider(self, name):
        return self._integration_api.get_tags_for_integration_provider(name)

    # Utility Methods for Integration Provider Management
    def get_integration_provider_by_category(
        self, category: str, active_only: bool = True
    ) -> List[Integration]:
        """Get integration providers filtered by category"""
        return self.get_integration_providers(category=category, active_only=active_only)

    def get_active_integration_providers(self) -> List[Integration]:
        """Get only active integration providers"""
        return self.get_integration_providers(active_only=True)

    def get_integration_available_apis(self, name: str) -> List[str]:
        """Get available APIs for an integration"""
        return self._integration_api.get_integration_available_apis(name)

    def save_all_integrations(self, request_body: List[IntegrationUpdate]) -> None:
        """Save all integrations"""
        self._integration_api.save_all_integrations(request_body)

    def get_all_integrations(
        self, category: Optional[str] = None, active_only: Optional[bool] = None
    ) -> List[Integration]:
        """Get all integrations with optional filtering"""
        kwargs = {}
        if category is not None:
            kwargs["category"] = category
        if active_only is not None:
            kwargs["active_only"] = active_only  # type: ignore[assignment]
        return self._integration_api.get_all_integrations(**kwargs)

    def get_providers_and_integrations(
        self, integration_type: Optional[str] = None, active_only: Optional[bool] = None
    ) -> List[str]:
        """Get providers and integrations together"""
        kwargs = {}
        if integration_type is not None:
            kwargs["type"] = integration_type
        if active_only is not None:
            kwargs["active_only"] = active_only  # type: ignore[assignment]
        return self._integration_api.get_providers_and_integrations(**kwargs)
