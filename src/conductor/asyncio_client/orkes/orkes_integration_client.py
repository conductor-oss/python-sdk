from __future__ import annotations

from typing import Dict, List, Optional

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.event_log_adapter import EventLogAdapter
from conductor.asyncio_client.adapters.models.integration_adapter import IntegrationAdapter
from conductor.asyncio_client.adapters.models.integration_api_adapter import IntegrationApiAdapter
from conductor.asyncio_client.adapters.models.integration_api_update_adapter import (
    IntegrationApiUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.integration_def_adapter import IntegrationDefAdapter
from conductor.asyncio_client.adapters.models.integration_update_adapter import (
    IntegrationUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.message_template_adapter import MessageTemplateAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.exceptions import NotFoundException
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesIntegrationClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        """Initialize the OrkesIntegrationClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            integration_client = OrkesIntegrationClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # Integration Provider Operations
    async def save_integration_provider(
        self, name: str, integration_update: IntegrationUpdateAdapter, **kwargs
    ) -> None:
        """Create or update an integration provider.

        Integration providers are external services like AI models, databases, or APIs
        that can be integrated with Conductor workflows.

        Args:
            name: Unique name for the integration provider
            integration_update: Integration configuration including credentials and settings
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.integration_update_adapter import IntegrationUpdateAdapter

            # Create an OpenAI integration provider
            integration = IntegrationUpdateAdapter(
                category="AI_MODEL",
                type="openai",
                enabled=True,
                configuration={
                    "apiKey": "sk-...",
                    "model": "gpt-4"
                }
            )
            await integration_client.save_integration_provider("my-openai", integration)
            ```
        """
        await self._integration_api.save_integration_provider(
            name=name, integration_update=integration_update, **kwargs
        )

    async def save_integration(
        self, integration_name, integration_details: IntegrationUpdateAdapter, **kwargs
    ) -> None:
        """Create or update an integration (alias for save_integration_provider).

        Args:
            integration_name: Unique name for the integration
            integration_details: Integration configuration including credentials and settings
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.integration_update_adapter import IntegrationUpdateAdapter

            integration = IntegrationUpdateAdapter(
                category="VECTOR_DB",
                type="pinecone",
                enabled=True,
                configuration={"apiKey": "...", "environment": "us-east-1"}
            )
            await integration_client.save_integration("my-pinecone", integration)
            ```
        """
        await self._integration_api.save_integration_provider(
            name=integration_name, integration_update=integration_details, **kwargs
        )

    async def get_integration_provider(self, name: str, **kwargs) -> IntegrationAdapter:
        """Get integration provider by name.

        Args:
            name: Name of the integration provider to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            IntegrationAdapter instance containing the integration provider details

        Example:
            ```python
            integration = await integration_client.get_integration_provider("my-openai")
            print(f"Type: {integration.type}, Enabled: {integration.enabled}")
            ```
        """
        return await self._integration_api.get_integration_provider(name=name, **kwargs)

    async def get_integration(
        self, integration_name: str, **kwargs
    ) -> Optional[IntegrationAdapter]:
        """Get integration by name, returning None if not found.

        This is a safe version of get_integration_provider that returns None
        instead of raising an exception when the integration is not found.

        Args:
            integration_name: Name of the integration to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            IntegrationAdapter instance if found, None otherwise

        Example:
            ```python
            integration = await integration_client.get_integration("my-openai")
            if integration:
                print(f"Found integration: {integration.type}")
            else:
                print("Integration not found")
            ```
        """
        try:
            return await self.get_integration_provider(name=integration_name, **kwargs)
        except NotFoundException:
            return None

    async def delete_integration_provider(self, name: str, **kwargs) -> None:
        """Delete an integration provider.

        Args:
            name: Name of the integration provider to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await integration_client.delete_integration_provider("old-integration")
            ```
        """
        await self._integration_api.delete_integration_provider(name=name, **kwargs)

    async def get_integration_providers(
        self, category: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[IntegrationAdapter]:
        """Get all integration providers with optional filtering.

        Args:
            category: Optional category to filter by (e.g., "AI_MODEL", "VECTOR_DB")
            active_only: If True, only return active integrations. If None, return all
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of IntegrationAdapter instances

        Example:
            ```python
            # Get all active AI model integrations
            ai_integrations = await integration_client.get_integration_providers(
                category="AI_MODEL",
                active_only=True
            )
            for integration in ai_integrations:
                print(f"AI Model: {integration.name}, Type: {integration.type}")
            ```
        """
        return await self._integration_api.get_integration_providers(
            category=category, active_only=active_only, **kwargs
        )

    async def get_integration_provider_defs(self, **kwargs) -> List[IntegrationDefAdapter]:
        """Get integration provider definitions.

        Retrieves the definitions/schemas for all available integration types.
        These definitions specify what configuration parameters are required for each type.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of IntegrationDefAdapter instances containing integration type definitions

        Example:
            ```python
            # Get all available integration definitions
            defs = await integration_client.get_integration_provider_defs()
            for definition in defs:
                print(f"Type: {definition.type}, Category: {definition.category}")
                print(f"Required fields: {definition.required_fields}")
            ```
        """
        return await self._integration_api.get_integration_provider_defs(**kwargs)

    # Integration API Operations
    async def save_integration_api(
        self,
        name: str,
        integration_name: str,
        integration_api_update: IntegrationApiUpdateAdapter,
        **kwargs,
    ) -> None:
        """Create or update an integration API configuration.

        Integration APIs define specific API endpoints or functions that can be
        used with an integration provider (e.g., different OpenAI models or endpoints).

        Args:
            name: Name of the API configuration
            integration_name: Name of the parent integration provider
            integration_api_update: API configuration details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.integration_api_update_adapter import IntegrationApiUpdateAdapter

            # Configure GPT-4 API for OpenAI integration
            api_config = IntegrationApiUpdateAdapter(
                api="chat_completion",
                enabled=True,
                configuration={
                    "model": "gpt-4",
                    "temperature": 0.7
                }
            )
            await integration_client.save_integration_api(
                "gpt-4-chat",
                "my-openai",
                api_config
            )
            ```
        """
        await self._integration_api.save_integration_api(
            name=name,
            integration_name=integration_name,
            integration_api_update=integration_api_update,
            **kwargs,
        )

    async def get_integration_api(
        self, name: str, integration_name: str, **kwargs
    ) -> IntegrationApiAdapter:
        """Get integration API configuration by name.

        Args:
            name: Name of the API configuration
            integration_name: Name of the parent integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            IntegrationApiAdapter instance containing the API configuration

        Example:
            ```python
            api = await integration_client.get_integration_api("gpt-4-chat", "my-openai")
            print(f"API: {api.api}, Enabled: {api.enabled}")
            ```
        """
        return await self._integration_api.get_integration_api(
            name=name, integration_name=integration_name, **kwargs
        )

    async def delete_integration_api(self, name: str, integration_name: str, **kwargs) -> None:
        """Delete an integration API configuration.

        Args:
            name: Name of the API configuration to delete
            integration_name: Name of the parent integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await integration_client.delete_integration_api("gpt-4-chat", "my-openai")
            ```
        """
        await self._integration_api.delete_integration_api(
            name=name, integration_name=integration_name, **kwargs
        )

    async def get_integration_apis(
        self, integration_name: str, **kwargs
    ) -> List[IntegrationApiAdapter]:
        """Get all API configurations for a specific integration.

        Args:
            integration_name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of IntegrationApiAdapter instances

        Example:
            ```python
            apis = await integration_client.get_integration_apis("my-openai")
            for api in apis:
                print(f"API: {api.name}, Type: {api.api}")
            ```
        """
        return await self._integration_api.get_integration_apis(name=integration_name, **kwargs)

    async def get_integration_available_apis(self, name: str, **kwargs) -> List[str]:
        """Get available API types for an integration.

        Returns the list of API types that can be configured for a given
        integration type (e.g., for OpenAI: chat_completion, text_completion, etc.).

        Args:
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of available API type strings

        Example:
            ```python
            available_apis = await integration_client.get_integration_available_apis("my-openai")
            print(f"Available APIs: {available_apis}")
            # Output: ['chat_completion', 'text_completion', 'embeddings']
            ```
        """
        return await self._integration_api.get_integration_available_apis(name=name, **kwargs)

    # Integration Operations
    async def save_all_integrations(self, request_body: List[IntegrationAdapter], **kwargs) -> None:
        """Bulk save multiple integrations at once.

        Args:
            request_body: List of IntegrationAdapter instances to save
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            integrations = [
                IntegrationAdapter(name="openai-1", type="openai", enabled=True),
                IntegrationAdapter(name="pinecone-1", type="pinecone", enabled=True)
            ]
            await integration_client.save_all_integrations(integrations)
            ```
        """
        await self._integration_api.save_all_integrations(integration=request_body, **kwargs)

    async def get_all_integrations(
        self, category: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[IntegrationAdapter]:
        """Get all integrations with optional filtering.

        Args:
            category: Optional category to filter by (e.g., "AI_MODEL", "VECTOR_DB")
            active_only: If True, only return active integrations
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of IntegrationAdapter instances

        Example:
            ```python
            # Get all active vector database integrations
            vector_dbs = await integration_client.get_all_integrations(
                category="VECTOR_DB",
                active_only=True
            )
            ```
        """
        return await self._integration_api.get_all_integrations(
            category=category, active_only=active_only, **kwargs
        )

    async def get_providers_and_integrations(
        self, integration_type: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[str]:
        """Get providers and integrations combined.

        Returns a list of all integration and provider names, optionally
        filtered by type and active status.

        Args:
            integration_type: Optional integration type to filter by
            active_only: If True, only return active items
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of integration/provider name strings

        Example:
            ```python
            # Get all active AI model providers and integrations
            all_ai = await integration_client.get_providers_and_integrations(
                integration_type="AI_MODEL",
                active_only=True
            )
            ```
        """
        return await self._integration_api.get_providers_and_integrations(
            type=integration_type, active_only=active_only, **kwargs
        )

    # Tag Management Operations
    async def put_tag_for_integration(
        self, tags: List[TagAdapter], name: str, integration_name: str, **kwargs
    ) -> None:
        """Add tags to an integration API.

        Args:
            tags: List of tags to add
            name: Name of the API configuration
            integration_name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [
                TagAdapter(key="environment", value="production"),
                TagAdapter(key="model", value="gpt-4")
            ]
            await integration_client.put_tag_for_integration(tags, "gpt-4-chat", "my-openai")
            ```
        """
        await self._integration_api.put_tag_for_integration(
            name=name, integration_name=integration_name, tag=tags, **kwargs
        )

    async def get_tags_for_integration(
        self, name: str, integration_name: str, **kwargs
    ) -> List[TagAdapter]:
        """Get tags for an integration API.

        Args:
            name: Name of the API configuration
            integration_name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await integration_client.get_tags_for_integration("gpt-4-chat", "my-openai")
            for tag in tags:
                print(f"{tag.key}: {tag.value}")
            ```
        """
        return await self._integration_api.get_tags_for_integration(
            name=name, integration_name=integration_name, **kwargs
        )

    async def delete_tag_for_integration(
        self, tags: List[TagAdapter], name: str, integration_name: str, **kwargs
    ) -> None:
        """Delete tags from an integration API.

        Args:
            tags: List of tags to delete
            name: Name of the API configuration
            integration_name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="environment", value="production")]
            await integration_client.delete_tag_for_integration(tags, "gpt-4-chat", "my-openai")
            ```
        """
        await self._integration_api.delete_tag_for_integration(
            name=name, integration_name=integration_name, tag=tags, **kwargs
        )

    async def put_tag_for_integration_provider(
        self, body: List[TagAdapter], name: str, **kwargs
    ) -> None:
        """Add tags to an integration provider.

        Args:
            body: List of tags to add
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [
                TagAdapter(key="team", value="ai-platform"),
                TagAdapter(key="cost-center", value="engineering")
            ]
            await integration_client.put_tag_for_integration_provider(tags, "my-openai")
            ```
        """
        await self._integration_api.put_tag_for_integration_provider(name=name, tag=body, **kwargs)

    async def get_tags_for_integration_provider(self, name: str, **kwargs) -> List[TagAdapter]:
        """Get tags for an integration provider.

        Args:
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await integration_client.get_tags_for_integration_provider("my-openai")
            for tag in tags:
                print(f"{tag.key}: {tag.value}")
            ```
        """
        return await self._integration_api.get_tags_for_integration_provider(name=name, **kwargs)

    async def delete_tag_for_integration_provider(
        self, body: List[TagAdapter], name: str, **kwargs
    ) -> None:
        """Delete tags from an integration provider.

        Args:
            body: List of tags to delete
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="team", value="ai-platform")]
            await integration_client.delete_tag_for_integration_provider(tags, "my-openai")
            ```
        """
        await self._integration_api.delete_tag_for_integration_provider(
            name=name, tag=body, **kwargs
        )

    # Token Usage Operations
    async def get_token_usage_for_integration(
        self, name: str, integration_name: str, **kwargs
    ) -> int:
        """Get token usage for a specific integration API.

        Returns the total number of tokens consumed by a specific API configuration.

        Args:
            name: Name of the API configuration
            integration_name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Total token count as an integer

        Example:
            ```python
            usage = await integration_client.get_token_usage_for_integration(
                "gpt-4-chat",
                "my-openai"
            )
            print(f"Total tokens used: {usage}")
            ```
        """
        return await self._integration_api.get_token_usage_for_integration(
            name=name, integration_name=integration_name, **kwargs
        )

    async def get_token_usage_for_integration_provider(self, name: str, **kwargs) -> Dict[str, str]:
        """Get token usage for an integration provider.

        Returns token usage statistics for all APIs under an integration provider.

        Args:
            name: Name of the integration provider
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping API names to their token usage

        Example:
            ```python
            usage = await integration_client.get_token_usage_for_integration_provider("my-openai")
            for api_name, tokens in usage.items():
                print(f"{api_name}: {tokens} tokens")
            ```
        """
        return await self._integration_api.get_token_usage_for_integration_provider(
            name=name, **kwargs
        )

    async def register_token_usage(
        self, name: str, integration_name: str, tokens: int, **kwargs
    ) -> None:
        """Register token usage for an integration.

        Records token consumption for billing and monitoring purposes.

        Args:
            name: Name of the API configuration
            integration_name: Name of the integration provider
            tokens: Number of tokens consumed
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Register that 1500 tokens were consumed
            await integration_client.register_token_usage(
                "gpt-4-chat",
                "my-openai",
                1500
            )
            ```
        """
        await self._integration_api.register_token_usage(
            name=name, integration_name=integration_name, body=tokens, **kwargs
        )

    # Prompt Integration Operations
    async def associate_prompt_with_integration(
        self, ai_prompt: str, integration_provider: str, integration_name: str, **kwargs
    ) -> None:
        """Associate a prompt template with an integration.

        Links a prompt template to an integration so it can be used with AI models.

        Args:
            ai_prompt: Name of the prompt template to associate
            integration_provider: Name of the integration provider
            integration_name: Name of the specific integration API
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await integration_client.associate_prompt_with_integration(
                "customer_service_prompt",
                "my-openai",
                "gpt-4-chat"
            )
            ```
        """
        await self._integration_api.associate_prompt_with_integration(
            integration_provider=integration_provider,
            integration_name=integration_name,
            prompt_name=ai_prompt,
            **kwargs,
        )

    async def get_prompts_with_integration(
        self, integration_provider: str, integration_name: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Get prompts associated with an integration.

        Retrieves all prompt templates that are linked to a specific integration.

        Args:
            integration_provider: Name of the integration provider
            integration_name: Name of the specific integration API
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplateAdapter instances

        Example:
            ```python
            prompts = await integration_client.get_prompts_with_integration(
                "my-openai",
                "gpt-4-chat"
            )
            for prompt in prompts:
                print(f"Prompt: {prompt.name}")
            ```
        """
        return await self._integration_api.get_prompts_with_integration(
            integration_provider=integration_provider, integration_name=integration_name, **kwargs
        )

    # Event and Statistics Operations
    async def record_event_stats(
        self, event_type: str, event_log: List[EventLogAdapter], **kwargs
    ) -> None:
        """Record event statistics for integrations.

        Records integration usage events for monitoring and analytics.

        Args:
            event_type: Type of event being recorded
            event_log: List of event log entries to record
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.event_log_adapter import EventLogAdapter

            events = [
                EventLogAdapter(
                    event="api_call",
                    timestamp=1234567890,
                    metadata={"tokens": 1500, "model": "gpt-4"}
                )
            ]
            await integration_client.record_event_stats("usage", events)
            ```
        """
        await self._integration_api.record_event_stats(
            type=event_type, event_log=event_log, **kwargs
        )

    # Utility Methods
    async def get_integration_by_category(
        self, category: str, active_only: bool = True
    ) -> List[IntegrationAdapter]:
        """Get integrations filtered by category.

        Convenience method for retrieving integrations of a specific type.

        Args:
            category: Category to filter by (e.g., "AI_MODEL", "VECTOR_DB")
            active_only: If True, only return active integrations. Defaults to True

        Returns:
            List of IntegrationAdapter instances matching the category

        Example:
            ```python
            # Get all active AI model integrations
            ai_models = await integration_client.get_integration_by_category("AI_MODEL")
            for model in ai_models:
                print(f"Model: {model.name}")
            ```
        """
        return await self.get_all_integrations(category=category, active_only=active_only)

    async def get_active_integrations(self) -> List[IntegrationAdapter]:
        """Get only active integrations.

        Convenience method for retrieving all active integrations regardless of category.

        Returns:
            List of all active IntegrationAdapter instances

        Example:
            ```python
            active = await integration_client.get_active_integrations()
            print(f"Found {len(active)} active integrations")
            ```
        """
        return await self.get_all_integrations(active_only=True)

    async def get_integration_provider_by_category(
        self, category: str, active_only: bool = True, **kwargs
    ) -> List[IntegrationAdapter]:
        """Get integration providers filtered by category.

        Convenience method for retrieving integration providers of a specific type.

        Args:
            category: Category to filter by (e.g., "AI_MODEL", "VECTOR_DB")
            active_only: If True, only return active providers. Defaults to True
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of IntegrationAdapter instances matching the category

        Example:
            ```python
            # Get all active vector database providers
            vector_dbs = await integration_client.get_integration_provider_by_category("VECTOR_DB")
            ```
        """
        return await self.get_integration_providers(
            category=category, active_only=active_only, **kwargs
        )

    async def get_active_integration_providers(self, **kwargs) -> List[IntegrationAdapter]:
        """Get only active integration providers.

        Convenience method for retrieving all active integration providers.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of all active IntegrationAdapter provider instances

        Example:
            ```python
            providers = await integration_client.get_active_integration_providers()
            for provider in providers:
                print(f"Provider: {provider.name}, Type: {provider.type}")
            ```
        """
        return await self.get_integration_providers(active_only=True, **kwargs)

    async def get_integrations(self, **kwargs) -> List[IntegrationAdapter]:
        """Get all integrations.

        Convenience method that retrieves all integration providers.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of all IntegrationAdapter instances

        Example:
            ```python
            all_integrations = await integration_client.get_integrations()
            print(f"Total integrations: {len(all_integrations)}")
            ```
        """
        return await self._integration_api.get_integration_providers(**kwargs)
