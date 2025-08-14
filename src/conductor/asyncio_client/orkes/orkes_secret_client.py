from __future__ import annotations

from typing import Dict, List

from conductor.asyncio_client.adapters.models.extended_secret_adapter import \
    ExtendedSecretAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.http.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesSecretClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Core Secret Operations
    async def put_secret(self, key: str, secret: str) -> object:
        """Store a secret value by key"""
        return await self.secret_api.put_secret(key, secret)

    async def get_secret(self, key: str) -> str:
        """Get a secret value by key"""
        return await self.secret_api.get_secret(key)

    async def delete_secret(self, key: str) -> object:
        """Delete a secret by key"""
        return await self.secret_api.delete_secret(key)

    async def secret_exists(self, key: str) -> bool:
        """Check if a secret exists by key"""
        return await self.secret_api.secret_exists(key)

    # Secret Listing Operations
    async def list_all_secret_names(self) -> List[str]:
        """List all secret names (keys)"""
        return await self.secret_api.list_all_secret_names()

    async def list_secrets_that_user_can_grant_access_to(self) -> List[str]:
        """List secrets that the current user can grant access to"""
        return await self.secret_api.list_secrets_that_user_can_grant_access_to()

    async def list_secrets_with_tags_that_user_can_grant_access_to(
        self,
    ) -> List[ExtendedSecretAdapter]:
        """List secrets with tags that the current user can grant access to"""
        return (
            await self.secret_api.list_secrets_with_tags_that_user_can_grant_access_to()
        )

    # Tag Management Operations
    async def put_tag_for_secret(self, key: str, tags: List[TagAdapter]) -> None:
        """Add tags to a secret"""
        await self.secret_api.put_tag_for_secret(key, tags)

    async def get_tags(self, key: str) -> List[TagAdapter]:
        """Get tags for a secret"""
        return await self.secret_api.get_tags(key)

    async def delete_tag_for_secret(self, key: str, tags: List[TagAdapter]) -> None:
        """Remove tags from a secret"""
        await self.secret_api.delete_tag_for_secret(key, tags)

    # Cache Operations
    async def clear_local_cache(self) -> Dict[str, str]:
        """Clear local cache"""
        return await self.secret_api.clear_local_cache()

    async def clear_redis_cache(self) -> Dict[str, str]:
        """Clear Redis cache"""
        return await self.secret_api.clear_redis_cache()

    # Convenience Methods
    async def list_secrets(self) -> List[str]:
        """Alias for list_all_secret_names for backward compatibility"""
        return await self.list_all_secret_names()

    async def update_secret(self, key: str, secret: str) -> object:
        """Alias for put_secret for consistency with other clients"""
        return await self.put_secret(key, secret)

    async def has_secret(self, key: str) -> bool:
        """Alias for secret_exists for consistency"""
        return await self.secret_exists(key)
