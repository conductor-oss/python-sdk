from __future__ import absolute_import, annotations

from typing import Dict, List, Optional

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
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.event_log import EventLog


class OrkesIntegrationClient(OrkesBaseClient, IntegrationClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def associate_prompt_with_integration(
        self, ai_integration: str, model_name: str, prompt_name: str, **kwargs
    ) -> None:
        self._integration_api.associate_prompt_with_integration(
            ai_integration, model_name, prompt_name, **kwargs
        )

    def delete_integration_api(self, api_name: str, integration_name: str, **kwargs) -> None:
        self._integration_api.delete_integration_api(api_name, integration_name, **kwargs)

    def delete_integration(self, integration_name: str, **kwargs) -> None:
        self._integration_api.delete_integration_provider(integration_name, **kwargs)

    def get_integration_api(
        self, api_name: str, integration_name: str, **kwargs
    ) -> Optional[IntegrationApi]:
        try:
            return self._integration_api.get_integration_api(api_name, integration_name, **kwargs)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integration_apis(self, integration_name: str, **kwargs) -> List[IntegrationApi]:
        return self._integration_api.get_integration_apis(integration_name, **kwargs)

    def get_integration(self, integration_name: str, **kwargs) -> Optional[Integration]:
        try:
            return self._integration_api.get_integration_provider(integration_name, **kwargs)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integrations(self, **kwargs) -> List[Integration]:
        return self._integration_api.get_integration_providers(**kwargs)

    def get_integration_provider(self, name: str, **kwargs) -> Optional[Integration]:
        """Get integration provider by name"""
        try:
            return self._integration_api.get_integration_provider(name, **kwargs)
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
            kwargs["active_only"] = active_only
        return self._integration_api.get_integration_providers(**kwargs)

    def get_integration_provider_defs(self, **kwargs) -> List[IntegrationDef]:
        """Get integration provider definitions"""
        return self._integration_api.get_integration_provider_defs(**kwargs)

    def get_prompts_with_integration(
        self, ai_integration: str, model_name: str, **kwargs
    ) -> List[MessageTemplate]:
        """Get prompts with integration"""
        return self._integration_api.get_prompts_with_integration(
            ai_integration, model_name, **kwargs
        )

    def save_integration_api(
        self, integration_name: str, api_name: str, api_details: IntegrationApiUpdate, **kwargs
    ) -> None:
        """Save integration API"""
        self._integration_api.save_integration_api(
            body=api_details, name=api_name, integration_name=integration_name, **kwargs
        )

    def save_integration(
        self, integration_name: str, integration_details: IntegrationUpdate, **kwargs
    ) -> None:
        """Save integration"""
        self._integration_api.save_integration_provider(
            integration_details, integration_name, **kwargs
        )

    def save_integration_provider(
        self, name: str, integration_details: IntegrationUpdate, **kwargs
    ) -> None:
        """Create or update an integration provider"""
        self._integration_api.save_integration_provider(integration_details, name, **kwargs)

    def get_token_usage_for_integration(self, name: str, integration_name: str, **kwargs) -> int:
        """Get token usage for integration"""
        return self._integration_api.get_token_usage_for_integration(
            name, integration_name, **kwargs
        )

    def get_token_usage_for_integration_provider(self, name: str, **kwargs) -> Dict[str, str]:
        """Get token usage for integration provider"""
        return self._integration_api.get_token_usage_for_integration_provider(name, **kwargs)

    def register_token_usage(self, body: int, name: str, integration_name: str, **kwargs) -> None:
        """Register token usage"""
        return self._integration_api.register_token_usage(body, name, integration_name, **kwargs)

    # Tags

    def delete_tag_for_integration(
        self, body: List[Tag], tag_name: str, integration_name: str, **kwargs
    ) -> None:
        """Delete tag for integration"""
        return self._integration_api.delete_tag_for_integration(
            body, tag_name, integration_name, **kwargs
        )

    def delete_tag_for_integration_provider(self, body: List[Tag], name: str, **kwargs) -> None:
        """Delete tag for integration provider"""
        return self._integration_api.delete_tag_for_integration_provider(body, name, **kwargs)

    def put_tag_for_integration(
        self, body: List[Tag], name: str, integration_name: str, **kwargs
    ) -> None:
        """Put tag for integration"""
        return self._integration_api.put_tag_for_integration(body, name, integration_name, **kwargs)

    def put_tag_for_integration_provider(self, body: List[Tag], name: str, **kwargs) -> None:
        """Put tag for integration provider"""
        return self._integration_api.put_tag_for_integration_provider(body, name, **kwargs)

    def get_tags_for_integration(self, name: str, integration_name: str, **kwargs) -> List[Tag]:
        """Get tags for integration"""
        return self._integration_api.get_tags_for_integration(name, integration_name, **kwargs)

    def get_tags_for_integration_provider(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for integration provider"""
        return self._integration_api.get_tags_for_integration_provider(name, **kwargs)

    # Utility Methods for Integration Provider Management
    def get_integration_provider_by_category(
        self, category: str, active_only: bool = True, **kwargs
    ) -> List[Integration]:
        """Get integration providers filtered by category"""
        return self.get_integration_providers(category=category, active_only=active_only, **kwargs)

    def get_active_integration_providers(self, **kwargs) -> List[Integration]:
        """Get only active integration providers"""
        return self.get_integration_providers(active_only=True, **kwargs)

    def get_integration_available_apis(self, name: str, **kwargs) -> List[str]:
        """Get available APIs for an integration"""
        return self._integration_api.get_integration_available_apis(name, **kwargs)

    def save_all_integrations(self, request_body: List[Integration], **kwargs) -> None:
        """Save all integrations"""
        self._integration_api.save_all_integrations(request_body, **kwargs)

    def get_all_integrations(
        self,
        category: Optional[str] = None,
        active_only: Optional[bool] = None,
    ) -> List[Integration]:
        """Get all integrations with optional filtering"""
        kwargs = {}
        if category is not None:
            kwargs["category"] = category
        if active_only is not None:
            kwargs["active_only"] = active_only
        return self._integration_api.get_all_integrations(**kwargs)

    def get_providers_and_integrations(
        self, integration_type: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[str]:
        """Get providers and integrations together"""
        kwargs = {}
        if integration_type is not None:
            kwargs["type"] = integration_type
        if active_only is not None:
            kwargs["active_only"] = active_only
        return self._integration_api.get_providers_and_integrations(**kwargs)

    def record_event_stats(self, body: List[EventLog], type: str, **kwargs) -> None:
        """Record event stats"""
        self._integration_api.record_event_stats(body, type, **kwargs)
