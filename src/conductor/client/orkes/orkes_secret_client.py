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
        super().__init__(configuration)

    def put_secret(self, key: str, value: str, **kwargs) -> None:
        self._secret_api.put_secret(body=value, key=key, **kwargs)

    def get_secret(self, key: str, **kwargs) -> str:
        return self._secret_api.get_secret(key=key, **kwargs)

    @deprecated("list_all_secret_names is deprecated; use list_all_secret_names_validated instead")
    @typing_deprecated(
        "list_all_secret_names is deprecated; use list_all_secret_names_validated instead"
    )
    def list_all_secret_names(self) -> Set[str]:
        return set(self._secret_api.list_all_secret_names())

    def list_all_secret_names_validated(self, **kwargs) -> List[str]:
        return self._secret_api.list_all_secret_names(**kwargs)

    def list_secrets_that_user_can_grant_access_to(self, **kwargs) -> List[str]:
        return self._secret_api.list_secrets_that_user_can_grant_access_to(**kwargs)

    def delete_secret(self, key: str, **kwargs) -> None:
        self._secret_api.delete_secret(key=key, **kwargs)

    def secret_exists(self, key: str, **kwargs) -> object:  # type: ignore[override]
        return self._secret_api.secret_exists(key=key, **kwargs)

    @deprecated("set_secret_tags is deprecated; use put_tag_for_secret instead")
    @typing_deprecated("set_secret_tags is deprecated; use put_tag_for_secret instead")
    def set_secret_tags(self, tags: List[Tag], key: str):
        self._secret_api.put_tag_for_secret(tags, key)

    def put_tag_for_secret(self, tags: List[Tag], key: str, **kwargs) -> None:
        self._secret_api.put_tag_for_secret(body=tags, key=key, **kwargs)

    @deprecated("get_secret_tags is deprecated; use get_tags instead")
    @typing_deprecated("get_secret_tags is deprecated; use get_tags instead")
    def get_secret_tags(self, key: str) -> List[Tag]:
        return self._secret_api.get_tags(key)

    def get_tags(self, key: str, **kwargs) -> List[Tag]:
        return self._secret_api.get_tags(key=key, **kwargs)

    @deprecated("delete_secret_tags is deprecated; use delete_tag_for_secret instead")
    @typing_deprecated("delete_secret_tags is deprecated; use delete_tag_for_secret instead")
    def delete_secret_tags(self, tags: List[Tag], key: str) -> None:
        return self._secret_api.delete_tag_for_secret(tags, key)

    def delete_tag_for_secret(self, tags: List[Tag], key: str, **kwargs) -> None:
        self._secret_api.delete_tag_for_secret(body=tags, key=key, **kwargs)

    def clear_local_cache(self, **kwargs) -> None:
        self._secret_api.clear_local_cache(**kwargs)

    def clear_redis_cache(self, **kwargs) -> None:
        self._secret_api.clear_redis_cache(**kwargs)

    def list_secrets_with_tags_that_user_can_grant_access_to(
        self, **kwargs
    ) -> List[ExtendedSecret]:
        return self._secret_api.list_secrets_with_tags_that_user_can_grant_access_to(**kwargs)
