from typing import List, Set

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.tag import Tag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.secret_client import SecretClient


class OrkesSecretClient(OrkesBaseClient, SecretClient):
    def __init__(self, configuration: Configuration):
        super(OrkesSecretClient, self).__init__(configuration)

    def put_secret(self, key: str, value: str):
        self._secret_api.put_secret(value, key)

    def get_secret(self, key: str) -> str:
        return self._secret_api.get_secret(key)

    def list_all_secret_names(self) -> Set[str]:
        return set(self._secret_api.list_all_secret_names())

    def list_secrets_that_user_can_grant_access_to(self) -> List[str]:
        return self._secret_api.list_secrets_that_user_can_grant_access_to()

    def delete_secret(self, key: str):
        self._secret_api.delete_secret(key)

    def secret_exists(self, key: str) -> object:
        return self._secret_api.secret_exists(key)

    def set_secret_tags(self, tags: List[Tag], key: str):
        self._secret_api.put_tag_for_secret(tags, key)

    def get_secret_tags(self, key: str) -> List[Tag]:
        return self._secret_api.get_tags(key)

    def delete_secret_tags(self, tags: List[Tag], key: str) -> None:
        return self._secret_api.delete_tag_for_secret(tags, key)
