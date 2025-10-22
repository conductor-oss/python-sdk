from typing import List, Dict

from conductor.asyncio_client.http.api import IntegrationResourceApi
from conductor.asyncio_client.adapters.models.integration_adapter import IntegrationAdapter
from conductor.asyncio_client.adapters.models.integration_api_adapter import IntegrationApiAdapter
from conductor.asyncio_client.adapters.models.integration_def_adapter import IntegrationDefAdapter
from conductor.asyncio_client.adapters.models.integration_update_adapter import (
    IntegrationUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.event_log_adapter import EventLogAdapter


class IntegrationResourceApiAdapter(IntegrationResourceApi):
    async def get_integration_provider(self, *args, **kwargs) -> IntegrationDefAdapter:
        return await super().get_integration_provider(*args, **kwargs)

    async def get_integration_providers(self, *args, **kwargs) -> List[IntegrationDefAdapter]:
        return await super().get_integration_providers(*args, **kwargs)

    async def get_integration_provider_defs(self, *args, **kwargs) -> List[IntegrationDefAdapter]:
        return await super().get_integration_provider_defs(*args, **kwargs)

    async def get_integration_api(self, *args, **kwargs) -> IntegrationApiAdapter:
        return await super().get_integration_api(*args, **kwargs)

    async def get_integration_apis(self, *args, **kwargs) -> List[IntegrationApiAdapter]:
        return await super().get_integration_apis(*args, **kwargs)

    async def get_integration_available_apis(self, *args, **kwargs) -> List[IntegrationApiAdapter]:
        return await super().get_integration_available_apis(*args, **kwargs)

    async def save_all_integrations(
        self, request_body: List[IntegrationUpdateAdapter], *args, **kwargs
    ) -> None:
        return await super().save_all_integrations(request_body, *args, **kwargs)

    async def get_all_integrations(self, *args, **kwargs) -> List[IntegrationAdapter]:
        return await super().get_all_integrations(*args, **kwargs)

    async def get_providers_and_integrations(self, *args, **kwargs) -> Dict[str, object]:
        return await super().get_providers_and_integrations(*args, **kwargs)

    async def put_tag_for_integration(
        self, name, integration_name, tag: List[TagAdapter], *args, **kwargs
    ) -> None:
        return await super().put_tag_for_integration(name, integration_name, tag, *args, **kwargs)

    async def get_tags_for_integration(self, *args, **kwargs) -> List[TagAdapter]:
        return await super().get_tags_for_integration(*args, **kwargs)

    async def delete_tag_for_integration(
        self, name, integration_name, tag: List[TagAdapter], *args, **kwargs
    ) -> None:
        return await super().delete_tag_for_integration(
            name, integration_name, tag, *args, **kwargs
        )

    async def put_tag_for_integration_provider(
        self, name, tag: List[TagAdapter], *args, **kwargs
    ) -> None:
        return await super().put_tag_for_integration_provider(name, tag, *args, **kwargs)

    async def get_tags_for_integration_provider(self, *args, **kwargs) -> List[TagAdapter]:
        return await super().get_tags_for_integration_provider(*args, **kwargs)

    async def delete_tag_for_integration_provider(
        self, name, tag: List[TagAdapter], *args, **kwargs
    ) -> None:
        return await super().delete_tag_for_integration_provider(name, tag, *args, **kwargs)

    async def get_token_usage_for_integration_provider(self, *args, **kwargs) -> int:
        return await super().get_token_usage_for_integration_provider(*args, **kwargs)

    async def get_prompts_with_integration(self, *args, **kwargs) -> List[str]:
        return await super().get_prompts_with_integration(*args, **kwargs)

    async def record_event_stats(
        self, type, event_log: List[EventLogAdapter], *args, **kwargs
    ) -> None:
        return await super().record_event_stats(type, event_log, *args, **kwargs)
