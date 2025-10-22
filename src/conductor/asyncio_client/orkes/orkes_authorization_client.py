from __future__ import annotations

from typing import List

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.authorization_request_adapter import (
    AuthorizationRequestAdapter as AuthorizationRequest,
)
from conductor.asyncio_client.adapters.models.conductor_user_adapter import (
    ConductorUserAdapter as ConductorUser,
)
from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import (
    ExtendedConductorApplicationAdapter as ExtendedConductorApplication,
)
from conductor.asyncio_client.adapters.models.granted_access_adapter import (
    GrantedAccessAdapter as GrantedAccess,
)
from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter as Group
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter as Tag
from conductor.asyncio_client.adapters.models.target_ref_adapter import (
    TargetRefAdapter as TargetRef,
)
from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import (
    UpsertGroupRequestAdapter as UpsertGroupRequest,
)
from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import (
    UpsertUserRequestAdapter as UpsertUserRequest,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.orkes.models.access_key import AccessKey


class OrkesAuthorizationClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # User Operations
    async def create_user(
        self, user_id: str, upsert_user_request: UpsertUserRequest
    ) -> ConductorUser:
        """Create a new user"""
        return await self.user_api.upsert_user(id=user_id, upsert_user_request=upsert_user_request)

    async def update_user(
        self, user_id: str, upsert_user_request: UpsertUserRequest
    ) -> ConductorUser:
        """Update an existing user"""
        return await self.user_api.upsert_user(id=user_id, upsert_user_request=upsert_user_request)

    async def get_user(self, user_id: str) -> ConductorUser:
        """Get user by ID"""
        user = await self.user_api.get_user(id=user_id)
        print(user)

        return ConductorUser.from_dict(user)

    async def delete_user(self, user_id: str) -> None:
        """Delete user by ID"""
        await self.user_api.delete_user(id=user_id)

    async def list_users(self, include_apps: bool = False) -> List[ConductorUser]:
        """List all users"""
        return await self.user_api.list_users(apps=include_apps)

    # Application Operations
    async def create_application(
        self, application: ExtendedConductorApplication
    ) -> ExtendedConductorApplication:
        """Create a new application"""
        app = await self.application_api.create_application(
            create_or_update_application_request=application
        )
        return ExtendedConductorApplication.from_dict(app)

    async def update_application(
        self, application_id: str, application: ExtendedConductorApplication
    ) -> ExtendedConductorApplication:
        """Update an existing application"""
        app = await self.application_api.update_application(
            id=application_id, create_or_update_application_request=application
        )
        return ExtendedConductorApplication.from_dict(app)

    async def get_application(self, application_id: str) -> ExtendedConductorApplication:
        """Get application by ID"""
        app = await self.application_api.get_application(id=application_id)
        return ExtendedConductorApplication.from_dict(app)

    async def delete_application(self, application_id: str) -> None:
        """Delete application by ID"""
        await self.application_api.delete_application(id=application_id)

    async def list_applications(self) -> List[ExtendedConductorApplication]:
        """List all applications"""
        return await self.application_api.list_applications()

    # Group Operations
    async def create_group(self, group_id: str, upsert_group_request: UpsertGroupRequest) -> Group:
        """Create a new group"""
        return await self.group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request
        )

    async def update_group(self, group_id: str, upsert_group_request: UpsertGroupRequest) -> Group:
        """Update an existing group"""
        group = await self.group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request
        )
        return Group.from_dict(group)

    async def get_group(self, group_id: str) -> Group:
        """Get group by ID"""
        group = await self.group_api.get_group(id=group_id)
        return Group.from_dict(group)

    async def delete_group(self, group_id: str) -> None:
        """Delete group by ID"""
        await self.group_api.delete_group(id=group_id)

    async def list_groups(self) -> List[Group]:
        """List all groups"""
        return await self.group_api.list_groups()

    # Group User Management Operations
    async def add_user_to_group(self, group_id: str, user_id: str) -> object:
        """Add a user to a group"""
        return await self.group_api.add_user_to_group(group_id=group_id, user_id=user_id)

    async def remove_user_from_group(self, group_id: str, user_id: str) -> object:
        """Remove a user from a group"""
        return await self.group_api.remove_user_from_group(group_id=group_id, user_id=user_id)

    async def add_users_to_group(self, group_id: str, user_ids: List[str]) -> object:
        """Add multiple users to a group"""
        return await self.group_api.add_users_to_group(group_id=group_id, request_body=user_ids)

    async def remove_users_from_group(self, group_id: str, user_ids: List[str]) -> object:
        """Remove multiple users from a group"""
        return await self.group_api.remove_users_from_group(
            group_id=group_id, request_body=user_ids
        )

    async def get_users_in_group(self, group_id: str) -> object:
        """Get all users in a group"""
        return await self.group_api.get_users_in_group(id=group_id)

    # Permission Operations (Only available operations)
    async def grant_permissions(self, authorization_request: AuthorizationRequest) -> object:
        """Grant permissions to users or groups"""
        return await self.authorization_api.grant_permissions(
            authorization_request=authorization_request
        )

    async def remove_permissions(self, authorization_request: AuthorizationRequest) -> object:
        """Remove permissions from users or groups"""
        return await self.authorization_api.remove_permissions(
            authorization_request=authorization_request
        )

    async def get_permissions(self, entity_type: str, entity_id: str) -> object:
        """Get permissions for a specific entity (user, group, or application)"""
        return await self.authorization_api.get_permissions(type=entity_type, id=entity_id)

    async def get_group_permissions(self, group_id: str) -> object:
        """Get permissions granted to a group"""
        return await self.group_api.get_granted_permissions1(group_id=group_id)

    # Convenience Methods
    async def upsert_user(
        self, user_id: str, upsert_user_request: UpsertUserRequest
    ) -> ConductorUser:
        """Alias for create_user/update_user"""
        user = await self.create_user(user_id, upsert_user_request)
        return ConductorUser.from_dict(user)

    async def upsert_group(self, group_id: str, upsert_group_request: UpsertGroupRequest) -> Group:
        """Alias for create_group/update_group"""
        group = await self.create_group(group_id, upsert_group_request)
        return Group.from_dict(group)

    async def set_application_tags(self, tags: List[Tag], application_id: str):
        await self.application_api.put_tag_for_application(application_id, tags)

    async def get_application_tags(self, application_id: str) -> List[Tag]:
        return await self.application_api.get_tags_for_application(application_id)

    async def delete_application_tags(self, tags: List[Tag], application_id: str):
        await self.application_api.delete_tag_for_application(application_id, tags)

    async def create_access_key(self, application_id: str) -> AccessKey:
        key_obj = await self.application_api.create_access_key(application_id)
        return key_obj

    async def get_access_keys(self, application_id: str) -> List[AccessKey]:
        access_keys_obj = await self.application_api.get_access_keys(application_id)
        access_keys = []
        for key_obj in access_keys_obj:
            access_keys.append(key_obj)

        return access_keys

    async def toggle_access_key_status(self, application_id: str, key_id: str) -> AccessKey:
        key_obj = await self.application_api.toggle_access_key_status(application_id, key_id)
        return key_obj

    async def delete_access_key(self, application_id: str, key_id: str):
        await self.application_api.delete_access_key(application_id, key_id)

    async def add_role_to_application_user(self, application_id: str, role: str):
        await self.application_api.add_role_to_application_user(application_id, role)

    async def remove_role_from_application_user(self, application_id: str, role: str):
        await self.application_api.remove_role_from_application_user(application_id, role)

    async def get_granted_permissions_for_group(self, group_id: str) -> List[GrantedAccess]:
        granted_access_obj = await self.group_api.get_granted_permissions1(group_id)
        granted_permissions = []
        for ga in granted_access_obj.granted_access:
            target = TargetRef(type=ga.target.type, id=ga.target.id)
            access = ga.access
            granted_permissions.append(GrantedAccess(target=target, access=access))
        return granted_permissions

    async def get_granted_permissions_for_user(self, user_id: str) -> List[GrantedAccess]:
        granted_access_obj = await self.user_api.get_granted_permissions(user_id)
        granted_permissions = []
        for ga in granted_access_obj["grantedAccess"]:
            target = TargetRef(type=ga["target"]["type"], id=ga["target"]["id"])
            access = ga["access"]
            granted_permissions.append(GrantedAccess(target=target, access=access))
        return granted_permissions

    async def get_app_by_access_key_id(
        self, access_key_id: str, *args, **kwargs
    ) -> ExtendedConductorApplication:
        application_access_key_obj = await self.application_api.get_app_by_access_key_id(
            access_key_id=access_key_id, *args, **kwargs
        )
        return ExtendedConductorApplication.from_dict(application_access_key_obj)
