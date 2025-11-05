from __future__ import absolute_import, annotations

from typing import Dict, List, Optional

from conductor.client.codegen.rest import ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import MessageTemplate
from conductor.client.http.models.event_log import EventLog
from conductor.client.http.models.integration import Integration
from conductor.client.http.models.integration_api import IntegrationApi
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.http.models.integration_def import IntegrationDef
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.tag import Tag
from conductor.client.integration_client import IntegrationClient
from conductor.client.orkes.orkes_base_client import OrkesBaseClient


class OrkesIntegrationClient(OrkesBaseClient, IntegrationClient):
    def __init__(self, configuration: Configuration):
        """Initialize the OrkesIntegrationClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            integration_client = OrkesIntegrationClient(config)
            ```
        """
        super().__init__(configuration)

    def associate_prompt_with_integration(
        self, ai_integration: str, model_name: str, prompt_name: str, **kwargs
    ) -> None:
        """Associate a prompt template with an AI integration.

        Args:
            ai_integration: Name of the AI integration provider (e.g., "openai")
            model_name: Name of the model (e.g., "gpt-4")
            prompt_name: Name of the prompt template
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            integration_client.associate_prompt_with_integration(
                "openai",
                "gpt-4",
                "customer_greeting"
            )
            ```
        """
        self._integration_api.associate_prompt_with_integration(
            integration_provider=ai_integration,
            integration_name=model_name,
            prompt_name=prompt_name,
            **kwargs,
        )

    def delete_integration_api(self, api_name: str, integration_name: str, **kwargs) -> None:
        """Delete an integration API configuration.

        Args:
            api_name: Name of the API to delete
            integration_name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            integration_client.delete_integration_api("payment_api", "stripe")
            ```
        """
        self._integration_api.delete_integration_api(
            name=api_name, integration_name=integration_name, **kwargs
        )

    def delete_integration(self, integration_name: str, **kwargs) -> None:
        """Delete an integration provider.

        Args:
            integration_name: Name of the integration to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            integration_client.delete_integration("old_stripe_integration")
            ```
        """
        self._integration_api.delete_integration_provider(name=integration_name, **kwargs)

    def get_integration_api(
        self, api_name: str, integration_name: str, **kwargs
    ) -> Optional[IntegrationApi]:
        """Get an integration API configuration by name.

        Args:
            api_name: Name of the API
            integration_name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            IntegrationApi instance if found, None otherwise

        Example:
            ```python
            api = integration_client.get_integration_api("payment_api", "stripe")
            if api:
                print(f"API: {api.name}, Endpoint: {api.endpoint}")
            ```
        """
        try:
            return self._integration_api.get_integration_api(
                name=api_name, integration_name=integration_name, **kwargs
            )
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integration_apis(self, integration_name: str, **kwargs) -> List[IntegrationApi]:
        """Get all API configurations for an integration.

        Args:
            integration_name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of IntegrationApi instances

        Example:
            ```python
            apis = integration_client.get_integration_apis("stripe")
            for api in apis:
                print(f"API: {api.name}")
            ```
        """
        return self._integration_api.get_integration_apis(name=integration_name, **kwargs)

    def get_integration(self, integration_name: str, **kwargs) -> Optional[Integration]:
        """Get an integration by name.

        Args:
            integration_name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Integration instance if found, None otherwise

        Example:
            ```python
            integration = integration_client.get_integration("stripe")
            if integration:
                print(f"Integration: {integration.name}, Enabled: {integration.enabled}")
            ```
        """
        try:
            return self._integration_api.get_integration_provider(name=integration_name, **kwargs)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integrations(self, **kwargs) -> List[Integration]:
        """Get all integrations.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Integration instances

        Example:
            ```python
            integrations = integration_client.get_integrations()
            for integration in integrations:
                print(f"Integration: {integration.name}")
            ```
        """
        return self._integration_api.get_integration_providers(**kwargs)

    def get_integration_provider(self, name: str, **kwargs) -> Optional[Integration]:
        """Get integration provider by name.

        Args:
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Integration instance if found, None otherwise

        Example:
            ```python
            provider = integration_client.get_integration_provider("openai")
            if provider:
                print(f"Provider: {provider.name}, Category: {provider.category}")
            ```
        """
        try:
            return self._integration_api.get_integration_provider(name=name, **kwargs)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integration_providers(
        self, category: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[Integration]:
        """Get all integration providers with optional filtering.

        Args:
            category: Optional category filter (e.g., "AI_MODEL", "DATABASE")
            active_only: If True, return only active providers
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Integration instances

        Example:
            ```python
            # Get all providers
            all_providers = integration_client.get_integration_providers()

            # Get only AI model providers
            ai_providers = integration_client.get_integration_providers(category="AI_MODEL")

            # Get only active providers
            active = integration_client.get_integration_providers(active_only=True)
            ```
        """
        if category is not None:
            kwargs["category"] = category
        if active_only is not None:
            kwargs["active_only"] = active_only
        return self._integration_api.get_integration_providers(**kwargs)

    def get_integration_provider_defs(self, **kwargs) -> List[IntegrationDef]:
        """Get integration provider definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of IntegrationDef instances with provider schemas

        Example:
            ```python
            defs = integration_client.get_integration_provider_defs()
            for definition in defs:
                print(f"Definition: {definition.name}")
            ```
        """
        return self._integration_api.get_integration_provider_defs(**kwargs)

    def get_prompts_with_integration(
        self, ai_integration: str, model_name: str, **kwargs
    ) -> List[MessageTemplate]:
        """Get prompts associated with an AI integration.

        Args:
            ai_integration: Name of the AI integration provider
            model_name: Name of the model
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplate instances

        Example:
            ```python
            prompts = integration_client.get_prompts_with_integration("openai", "gpt-4")
            for prompt in prompts:
                print(f"Prompt: {prompt.name}")
            ```
        """
        return self._integration_api.get_prompts_with_integration(
            integration_provider=ai_integration, integration_name=model_name, **kwargs
        )

    def save_integration_api(
        self, integration_name: str, api_name: str, api_details: IntegrationApiUpdate, **kwargs
    ) -> None:
        """Save an integration API configuration.

        Args:
            integration_name: Name of the integration
            api_name: Name of the API
            api_details: API configuration details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.integration_api_update import IntegrationApiUpdate

            api_details = IntegrationApiUpdate(
                endpoint="https://api.stripe.com/v1/charges",
                method="POST",
                headers={"Authorization": "Bearer ${api_key}"}
            )

            integration_client.save_integration_api("stripe", "create_charge", api_details)
            ```
        """
        self._integration_api.save_integration_api(
            body=api_details, name=api_name, integration_name=integration_name, **kwargs
        )

    def save_integration(
        self, integration_name: str, integration_details: IntegrationUpdate, **kwargs
    ) -> None:
        """Save an integration configuration.

        Args:
            integration_name: Name of the integration
            integration_details: Integration configuration details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.integration_update import IntegrationUpdate

            integration_details = IntegrationUpdate(
                category="PAYMENT",
                enabled=True,
                configuration={
                    "api_key": "sk_test_...",
                    "webhook_secret": "whsec_..."
                }
            )

            integration_client.save_integration("stripe", integration_details)
            ```
        """
        self._integration_api.save_integration_provider(
            body=integration_details, name=integration_name, **kwargs
        )

    def save_integration_provider(
        self, name: str, integration_details: IntegrationUpdate, **kwargs
    ) -> None:
        """Create or update an integration provider.

        Args:
            name: Name of the integration provider
            integration_details: Integration configuration details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.integration_update import IntegrationUpdate

            integration_details = IntegrationUpdate(
                category="AI_MODEL",
                type="openai",
                enabled=True,
                configuration={
                    "apiKey": "sk-...",
                    "model": "gpt-4"
                }
            )

            integration_client.save_integration_provider("my-openai", integration_details)
            ```
        """
        self._integration_api.save_integration_provider(
            body=integration_details, name=name, **kwargs
        )

    def get_token_usage_for_integration(self, name: str, integration_name: str, **kwargs) -> int:
        """Get token usage for a specific integration.

        Args:
            name: Name of the integration provider
            integration_name: Name of the specific integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Token usage count

        Example:
            ```python
            usage = integration_client.get_token_usage_for_integration("openai", "gpt-4")
            print(f"Tokens used: {usage}")
            ```
        """
        return self._integration_api.get_token_usage_for_integration(
            name=name, integration_name=integration_name, **kwargs
        )

    def get_token_usage_for_integration_provider(self, name: str, **kwargs) -> Dict[str, str]:
        """Get token usage for an integration provider.

        Args:
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping integration names to token usage

        Example:
            ```python
            usage = integration_client.get_token_usage_for_integration_provider("openai")
            for integration, tokens in usage.items():
                print(f"{integration}: {tokens} tokens")
            ```
        """
        return self._integration_api.get_token_usage_for_integration_provider(name=name, **kwargs)

    def register_token_usage(self, body: int, name: str, integration_name: str, **kwargs) -> None:
        """Register token usage for an integration.

        Args:
            body: Number of tokens used
            name: Name of the integration provider
            integration_name: Name of the specific integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Record 1500 tokens used
            integration_client.register_token_usage(1500, "openai", "gpt-4")
            ```
        """
        return self._integration_api.register_token_usage(
            body=body, name=name, integration_name=integration_name, **kwargs
        )

    # Tags

    def delete_tag_for_integration(
        self, body: List[Tag], tag_name: str, integration_name: str, **kwargs
    ) -> None:
        """Delete tags for a specific integration.

        Args:
            body: List of tags to delete
            tag_name: Name of the tag
            integration_name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags = [Tag(key="environment", value="staging")]
            integration_client.delete_tag_for_integration(tags, "env_tag", "stripe")
            ```
        """
        return self._integration_api.delete_tag_for_integration(
            body=body, name=tag_name, integration_name=integration_name, **kwargs
        )

    def delete_tag_for_integration_provider(self, body: List[Tag], name: str, **kwargs) -> None:
        """Delete tags for an integration provider.

        Args:
            body: List of tags to delete
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags = [Tag(key="category", value="deprecated")]
            integration_client.delete_tag_for_integration_provider(tags, "openai")
            ```
        """
        return self._integration_api.delete_tag_for_integration_provider(
            body=body, name=name, **kwargs
        )

    def put_tag_for_integration(
        self, body: List[Tag], name: str, integration_name: str, **kwargs
    ) -> None:
        """Set tags for a specific integration.

        Args:
            body: List of tags to set
            name: Name of the integration provider
            integration_name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags = [
                Tag(key="environment", value="production"),
                Tag(key="team", value="payments")
            ]
            integration_client.put_tag_for_integration(tags, "stripe", "payment_processor")
            ```
        """
        return self._integration_api.put_tag_for_integration(
            body=body, name=name, integration_name=integration_name, **kwargs
        )

    def put_tag_for_integration_provider(self, body: List[Tag], name: str, **kwargs) -> None:
        """Set tags for an integration provider.

        Args:
            body: List of tags to set
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags = [
                Tag(key="category", value="ai_model"),
                Tag(key="priority", value="high")
            ]
            integration_client.put_tag_for_integration_provider(tags, "openai")
            ```
        """
        return self._integration_api.put_tag_for_integration_provider(
            body=body, name=name, **kwargs
        )

    def get_tags_for_integration(self, name: str, integration_name: str, **kwargs) -> List[Tag]:
        """Get tags for a specific integration.

        Args:
            name: Name of the integration provider
            integration_name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Tag instances

        Example:
            ```python
            tags = integration_client.get_tags_for_integration("stripe", "payment_processor")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        return self._integration_api.get_tags_for_integration(
            name=name, integration_name=integration_name, **kwargs
        )

    def get_tags_for_integration_provider(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for an integration provider.

        Args:
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Tag instances

        Example:
            ```python
            tags = integration_client.get_tags_for_integration_provider("openai")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        return self._integration_api.get_tags_for_integration_provider(name=name, **kwargs)

    # Utility Methods for Integration Provider Management
    def get_integration_provider_by_category(
        self, category: str, active_only: bool = True, **kwargs
    ) -> List[Integration]:
        """Get integration providers filtered by category.

        Args:
            category: Category to filter by (e.g., "AI_MODEL", "DATABASE", "PAYMENT")
            active_only: If True, return only active providers
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Integration instances

        Example:
            ```python
            # Get all active AI model providers
            ai_providers = integration_client.get_integration_provider_by_category("AI_MODEL")
            ```
        """
        return self.get_integration_providers(category=category, active_only=active_only, **kwargs)

    def get_active_integration_providers(self, **kwargs) -> List[Integration]:
        """Get only active integration providers.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Integration instances

        Example:
            ```python
            active_providers = integration_client.get_active_integration_providers()
            print(f"Found {len(active_providers)} active providers")
            ```
        """
        return self.get_integration_providers(active_only=True, **kwargs)

    def get_integration_available_apis(self, name: str, **kwargs) -> List[str]:
        """Get available APIs for an integration.

        Args:
            name: Name of the integration
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of available API names

        Example:
            ```python
            apis = integration_client.get_integration_available_apis("stripe")
            print(f"Available APIs: {', '.join(apis)}")
            ```
        """
        return self._integration_api.get_integration_available_apis(name=name, **kwargs)

    def save_all_integrations(self, request_body: List[Integration], **kwargs) -> None:
        """Save multiple integrations in bulk.

        Args:
            request_body: List of Integration instances to save
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            integrations = [
                Integration(name="stripe", category="PAYMENT", enabled=True),
                Integration(name="openai", category="AI_MODEL", enabled=True)
            ]
            integration_client.save_all_integrations(integrations)
            ```
        """
        self._integration_api.save_all_integrations(body=request_body, **kwargs)

    def get_all_integrations(
        self, category: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[Integration]:
        """Get all integrations with optional filtering.

        Args:
            category: Optional category filter
            active_only: If True, return only active integrations
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Integration instances

        Example:
            ```python
            # Get all integrations
            all_integrations = integration_client.get_all_integrations()

            # Get only active payment integrations
            payments = integration_client.get_all_integrations(
                category="PAYMENT",
                active_only=True
            )
            ```
        """
        if category is not None:
            kwargs["category"] = category
        if active_only is not None:
            kwargs["active_only"] = active_only
        return self._integration_api.get_all_integrations(**kwargs)

    def get_providers_and_integrations(
        self, integration_type: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[str]:
        """Get providers and integrations together.

        Args:
            integration_type: Optional integration type filter
            active_only: If True, return only active items
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of provider and integration names

        Example:
            ```python
            all_items = integration_client.get_providers_and_integrations()
            print(f"Total providers and integrations: {len(all_items)}")
            ```
        """
        if integration_type is not None:
            kwargs["type"] = integration_type
        if active_only is not None:
            kwargs["active_only"] = active_only
        return self._integration_api.get_providers_and_integrations(**kwargs)

    def record_event_stats(self, body: List[EventLog], type: str, **kwargs) -> None:
        """Record event statistics for integrations.

        Args:
            body: List of event logs to record
            type: Type of event
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.event_log import EventLog

            event_logs = [
                EventLog(
                    event_type="API_CALL",
                    integration_name="stripe",
                    timestamp=1234567890
                )
            ]
            integration_client.record_event_stats(event_logs, "API_USAGE")
            ```
        """
        self._integration_api.record_event_stats(body=body, type=type, **kwargs)
