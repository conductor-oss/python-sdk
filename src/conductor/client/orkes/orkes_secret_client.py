from typing import List, Set

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.extended_secret import ExtendedSecret
from conductor.client.http.models.tag import Tag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.secret_client import SecretClient


class OrkesSecretClient(OrkesBaseClient, SecretClient):
    def __init__(self, configuration: Configuration):
        """Initialize the OrkesSecretClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            secret_client = OrkesSecretClient(config)
            ```
        """
        super().__init__(configuration)

    def put_secret(self, key: str, value: str, **kwargs) -> None:
        """Store a secret value by key.

        Args:
            key: Unique key for the secret
            value: Secret value to store
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Store database credentials
            secret_client.put_secret("db_password", "mysecretpassword123")

            # Store API keys
            secret_client.put_secret("openai_api_key", "sk-...")
            ```
        """
        self._secret_api.put_secret(body=value, key=key, **kwargs)

    def get_secret(self, key: str, **kwargs) -> str:
        """Get a secret value by key.

        Args:
            key: Unique key for the secret
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            The secret value

        Example:
            ```python
            password = secret_client.get_secret("db_password")
            # Use password in workflow
            ```
        """
        return self._secret_api.get_secret(key=key, **kwargs)

    @deprecated("list_all_secret_names is deprecated; use list_all_secret_names_validated instead")
    @typing_deprecated(
        "list_all_secret_names is deprecated; use list_all_secret_names_validated instead"
    )
    def list_all_secret_names(self) -> Set[str]:
        """List all secret names.

        .. deprecated::
            Use list_all_secret_names_validated() instead.

        Returns:
            Set of secret names
        """
        return set(self._secret_api.list_all_secret_names())

    def list_all_secret_names_validated(self, **kwargs) -> List[str]:
        """List all secret names.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of secret names

        Example:
            ```python
            names = secret_client.list_all_secret_names_validated()
            for name in names:
                print(f"Secret: {name}")
            ```
        """
        return self._secret_api.list_all_secret_names(**kwargs)

    def list_secrets_that_user_can_grant_access_to(self, **kwargs) -> List[str]:
        """List secrets that the current user can grant access to.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of secret names

        Example:
            ```python
            grantable_secrets = secret_client.list_secrets_that_user_can_grant_access_to()
            print(f"Can grant access to {len(grantable_secrets)} secrets")
            ```
        """
        return self._secret_api.list_secrets_that_user_can_grant_access_to(**kwargs)

    def delete_secret(self, key: str, **kwargs) -> None:
        """Delete a secret by key.

        Args:
            key: Unique key for the secret to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            secret_client.delete_secret("old_api_key")
            ```
        """
        self._secret_api.delete_secret(key=key, **kwargs)

    def secret_exists(self, key: str, **kwargs) -> object:  # type: ignore[override]
        """Check if a secret exists by key.

        Args:
            key: Unique key for the secret
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Object indicating if secret exists

        Example:
            ```python
            if secret_client.secret_exists("db_password"):
                print("Secret exists")
            ```
        """
        return self._secret_api.secret_exists(key=key, **kwargs)

    def set_secret_tags(self, tags: List[Tag], key: str, **kwargs) -> None:
        """Set tags for a secret.

        Args:
            tags: List of tags to set
            key: Unique key for the secret
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags = [
                Tag(key="environment", value="production"),
                Tag(key="type", value="database")
            ]
            secret_client.set_secret_tags(tags, "db_password")
            ```
        """
        self._secret_api.put_tag_for_secret(body=tags, key=key, **kwargs)

    def get_secret_tags(self, key: str, **kwargs) -> List[Tag]:
        """Get tags for a secret.

        Args:
            key: Unique key for the secret
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Tag instances

        Example:
            ```python
            tags = secret_client.get_secret_tags("db_password")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        return self._secret_api.get_tags(key=key, **kwargs)

    def delete_secret_tags(self, tags: List[Tag], key: str, **kwargs) -> None:
        """Delete tags for a secret.

        Args:
            tags: List of tags to delete
            key: Unique key for the secret
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags_to_delete = [Tag(key="environment", value="staging")]
            secret_client.delete_secret_tags(tags_to_delete, "db_password")
            ```
        """
        self._secret_api.delete_tag_for_secret(body=tags, key=key, **kwargs)

    def clear_local_cache(self, **kwargs) -> None:
        """Clear the local secret cache.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            secret_client.clear_local_cache()
            ```
        """
        self._secret_api.clear_local_cache(**kwargs)

    def clear_redis_cache(self, **kwargs) -> None:
        """Clear the Redis secret cache.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            secret_client.clear_redis_cache()
            ```
        """
        self._secret_api.clear_redis_cache(**kwargs)

    def list_secrets_with_tags_that_user_can_grant_access_to(
        self, **kwargs
    ) -> List[ExtendedSecret]:
        """List secrets with tags that the current user can grant access to.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ExtendedSecret instances with tag information

        Example:
            ```python
            secrets = secret_client.list_secrets_with_tags_that_user_can_grant_access_to()
            for secret in secrets:
                print(f"Secret: {secret.key}, Tags: {secret.tags}")
            ```
        """
        return self._secret_api.list_secrets_with_tags_that_user_can_grant_access_to(**kwargs)
