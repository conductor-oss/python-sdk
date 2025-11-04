from __future__ import annotations

from typing import Dict, List

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.extended_secret_adapter import ExtendedSecretAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesSecretClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Core Secret Operations
    @deprecated("put_secret is deprecated; use put_secret_validated instead")
    @typing_deprecated("put_secret is deprecated; use put_secret_validated instead")
    async def put_secret(self, key: str, secret: str) -> object:
        """Store a secret value by key"""
        return await self._secret_api.put_secret(key, secret)

    async def put_secret_validated(self, key: str, secret: str, **kwargs) -> None:
        """Store a secret value by key"""
        await self._secret_api.put_secret(key=key, body=secret, **kwargs)

    async def get_secret(self, key: str, **kwargs) -> str:
        """Get a secret value by key"""
        return await self._secret_api.get_secret(key=key, **kwargs)

    @deprecated("delete_secret is deprecated; use delete_secret_validated instead")
    @typing_deprecated("delete_secret is deprecated; use delete_secret_validated instead")
    async def delete_secret(self, key: str) -> object:
        """Delete a secret by key"""
        return await self._secret_api.delete_secret(key)

    async def delete_secret_validated(self, key: str, **kwargs) -> None:
        """Delete a secret by key"""
        await self._secret_api.delete_secret(key=key, **kwargs)

    @deprecated("secret_exists is deprecated; use secret_exists_validated instead")
    @typing_deprecated("secret_exists is deprecated; use secret_exists_validated instead")
    async def secret_exists(self, key: str) -> object:
        """Check if a secret exists by key"""
        return await self._secret_api.secret_exists(key)

    async def secret_exists_validated(self, key: str, **kwargs) -> bool:
        """Check if a secret exists by key"""
        result = await self._secret_api.secret_exists(key=key, **kwargs)
        return bool(result)

    # Secret Listing Operations
    async def list_all_secret_names(self, **kwargs) -> List[str]:
        """List all secret names (keys)"""
        return await self._secret_api.list_all_secret_names(**kwargs)

    async def list_secrets_that_user_can_grant_access_to(self, **kwargs) -> List[str]:
        """List secrets that the current user can grant access to"""
        return await self._secret_api.list_secrets_that_user_can_grant_access_to(**kwargs)

    async def list_secrets_with_tags_that_user_can_grant_access_to(
        self, **kwargs
    ) -> List[ExtendedSecretAdapter]:
        """List secrets with tags that the current user can grant access to"""
        return await self._secret_api.list_secrets_with_tags_that_user_can_grant_access_to(**kwargs)

    # Tag Management Operations
    async def put_tag_for_secret(self, key: str, tags: List[TagAdapter], **kwargs) -> None:
        """Add tags to a secret"""
        await self._secret_api.put_tag_for_secret(key=key, tag=tags, **kwargs)

    async def get_tags(self, key: str, **kwargs) -> List[TagAdapter]:
        """Get tags for a secret"""
        return await self._secret_api.get_tags(key=key, **kwargs)

    async def delete_tag_for_secret(self, key: str, tags: List[TagAdapter], **kwargs) -> None:
        """Remove tags from a secret"""
        await self._secret_api.delete_tag_for_secret(key=key, tag=tags, **kwargs)

    # Cache Operations
    @deprecated("clear_local_cache is deprecated; use clear_local_cache_validated instead")
    @typing_deprecated("clear_local_cache is deprecated; use clear_local_cache_validated instead")
    async def clear_local_cache(self) -> Dict[str, str]:
        """Clear local cache"""
        return await self._secret_api.clear_local_cache()

    async def clear_local_cache_validated(self, **kwargs) -> None:
        """Clear local cache"""
        await self._secret_api.clear_local_cache(**kwargs)

    @deprecated("clear_redis_cache is deprecated; use clear_redis_cache_validated instead")
    @typing_deprecated("clear_redis_cache is deprecated; use clear_redis_cache_validated instead")
    async def clear_redis_cache(self) -> Dict[str, str]:
        """Clear Redis cache"""
        return await self._secret_api.clear_redis_cache()

    async def clear_redis_cache_validated(self, **kwargs) -> None:
        """Clear Redis cache"""
        await self._secret_api.clear_redis_cache(**kwargs)

    # Convenience Methods
    async def list_secrets(self, **kwargs) -> List[str]:
        """Alias for list_all_secret_names for backward compatibility"""
        return await self.list_all_secret_names(**kwargs)

    @deprecated("update_secret is deprecated; use update_secret_validated instead")
    @typing_deprecated("update_secret is deprecated; use update_secret_validated instead")
    async def update_secret(self, key: str, secret: str) -> object:
        """Alias for put_secret for consistency with other clients"""
        return await self.put_secret(key, secret)

    async def update_secret_validated(self, key: str, secret: str, **kwargs) -> None:
        """Alias for put_secret_validated for consistency with other clients"""
        await self.put_secret_validated(key=key, secret=secret, **kwargs)

    @deprecated("has_secret is deprecated; use has_secret_validated instead")
    @typing_deprecated("has_secret is deprecated; use has_secret_validated instead")
    async def has_secret(self, key: str) -> object:
        """Alias for secret_exists for consistency"""
        return await self.secret_exists(key)

    async def has_secret_validated(self, key: str, **kwargs) -> bool:
        """Alias for secret_exists_validated for consistency"""
        return await self.secret_exists_validated(key=key, **kwargs)
