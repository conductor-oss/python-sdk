from abc import ABC, abstractmethod
from typing import List, Set

from conductor.client.http.models.tag import Tag


class SecretClient(ABC):
    @abstractmethod
    def put_secret(self, key: str, value: str):
        pass

    @abstractmethod
    def get_secret(self, key: str) -> str:
        pass

    @abstractmethod
    def list_all_secret_names(self) -> Set[str]:
        pass

    @abstractmethod
    def list_secrets_that_user_can_grant_access_to(self) -> List[str]:
        pass

    @abstractmethod
    def delete_secret(self, key: str):
        pass

    @abstractmethod
    def secret_exists(self, key: str, **kwargs) -> bool:
        pass

    @abstractmethod
    def set_secret_tags(self, tags: List[Tag], key: str) -> None:
        pass

    @abstractmethod
    def get_secret_tags(self, key: str) -> List[Tag]:
        pass

    @abstractmethod
    def delete_secret_tags(self, tags: List[Tag], key: str) -> None:
        pass
