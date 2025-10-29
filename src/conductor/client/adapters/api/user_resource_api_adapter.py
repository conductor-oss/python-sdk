from conductor.client.codegen.api.user_resource_api import UserResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.response import Response
from conductor.client.http.models.conductor_user import ConductorUser
from typing import List
from conductor.client.http.models.upsert_user_request import UpsertUserRequest


class UserResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = UserResourceApi(api_client)

    def check_permissions(self, user_id: str, type: str, id: str, **kwargs) -> object:
        """Check permissions for a user"""
        return self._api.check_permissions(user_id, type, id, **kwargs)

    def get_granted_permissions(self, user_id: str, **kwargs) -> object:
        """Get the permissions this user has over workflows and tasks"""
        # Convert empty user_id to None to prevent sending invalid data to server
        if not user_id:
            user_id = None
        return self._api.get_granted_permissions(user_id=user_id, **kwargs)

    def get_user(self, id: str, **kwargs) -> object:
        """Get a user by their ID"""
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return self._api.get_user(id=id, **kwargs)

    def upsert_user(self, upsert_user_request: UpsertUserRequest, id: str, **kwargs) -> Response:
        """Create or update a user"""
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return self._api.upsert_user(id=id, body=upsert_user_request, **kwargs)

    def delete_user(self, id: str, **kwargs) -> Response:
        """Delete a user"""
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return self._api.delete_user(id=id, **kwargs)

    def list_users(self, **kwargs) -> List[ConductorUser]:
        """Get all users"""
        return self._api.list_users(**kwargs)
