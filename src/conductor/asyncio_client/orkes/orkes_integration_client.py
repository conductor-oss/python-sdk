from __future__ import annotations
from typing import Optional, List, Dict

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters.models.integration_adapter import IntegrationAdapter
from conductor.asyncio_client.adapters.models.integration_api_adapter import IntegrationApiAdapter
from conductor.asyncio_client.adapters.models.integration_api_update_adapter import (
    IntegrationApiUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.integration_def_adapter import IntegrationDefAdapter
from conductor.asyncio_client.adapters.models.integration_update_adapter import (
    IntegrationUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.event_log_adapter import EventLogAdapter
from conductor.asyncio_client.http.exceptions import NotFoundException
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesIntegrationClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Integration Provider Operations
    async def save_integration_provider(
        self, name: str, integration_update: IntegrationUpdateAdapter
    ) -> None:
        """Create or update an integration provider"""
        await self.integration_api.save_integration_provider(name, integration_update)

    async def save_integration(
        self, integration_name, integration_details: IntegrationUpdateAdapter
    ) -> None:
        await self.integration_api.save_integration_provider(integration_name, integration_details)

    async def get_integration_provider(self, name: str) -> IntegrationDefAdapter:
        """Get integration provider by name"""
        return await self.integration_api.get_integration_provider(name)

    async def get_integration(self, integration_name: str) -> IntegrationDefAdapter | None:
        try:
            return await self.get_integration_provider(integration_name)
        except NotFoundException:
            return None

    async def delete_integration_provider(self, name: str) -> None:
        """Delete an integration provider"""
        await self.integration_api.delete_integration_provider(name)

    async def get_integration_providers(
        self, category: Optional[str] = None, active_only: Optional[bool] = None
    ) -> List[IntegrationDefAdapter]:
        """Get all integration providers"""
        return await self.integration_api.get_integration_providers(
            category=category, active_only=active_only
        )

    async def get_integration_provider_defs(self) -> List[IntegrationDefAdapter]:
        """Get integration provider definitions"""
        return await self.integration_api.get_integration_provider_defs()

    # Integration API Operations
    async def save_integration_api(
        self, name: str, integration_name: str, integration_api_update: IntegrationApiUpdateAdapter
    ) -> None:
        """Create or update an integration API"""
        await self.integration_api.save_integration_api(
            name, integration_name, integration_api_update
        )

    async def get_integration_api(self, name: str, integration_name: str) -> IntegrationApiAdapter:
        """Get integration API by name and integration name"""
        return await self.integration_api.get_integration_api(name, integration_name)

    async def delete_integration_api(self, name: str, integration_name: str) -> None:
        """Delete an integration API"""
        await self.integration_api.delete_integration_api(name, integration_name)

    async def get_integration_apis(self, integration_name: str) -> List[IntegrationApiAdapter]:
        """Get all APIs for a specific integration"""
        return await self.integration_api.get_integration_apis(integration_name)

    async def get_integration_available_apis(self, name: str) -> List[IntegrationApiAdapter]:
        """Get available APIs for an integration"""
        return await self.integration_api.get_integration_available_apis(name)

    # Integration Operations
    async def save_all_integrations(self, request_body: List[IntegrationUpdateAdapter]) -> None:
        """Save all integrations"""
        await self.integration_api.save_all_integrations(request_body)

    async def get_all_integrations(
        self, category: Optional[str] = None, active_only: Optional[bool] = None
    ) -> List[IntegrationAdapter]:
        """Get all integrations with optional filtering"""
        return await self.integration_api.get_all_integrations(
            category=category, active_only=active_only
        )

    async def get_providers_and_integrations(
        self, integration_type: Optional[str] = None, active_only: Optional[bool] = None
    ) -> Dict[str, object]:
        """Get providers and integrations together"""
        return await self.integration_api.get_providers_and_integrations(
            type=integration_type, active_only=active_only
        )

    # Tag Management Operations
    async def put_tag_for_integration(
        self, tags: List[TagAdapter], name: str, integration_name: str
    ) -> None:
        """Add tags to an integration"""
        await self.integration_api.put_tag_for_integration(
            name=name, integration_name=integration_name, tag=tags
        )

    async def get_tags_for_integration(self, name: str, integration_name: str) -> List[TagAdapter]:
        """Get tags for an integration"""
        return await self.integration_api.get_tags_for_integration(
            name=name, integration_name=integration_name
        )

    async def delete_tag_for_integration(
        self, tags: List[TagAdapter], name: str, integration_name: str
    ) -> None:
        """Delete tags from an integration"""
        await self.integration_api.delete_tag_for_integration(
            name=name, integration_name=integration_name, tag=tags
        )

    async def put_tag_for_integration_provider(self, body: List[TagAdapter], name: str) -> None:
        """Add tags to an integration provider"""
        await self.integration_api.put_tag_for_integration_provider(name, body)

    async def get_tags_for_integration_provider(self, name: str) -> List[TagAdapter]:
        """Get tags for an integration provider"""
        return await self.integration_api.get_tags_for_integration_provider(name)

    async def delete_tag_for_integration_provider(self, body: List[TagAdapter], name: str) -> None:
        """Delete tags from an integration provider"""
        await self.integration_api.delete_tag_for_integration_provider(name, body)

    # Token Usage Operations
    async def get_token_usage_for_integration(self, name: str, integration_name: str) -> int:
        """Get token usage for a specific integration"""
        return await self.integration_api.get_token_usage_for_integration(name, integration_name)

    async def get_token_usage_for_integration_provider(self, name: str) -> int:
        """Get token usage for an integration provider"""
        return await self.integration_api.get_token_usage_for_integration_provider(name)

    async def register_token_usage(self, name: str, integration_name: str, tokens: int) -> None:
        """Register token usage for an integration"""
        await self.integration_api.register_token_usage(name, integration_name, tokens)

    # Prompt Integration Operations
    async def associate_prompt_with_integration(
        self, ai_prompt: str, integration_provider: str, integration_name: str
    ) -> None:
        """Associate a prompt with an integration"""
        await self.integration_api.associate_prompt_with_integration(
            ai_prompt, integration_provider, integration_name
        )

    async def get_prompts_with_integration(
        self, integration_provider: str, integration_name: str
    ) -> List[str]:
        """Get prompts associated with an integration"""
        return await self.integration_api.get_prompts_with_integration(
            integration_provider, integration_name
        )

    # Event and Statistics Operations
    async def record_event_stats(self, event_type: str, event_log: List[EventLogAdapter]) -> None:
        """Record event statistics"""
        await self.integration_api.record_event_stats(type=event_type, event_log=event_log)

    # Utility Methods
    async def get_integration_by_category(
        self, category: str, active_only: bool = True
    ) -> List[IntegrationAdapter]:
        """Get integrations filtered by category"""
        return await self.get_all_integrations(category=category, active_only=active_only)

    async def get_active_integrations(self) -> List[IntegrationAdapter]:
        """Get only active integrations"""
        return await self.get_all_integrations(active_only=True)

    async def get_integration_provider_by_category(
        self, category: str, active_only: bool = True
    ) -> List[IntegrationDefAdapter]:
        """Get integration providers filtered by category"""
        return await self.get_integration_providers(category=category, active_only=active_only)

    async def get_active_integration_providers(self) -> List[IntegrationDefAdapter]:
        """Get only active integration providers"""
        return await self.get_integration_providers(active_only=True)
