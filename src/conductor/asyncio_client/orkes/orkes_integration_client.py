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
        super().__init__(configuration, api_client)

    # Integration Provider Operations
    async def save_integration_provider(
        self, name: str, integration_update: IntegrationUpdateAdapter, **kwargs
    ) -> None:
        """Create or update an integration provider"""
        await self._integration_api.save_integration_provider(
            name=name, integration_update=integration_update, **kwargs
        )

    async def save_integration(
        self, integration_name, integration_details: IntegrationUpdateAdapter, **kwargs
    ) -> None:
        await self._integration_api.save_integration_provider(
            name=integration_name, integration_update=integration_details, **kwargs
        )

    async def get_integration_provider(self, name: str, **kwargs) -> IntegrationAdapter:
        """Get integration provider by name"""
        return await self._integration_api.get_integration_provider(name=name, **kwargs)

    async def get_integration(
        self, integration_name: str, **kwargs
    ) -> Optional[IntegrationAdapter]:
        try:
            return await self.get_integration_provider(name=integration_name, **kwargs)
        except NotFoundException:
            return None

    async def delete_integration_provider(self, name: str, **kwargs) -> None:
        """Delete an integration provider"""
        await self._integration_api.delete_integration_provider(name=name, **kwargs)

    async def get_integration_providers(
        self, category: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[IntegrationAdapter]:
        """Get all integration providers"""
        return await self._integration_api.get_integration_providers(
            category=category, active_only=active_only, **kwargs
        )

    async def get_integration_provider_defs(self, **kwargs) -> List[IntegrationDefAdapter]:
        """Get integration provider definitions"""
        return await self._integration_api.get_integration_provider_defs(**kwargs)

    # Integration API Operations
    async def save_integration_api(
        self,
        name: str,
        integration_name: str,
        integration_api_update: IntegrationApiUpdateAdapter,
        **kwargs,
    ) -> None:
        """Create or update an integration API"""
        await self._integration_api.save_integration_api(
            name=name,
            integration_name=integration_name,
            integration_api_update=integration_api_update,
            **kwargs,
        )

    async def get_integration_api(
        self, name: str, integration_name: str, **kwargs
    ) -> IntegrationApiAdapter:
        """Get integration API by name and integration name"""
        return await self._integration_api.get_integration_api(
            name=name, integration_name=integration_name, **kwargs
        )

    async def delete_integration_api(self, name: str, integration_name: str, **kwargs) -> None:
        """Delete an integration API"""
        await self._integration_api.delete_integration_api(
            name=name, integration_name=integration_name, **kwargs
        )

    async def get_integration_apis(
        self, integration_name: str, **kwargs
    ) -> List[IntegrationApiAdapter]:
        """Get all APIs for a specific integration"""
        return await self._integration_api.get_integration_apis(name=integration_name, **kwargs)

    async def get_integration_available_apis(self, name: str, **kwargs) -> List[str]:
        """Get available APIs for an integration"""
        return await self._integration_api.get_integration_available_apis(name=name, **kwargs)

    # Integration Operations
    async def save_all_integrations(self, request_body: List[IntegrationAdapter], **kwargs) -> None:
        """Save all integrations"""
        await self._integration_api.save_all_integrations(integration=request_body, **kwargs)

    async def get_all_integrations(
        self, category: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[IntegrationAdapter]:
        """Get all integrations with optional filtering"""
        return await self._integration_api.get_all_integrations(
            category=category, active_only=active_only, **kwargs
        )

    async def get_providers_and_integrations(
        self, integration_type: Optional[str] = None, active_only: Optional[bool] = None, **kwargs
    ) -> List[str]:
        """Get providers and integrations together"""
        return await self._integration_api.get_providers_and_integrations(
            type=integration_type, active_only=active_only, **kwargs
        )

    # Tag Management Operations
    async def put_tag_for_integration(
        self, tags: List[TagAdapter], name: str, integration_name: str, **kwargs
    ) -> None:
        """Add tags to an integration"""
        await self._integration_api.put_tag_for_integration(
            name=name, integration_name=integration_name, tag=tags, **kwargs
        )

    async def get_tags_for_integration(
        self, name: str, integration_name: str, **kwargs
    ) -> List[TagAdapter]:
        """Get tags for an integration"""
        return await self._integration_api.get_tags_for_integration(
            name=name, integration_name=integration_name, **kwargs
        )

    async def delete_tag_for_integration(
        self, tags: List[TagAdapter], name: str, integration_name: str, **kwargs
    ) -> None:
        """Delete tags from an integration"""
        await self._integration_api.delete_tag_for_integration(
            name=name, integration_name=integration_name, tag=tags, **kwargs
        )

    async def put_tag_for_integration_provider(
        self, body: List[TagAdapter], name: str, **kwargs
    ) -> None:
        """Add tags to an integration provider"""
        await self._integration_api.put_tag_for_integration_provider(name=name, tag=body, **kwargs)

    async def get_tags_for_integration_provider(self, name: str, **kwargs) -> List[TagAdapter]:
        """Get tags for an integration provider"""
        return await self._integration_api.get_tags_for_integration_provider(name=name, **kwargs)

    async def delete_tag_for_integration_provider(
        self, body: List[TagAdapter], name: str, **kwargs
    ) -> None:
        """Delete tags from an integration provider"""
        await self._integration_api.delete_tag_for_integration_provider(
            name=name, tag=body, **kwargs
        )

    # Token Usage Operations
    async def get_token_usage_for_integration(
        self, name: str, integration_name: str, **kwargs
    ) -> int:
        """Get token usage for a specific integration"""
        return await self._integration_api.get_token_usage_for_integration(
            name=name, integration_name=integration_name, **kwargs
        )

    async def get_token_usage_for_integration_provider(self, name: str, **kwargs) -> Dict[str, str]:
        """Get token usage for an integration provider"""
        return await self._integration_api.get_token_usage_for_integration_provider(
            name=name, **kwargs
        )

    async def register_token_usage(
        self, name: str, integration_name: str, tokens: int, **kwargs
    ) -> None:
        """Register token usage for an integration"""
        await self._integration_api.register_token_usage(
            name=name, integration_name=integration_name, body=tokens, **kwargs
        )

    # Prompt Integration Operations
    async def associate_prompt_with_integration(
        self, ai_prompt: str, integration_provider: str, integration_name: str, **kwargs
    ) -> None:
        """Associate a prompt with an integration"""
        await self._integration_api.associate_prompt_with_integration(
            integration_provider=integration_provider,
            integration_name=integration_name,
            prompt_name=ai_prompt,
            **kwargs,
        )

    async def get_prompts_with_integration(
        self, integration_provider: str, integration_name: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Get prompts associated with an integration"""
        return await self._integration_api.get_prompts_with_integration(
            integration_provider=integration_provider, integration_name=integration_name, **kwargs
        )

    # Event and Statistics Operations
    async def record_event_stats(
        self, event_type: str, event_log: List[EventLogAdapter], **kwargs
    ) -> None:
        """Record event statistics"""
        await self._integration_api.record_event_stats(
            type=event_type, event_log=event_log, **kwargs
        )

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
        self, category: str, active_only: bool = True, **kwargs
    ) -> List[IntegrationAdapter]:
        """Get integration providers filtered by category"""
        return await self.get_integration_providers(
            category=category, active_only=active_only, **kwargs
        )

    async def get_active_integration_providers(self, **kwargs) -> List[IntegrationAdapter]:
        """Get only active integration providers"""
        return await self.get_integration_providers(active_only=True, **kwargs)

    async def get_integrations(self, **kwargs) -> List[IntegrationAdapter]:
        return await self._integration_api.get_integration_providers(**kwargs)
