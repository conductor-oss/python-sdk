from typing import List

from conductor.client.codegen.api.environment_resource_api import EnvironmentResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.environment_variable import EnvironmentVariable
from conductor.client.http.models.tag import Tag


class EnvironmentResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = EnvironmentResourceApi(api_client)

    def create_or_update_env_variable(self, body: str, key: str, **kwargs) -> None:
        """Create or update an environment variable"""
        return self._api.create_or_update_env_variable(body, key, **kwargs)

    def delete_env_variable(self, key: str, **kwargs) -> str:
        """Delete an environment variable"""
        return self._api.delete_env_variable(key, **kwargs)

    def delete_tag_for_env_var(self, body: List[Tag], name: str, **kwargs) -> None:
        """Delete a tag for an environment variable"""
        return self._api.delete_tag_for_env_var(body, name, **kwargs)

    def get(self, key: str, **kwargs) -> str:
        """Get an environment variable"""
        return self._api.get(key, **kwargs)

    def get_all(self, **kwargs) -> List[EnvironmentVariable]:
        """Get all environment variables"""
        return self._api.get_all(**kwargs)

    def get_tags_for_env_var(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for an environment variable"""
        return self._api.get_tags_for_env_var(name, **kwargs)

    def put_tag_for_env_var(self, body: List[Tag], name: str, **kwargs) -> None:
        """Put a tag for an environment variable"""
        return self._api.put_tag_for_env_var(body, name, **kwargs)
