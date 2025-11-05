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
        """Initialize the OrkesSecretClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            secret_client = OrkesSecretClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # Core Secret Operations
    @deprecated("put_secret is deprecated; use put_secret_validated instead")
    @typing_deprecated("put_secret is deprecated; use put_secret_validated instead")
    async def put_secret(self, key: str, secret: str) -> object:
        """Store a secret value by key.

        .. deprecated::
            Use put_secret_validated instead for type-safe validated responses.

        Args:
            key: Unique key for the secret
            secret: Secret value to store

        Returns:
            Raw response object from the API

        Example:
            ```python
            await secret_client.put_secret("db_password", "mysecretpassword123")
            ```
        """
        return await self._secret_api.put_secret(key, secret)

    async def put_secret_validated(self, key: str, secret: str, **kwargs) -> None:
        """Store a secret value by key.

        Args:
            key: Unique key for the secret
            secret: Secret value to store
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Store database credentials
            await secret_client.put_secret_validated("db_password", "mysecretpassword123")

            # Store API keys
            await secret_client.put_secret_validated("openai_api_key", "sk-...")
            ```
        """
        await self._secret_api.put_secret(key=key, body=secret, **kwargs)

    async def get_secret(self, key: str, **kwargs) -> str:
        """Get a secret value by key.

        Args:
            key: Key of the secret to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Secret value as string

        Example:
            ```python
            password = await secret_client.get_secret("db_password")
            # Use password in workflow tasks
            ```
        """
        return await self._secret_api.get_secret(key=key, **kwargs)

    @deprecated("delete_secret is deprecated; use delete_secret_validated instead")
    @typing_deprecated("delete_secret is deprecated; use delete_secret_validated instead")
    async def delete_secret(self, key: str) -> object:
        """Delete a secret by key.

        .. deprecated::
            Use delete_secret_validated instead for type-safe validated responses.

        Args:
            key: Key of the secret to delete

        Returns:
            Raw response object from the API

        Example:
            ```python
            await secret_client.delete_secret("old_api_key")
            ```
        """
        return await self._secret_api.delete_secret(key)

    async def delete_secret_validated(self, key: str, **kwargs) -> None:
        """Delete a secret by key.

        Args:
            key: Key of the secret to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await secret_client.delete_secret_validated("old_api_key")
            ```
        """
        await self._secret_api.delete_secret(key=key, **kwargs)

    @deprecated("secret_exists is deprecated; use secret_exists_validated instead")
    @typing_deprecated("secret_exists is deprecated; use secret_exists_validated instead")
    async def secret_exists(self, key: str) -> object:
        """Check if a secret exists by key.

        .. deprecated::
            Use secret_exists_validated instead for type-safe validated responses.

        Args:
            key: Key of the secret to check

        Returns:
            Raw response object from the API

        Example:
            ```python
            await secret_client.secret_exists("db_password")
            ```
        """
        return await self._secret_api.secret_exists(key)

    async def secret_exists_validated(self, key: str, **kwargs) -> bool:
        """Check if a secret exists by key.

        Args:
            key: Key of the secret to check
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            True if secret exists, False otherwise

        Example:
            ```python
            if await secret_client.secret_exists_validated("db_password"):
                print("Secret exists")
            else:
                print("Secret not found")
            ```
        """
        result = await self._secret_api.secret_exists(key=key, **kwargs)
        return bool(result)

    # Secret Listing Operations
    async def list_all_secret_names(self, **kwargs) -> List[str]:
        """List all secret names (keys).

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of secret key names

        Example:
            ```python
            secrets = await secret_client.list_all_secret_names()
            for secret_key in secrets:
                print(f"Secret: {secret_key}")
            ```
        """
        return await self._secret_api.list_all_secret_names(**kwargs)

    async def list_secrets_that_user_can_grant_access_to(self, **kwargs) -> List[str]:
        """List secrets that the current user can grant access to.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of secret keys the user can grant access to

        Example:
            ```python
            grantable = await secret_client.list_secrets_that_user_can_grant_access_to()
            print(f"You can grant access to {len(grantable)} secrets")
            ```
        """
        return await self._secret_api.list_secrets_that_user_can_grant_access_to(**kwargs)

    async def list_secrets_with_tags_that_user_can_grant_access_to(
        self, **kwargs
    ) -> List[ExtendedSecretAdapter]:
        """List secrets with tags that the current user can grant access to.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ExtendedSecretAdapter instances with tag information

        Example:
            ```python
            secrets = await secret_client.list_secrets_with_tags_that_user_can_grant_access_to()
            for secret in secrets:
                print(f"Secret: {secret.key}, Tags: {secret.tags}")
            ```
        """
        return await self._secret_api.list_secrets_with_tags_that_user_can_grant_access_to(**kwargs)

    # Tag Management Operations
    async def put_tag_for_secret(self, key: str, tags: List[TagAdapter], **kwargs) -> None:
        """Add tags to a secret.

        Args:
            key: Key of the secret
            tags: List of tags to add
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [
                TagAdapter(key="environment", value="production"),
                TagAdapter(key="team", value="platform")
            ]
            await secret_client.put_tag_for_secret("db_password", tags)
            ```
        """
        await self._secret_api.put_tag_for_secret(key=key, tag=tags, **kwargs)

    async def get_tags(self, key: str, **kwargs) -> List[TagAdapter]:
        """Get tags for a secret.

        Args:
            key: Key of the secret
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await secret_client.get_tags("db_password")
            for tag in tags:
                print(f"{tag.key}: {tag.value}")
            ```
        """
        return await self._secret_api.get_tags(key=key, **kwargs)

    async def delete_tag_for_secret(self, key: str, tags: List[TagAdapter], **kwargs) -> None:
        """Remove tags from a secret.

        Args:
            key: Key of the secret
            tags: List of tags to remove
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="environment", value="production")]
            await secret_client.delete_tag_for_secret("db_password", tags)
            ```
        """
        await self._secret_api.delete_tag_for_secret(key=key, tag=tags, **kwargs)

    # Cache Operations
    @deprecated("clear_local_cache is deprecated; use clear_local_cache_validated instead")
    @typing_deprecated("clear_local_cache is deprecated; use clear_local_cache_validated instead")
    async def clear_local_cache(self) -> Dict[str, str]:
        """Clear local secret cache.

        .. deprecated::
            Use clear_local_cache_validated instead for type-safe validated responses.

        Returns:
            Dictionary with cache clear results

        Example:
            ```python
            await secret_client.clear_local_cache()
            ```
        """
        return await self._secret_api.clear_local_cache()

    async def clear_local_cache_validated(self, **kwargs) -> None:
        """Clear local secret cache.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Clear cache after updating secrets
            await secret_client.clear_local_cache_validated()
            ```
        """
        await self._secret_api.clear_local_cache(**kwargs)

    @deprecated("clear_redis_cache is deprecated; use clear_redis_cache_validated instead")
    @typing_deprecated("clear_redis_cache is deprecated; use clear_redis_cache_validated instead")
    async def clear_redis_cache(self) -> Dict[str, str]:
        """Clear Redis secret cache.

        .. deprecated::
            Use clear_redis_cache_validated instead for type-safe validated responses.

        Returns:
            Dictionary with cache clear results

        Example:
            ```python
            await secret_client.clear_redis_cache()
            ```
        """
        return await self._secret_api.clear_redis_cache()

    async def clear_redis_cache_validated(self, **kwargs) -> None:
        """Clear Redis secret cache.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Clear Redis cache after updating secrets
            await secret_client.clear_redis_cache_validated()
            ```
        """
        await self._secret_api.clear_redis_cache(**kwargs)

    # Convenience Methods
    async def list_secrets(self, **kwargs) -> List[str]:
        """List all secret names (alias for list_all_secret_names).

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of secret key names

        Example:
            ```python
            secrets = await secret_client.list_secrets()
            ```
        """
        return await self.list_all_secret_names(**kwargs)

    @deprecated("update_secret is deprecated; use update_secret_validated instead")
    @typing_deprecated("update_secret is deprecated; use update_secret_validated instead")
    async def update_secret(self, key: str, secret: str) -> object:
        """Update a secret value (alias for put_secret).

        .. deprecated::
            Use update_secret_validated instead for type-safe validated responses.

        Args:
            key: Key of the secret to update
            secret: New secret value

        Returns:
            Raw response object from the API

        Example:
            ```python
            await secret_client.update_secret("api_key", "new_value")
            ```
        """
        return await self.put_secret(key, secret)

    async def update_secret_validated(self, key: str, secret: str, **kwargs) -> None:
        """Update a secret value (alias for put_secret_validated).

        Args:
            key: Key of the secret to update
            secret: New secret value
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await secret_client.update_secret_validated("api_key", "new_value")
            ```
        """
        await self.put_secret_validated(key=key, secret=secret, **kwargs)

    @deprecated("has_secret is deprecated; use has_secret_validated instead")
    @typing_deprecated("has_secret is deprecated; use has_secret_validated instead")
    async def has_secret(self, key: str) -> object:
        """Check if a secret exists (alias for secret_exists).

        .. deprecated::
            Use has_secret_validated instead for type-safe validated responses.

        Args:
            key: Key of the secret to check

        Returns:
            Raw response object from the API

        Example:
            ```python
            await secret_client.has_secret("db_password")
            ```
        """
        return await self.secret_exists(key)

    async def has_secret_validated(self, key: str, **kwargs) -> bool:
        """Check if a secret exists (alias for secret_exists_validated).

        Args:
            key: Key of the secret to check
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            True if secret exists, False otherwise

        Example:
            ```python
            if await secret_client.has_secret_validated("db_password"):
                print("Password is configured")
            ```
        """
        return await self.secret_exists_validated(key=key, **kwargs)
