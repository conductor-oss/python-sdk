from conductor.client.codegen.api.secret_resource_api import SecretResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from typing import Dict, List
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.extended_secret import ExtendedSecret


class SecretResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = SecretResourceApi(api_client)

    def clear_local_cache(self, **kwargs) -> Dict[str, str]:
        """Clear local cache"""
        return self._api.clear_local_cache(**kwargs)

    def clear_redis_cache(self, **kwargs) -> Dict[str, str]:
        """Clear redis cache"""
        return self._api.clear_redis_cache(**kwargs)

    def delete_secret(self, key: str, **kwargs) -> object:
        """Delete a secret"""
        return self._api.delete_secret(key, **kwargs)

    def delete_tag_for_secret(self, body: List[Tag], key: str, **kwargs) -> None:
        """Delete a tag for a secret"""
        return self._api.delete_tag_for_secret(body, key, **kwargs)

    def get_secret(self, key: str, **kwargs) -> str:
        """Get a secret"""
        return self._api.get_secret(key, **kwargs)

    def get_tags(self, key: str, **kwargs) -> List[Tag]:
        """Get tags for a secret"""
        return self._api.get_tags(key, **kwargs)

    def list_all_secret_names(self, **kwargs) -> List[str]:
        """List all secret names"""
        return self._api.list_all_secret_names(**kwargs)

    def list_secrets_that_user_can_grant_access_to(self, **kwargs) -> List[str]:
        """List secrets that user can grant access to"""
        return self._api.list_secrets_that_user_can_grant_access_to(**kwargs)

    def list_secrets_with_tags_that_user_can_grant_access_to(
        self, **kwargs
    ) -> List[ExtendedSecret]:
        """List secrets with tags that user can grant access to"""
        return self._api.list_secrets_with_tags_that_user_can_grant_access_to(**kwargs)

    def put_secret(self, body: str, key: str, **kwargs) -> object:
        """Put a secret"""
        return self._api.put_secret(body, key, **kwargs)

    def put_tag_for_secret(self, body: List[Tag], key: str, **kwargs) -> None:
        """Put a tag for a secret"""
        return self._api.put_tag_for_secret(body, key, **kwargs)

    def secret_exists(self, key: str, **kwargs) -> object:
        """Check if a secret exists"""
        return self._api.secret_exists(key, **kwargs)
