from typing import List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.group_resource_api import GroupResourceApi
from conductor.client.http.models.granted_access_response import GrantedAccessResponse
from conductor.client.http.models.group import Group
from conductor.client.http.models.response import Response
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest


class GroupResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = GroupResourceApi(api_client)

    def add_user_to_group(self, group_id: str, user_id: str, **kwargs) -> object:
        """Add a user to a group"""
        return self._api.add_user_to_group(group_id, user_id, **kwargs)

    def add_users_to_group(self, body: List[str], group_id: str, **kwargs) -> None:
        """Add users to a group"""
        return self._api.add_users_to_group(body, group_id, **kwargs)

    def delete_group(self, id: str, **kwargs) -> Response:
        """Delete a group"""
        return self._api.delete_group(id, **kwargs)

    def get_granted_permissions1(self, group_id: str, **kwargs) -> GrantedAccessResponse:
        """Get granted permissions for a group"""
        return self._api.get_granted_permissions1(group_id, **kwargs)

    def get_group(self, id: str, **kwargs) -> object:
        """Get a group"""
        return self._api.get_group(id, **kwargs)

    def get_users_in_group(self, id: str, **kwargs) -> object:
        """Get users in a group"""
        return self._api.get_users_in_group(id, **kwargs)

    def list_groups(self, **kwargs) -> List[Group]:
        """List groups"""
        return self._api.list_groups(**kwargs)

    def remove_user_from_group(self, group_id: str, user_id: str, **kwargs) -> object:
        """Remove a user from a group"""
        return self._api.remove_user_from_group(group_id, user_id, **kwargs)

    def remove_users_from_group(self, body: List[str], group_id: str, **kwargs) -> None:
        """Remove users from a group"""
        return self._api.remove_users_from_group(body, group_id, **kwargs)

    def upsert_group(self, body: UpsertGroupRequest, id: str, **kwargs) -> object:
        """Upsert a group"""
        return self._api.upsert_group(body, id, **kwargs)
