from __future__ import annotations

from typing import List

from conductor.asyncio_client.adapters.models.authorization_request_adapter import \
    AuthorizationRequestAdapter
from conductor.asyncio_client.adapters.models.conductor_user_adapter import \
    ConductorUserAdapter
from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import \
    ExtendedConductorApplicationAdapter
from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter
from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import \
    UpsertGroupRequestAdapter
from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import \
    UpsertUserRequestAdapter
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesAuthorizationClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # User Operations
    async def create_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> ConductorUserAdapter:
        """Create a new user"""
        return await self.user_api.upsert_user(
            id=user_id, upsert_user_request=upsert_user_request
        )

    async def update_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> ConductorUserAdapter:
        """Update an existing user"""
        return await self.user_api.upsert_user(
            id=user_id, upsert_user_request=upsert_user_request
        )

    async def get_user(self, user_id: str) -> ConductorUserAdapter:
        """Get user by ID"""
        return await self.user_api.get_user(id=user_id)

    async def delete_user(self, user_id: str) -> None:
        """Delete user by ID"""
        await self.user_api.delete_user(id=user_id)

    async def list_users(
        self, include_apps: bool = False
    ) -> List[ConductorUserAdapter]:
        """List all users"""
        return await self.user_api.list_users(apps=include_apps)

    # Application Operations
    async def create_application(
        self, application: ExtendedConductorApplicationAdapter
    ) -> ExtendedConductorApplicationAdapter:
        """Create a new application"""
        return await self.application_api.create_application(
            create_or_update_application_request=application
        )

    async def update_application(
        self, application_id: str, application: ExtendedConductorApplicationAdapter
    ) -> ExtendedConductorApplicationAdapter:
        """Update an existing application"""
        return await self.application_api.update_application(
            id=application_id, create_or_update_application_request=application
        )

    async def get_application(
        self, application_id: str
    ) -> ExtendedConductorApplicationAdapter:
        """Get application by ID"""
        return await self.application_api.get_application(id=application_id)

    async def delete_application(self, application_id: str) -> None:
        """Delete application by ID"""
        await self.application_api.delete_application(id=application_id)

    async def list_applications(self) -> List[ExtendedConductorApplicationAdapter]:
        """List all applications"""
        return await self.application_api.list_applications()

    # Group Operations
    async def create_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter
    ) -> GroupAdapter:
        """Create a new group"""
        return await self.group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request
        )

    async def update_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter
    ) -> GroupAdapter:
        """Update an existing group"""
        return await self.group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request
        )

    async def get_group(self, group_id: str) -> GroupAdapter:
        """Get group by ID"""
        return await self.group_api.get_group(id=group_id)

    async def delete_group(self, group_id: str) -> None:
        """Delete group by ID"""
        await self.group_api.delete_group(id=group_id)

    async def list_groups(self) -> List[GroupAdapter]:
        """List all groups"""
        return await self.group_api.list_groups()

    # Group User Management Operations
    async def add_user_to_group(self, group_id: str, user_id: str) -> object:
        """Add a user to a group"""
        return await self.group_api.add_user_to_group(
            group_id=group_id, user_id=user_id
        )

    async def remove_user_from_group(self, group_id: str, user_id: str) -> object:
        """Remove a user from a group"""
        return await self.group_api.remove_user_from_group(
            group_id=group_id, user_id=user_id
        )

    async def add_users_to_group(self, group_id: str, user_ids: List[str]) -> object:
        """Add multiple users to a group"""
        return await self.group_api.add_users_to_group(
            group_id=group_id, request_body=user_ids
        )

    async def remove_users_from_group(
        self, group_id: str, user_ids: List[str]
    ) -> object:
        """Remove multiple users from a group"""
        return await self.group_api.remove_users_from_group(
            group_id=group_id, request_body=user_ids
        )

    async def get_users_in_group(self, group_id: str) -> object:
        """Get all users in a group"""
        return await self.group_api.get_users_in_group(id=group_id)

    # Permission Operations (Only available operations)
    async def grant_permissions(
        self, authorization_request: AuthorizationRequestAdapter
    ) -> object:
        """Grant permissions to users or groups"""
        return await self.authorization_api.grant_permissions(
            authorization_request=authorization_request
        )

    async def remove_permissions(
        self, authorization_request: AuthorizationRequestAdapter
    ) -> object:
        """Remove permissions from users or groups"""
        return await self.authorization_api.remove_permissions(
            authorization_request=authorization_request
        )

    async def get_permissions(self, entity_type: str, entity_id: str) -> object:
        """Get permissions for a specific entity (user, group, or application)"""
        return await self.authorization_api.get_permissions(
            type=entity_type, id=entity_id
        )

    async def get_group_permissions(self, group_id: str) -> object:
        """Get permissions granted to a group"""
        return await self.group_api.get_granted_permissions1(group_id=group_id)

    # Convenience Methods
    async def upsert_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> ConductorUserAdapter:
        """Alias for create_user/update_user"""
        return await self.create_user(user_id, upsert_user_request)

    async def upsert_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter
    ) -> GroupAdapter:
        """Alias for create_group/update_group"""
        return await self.create_group(group_id, upsert_group_request)
