from __future__ import annotations

from typing import Any, Dict, List, Optional, cast
from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.authorization_request_adapter import (
    AuthorizationRequestAdapter,
)
from conductor.asyncio_client.adapters.models.conductor_user_adapter import (
    ConductorUserAdapter,
)
from conductor.asyncio_client.adapters.models.create_or_update_application_request_adapter import (
    CreateOrUpdateApplicationRequestAdapter,
)
from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import (
    ExtendedConductorApplicationAdapter,
)
from conductor.asyncio_client.adapters.models.granted_access_adapter import (
    GrantedAccessAdapter,
)
from conductor.asyncio_client.adapters.models.granted_access_response_adapter import (
    GrantedAccessResponseAdapter,
)
from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.target_ref_adapter import (
    TargetRefAdapter,
)
from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import (
    UpsertGroupRequestAdapter,
)
from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import (
    UpsertUserRequestAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient
from conductor.asyncio_client.adapters.models.created_access_key_adapter import (
    CreatedAccessKeyAdapter,
)
from conductor.asyncio_client.adapters.models.access_key_adapter import AccessKeyAdapter
from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter


class OrkesAuthorizationClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # User Operations
    @deprecated("create_user is deprecated; use create_user_validated instead")
    @typing_deprecated("create_user is deprecated; use create_user_validated instead")
    async def create_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> object:
        """Create a new user"""
        return await self._user_api.upsert_user(id=user_id, upsert_user_request=upsert_user_request)

    async def create_user_validated(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter, **kwargs
    ) -> Optional[ConductorUserAdapter]:
        """Create a new user and return a validated ConductorUserAdapter"""
        result = await self._user_api.upsert_user(
            id=user_id, upsert_user_request=upsert_user_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ConductorUserAdapter.from_dict(result_dict)

        return result_model

    @deprecated("update_user is deprecated; use update_user_validated instead")
    @typing_deprecated("update_user is deprecated; use update_user_validated instead")
    async def update_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> object:
        """Update an existing user"""
        return await self._user_api.upsert_user(id=user_id, upsert_user_request=upsert_user_request)

    async def update_user_validated(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter, **kwargs
    ) -> Optional[ConductorUserAdapter]:
        """Update an existing user and return a validated ConductorUserAdapter"""
        result = await self._user_api.upsert_user(
            id=user_id, upsert_user_request=upsert_user_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ConductorUserAdapter.from_dict(result_dict)

        return result_model

    @deprecated("get_user is deprecated; use get_user_validated instead")
    @typing_deprecated("get_user is deprecated; use get_user_validated instead")
    async def get_user(self, user_id: str) -> object:
        """Get user by ID"""
        result = await self._user_api.get_user(id=user_id)
        return result

    async def get_user_validated(self, user_id: str, **kwargs) -> Optional[ConductorUserAdapter]:
        """Get a user and return a validated ConductorUserAdapter"""
        result = await self._user_api.get_user(id=user_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = ConductorUserAdapter.from_dict(result_dict)

        return result_model

    async def delete_user(self, user_id: str, **kwargs) -> None:
        """Delete user by ID"""
        await self._user_api.delete_user(id=user_id, **kwargs)

    async def list_users(self, include_apps: bool = False, **kwargs) -> List[ConductorUserAdapter]:
        """List all users"""
        return await self._user_api.list_users(apps=include_apps, **kwargs)

    async def get_user_permissions(
        self, user_id: str, **kwargs
    ) -> Optional[GrantedAccessResponseAdapter]:
        """Get permissions granted to user"""
        result = await self._user_api.get_granted_permissions(user_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = GrantedAccessResponseAdapter.from_dict(result_dict)

        return result_model

    # Application Operations
    @deprecated("create_application is deprecated; use create_application_validated instead")
    @typing_deprecated("create_application is deprecated; use create_application_validated instead")
    async def create_application(
        self, create_or_update_application_request: CreateOrUpdateApplicationRequestAdapter
    ) -> object:
        """Create a new application"""
        result = await self._application_api.create_application(
            create_or_update_application_request=create_or_update_application_request
        )
        return result

    async def create_application_validated(
        self,
        create_or_update_application_request: CreateOrUpdateApplicationRequestAdapter,
        **kwargs,
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        """Create a new application and return a validated ExtendedConductorApplicationAdapter"""
        result = await self._application_api.create_application(
            create_or_update_application_request=create_or_update_application_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    @deprecated("update_application is deprecated; use update_application_validated instead")
    @typing_deprecated("update_application is deprecated; use update_application_validated instead")
    async def update_application(
        self, application_id: str, application: CreateOrUpdateApplicationRequestAdapter
    ) -> object:
        """Update an existing application"""
        result = await self._application_api.update_application(application_id, application)
        return result

    async def update_application_validated(
        self,
        application_id: str,
        create_or_update_application_request: CreateOrUpdateApplicationRequestAdapter,
        **kwargs,
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        """Update an existing application and return a validated ExtendedConductorApplicationAdapter"""
        result = await self._application_api.update_application(
            id=application_id,
            create_or_update_application_request=create_or_update_application_request,
            **kwargs,
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    @deprecated("get_application is deprecated; use get_application_validated instead")
    @typing_deprecated("get_application is deprecated; use get_application_validated instead")
    async def get_application(self, application_id: str) -> object:
        """Get application by ID"""
        result = await self._application_api.get_application(id=application_id)
        return result

    async def get_application_validated(
        self, application_id: str, **kwargs
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        """Get an application by ID and return a validated ExtendedConductorApplicationAdapter"""
        result = await self._application_api.get_application(id=application_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    async def delete_application(self, application_id: str, **kwargs) -> None:
        """Delete application by ID"""
        await self._application_api.delete_application(id=application_id, **kwargs)

    async def list_applications(self, **kwargs) -> List[ExtendedConductorApplicationAdapter]:
        """List all applications"""
        return await self._application_api.list_applications(**kwargs)

    # Group Operations
    @deprecated("create_group is deprecated; use create_group_validated instead")
    @typing_deprecated("create_group is deprecated; use create_group_validated instead")
    async def create_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter
    ) -> object:
        """Create a new group"""
        return await self._group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request
        )

    async def create_group_validated(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter, **kwargs
    ) -> Optional[GroupAdapter]:
        """Create a new group and return a validated GroupAdapter"""
        result = await self._group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = GroupAdapter.from_dict(result_dict)

        return result_model

    async def update_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter, **kwargs
    ) -> Optional[GroupAdapter]:
        """Update an existing group"""
        result = await self._group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = GroupAdapter.from_dict(result_dict)

        return result_model

    @deprecated("get_group is deprecated; use get_group_validated instead")
    @typing_deprecated("get_group is deprecated; use get_group_validated instead")
    async def get_group(self, group_id: str) -> object:
        """Get group by ID"""
        result = await self._group_api.get_group(id=group_id)
        return result

    async def get_group_validated(self, group_id: str, **kwargs) -> Optional[GroupAdapter]:
        """Get a group by ID and return a validated GroupAdapter"""
        result = await self._group_api.get_group(id=group_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = GroupAdapter.from_dict(result_dict)

        return result_model

    async def delete_group(self, group_id: str, **kwargs) -> None:
        """Delete group by ID"""
        await self._group_api.delete_group(id=group_id, **kwargs)

    async def list_groups(self, **kwargs) -> List[GroupAdapter]:
        """List all groups"""
        return await self._group_api.list_groups(**kwargs)

    # Group User Management Operations
    @deprecated("add_user_to_group is deprecated; use add_user_to_group_validated instead")
    @typing_deprecated("add_user_to_group is deprecated; use add_user_to_group_validated instead")
    async def add_user_to_group(self, group_id: str, user_id: str) -> object:
        """Add a user to a group"""
        return await self._group_api.add_user_to_group(group_id=group_id, user_id=user_id)

    async def add_user_to_group_validated(self, group_id: str, user_id: str, **kwargs) -> None:
        """Add a user to a group and return None"""
        await self._group_api.add_user_to_group(group_id=group_id, user_id=user_id, **kwargs)

    @deprecated(
        "remove_user_from_group is deprecated; use remove_user_from_group_validated instead"
    )
    @typing_deprecated(
        "remove_user_from_group is deprecated; use remove_user_from_group_validated instead"
    )
    async def remove_user_from_group(self, group_id: str, user_id: str) -> object:
        """Remove a user from a group"""
        return await self._group_api.remove_user_from_group(group_id=group_id, user_id=user_id)

    async def remove_user_from_group_validated(self, group_id: str, user_id: str, **kwargs) -> None:
        """Remove a user from a group and return None"""
        await self._group_api.remove_user_from_group(group_id=group_id, user_id=user_id, **kwargs)

    @deprecated("add_users_to_group is deprecated; use add_users_to_group_validated instead")
    @typing_deprecated("add_users_to_group is deprecated; use add_users_to_group_validated instead")
    async def add_users_to_group(self, group_id: str, user_ids: List[str]) -> None:
        """Add multiple users to a group"""
        return await self._group_api.add_users_to_group(group_id=group_id, request_body=user_ids)

    async def add_users_to_group_validated(
        self, group_id: str, user_ids: List[str], **kwargs
    ) -> None:
        """Add multiple users to a group and return None"""
        await self._group_api.add_users_to_group(group_id=group_id, request_body=user_ids, **kwargs)

    async def remove_users_from_group(self, group_id: str, user_ids: List[str], **kwargs) -> None:
        """Remove multiple users from a group"""
        return await self._group_api.remove_users_from_group(
            group_id=group_id, request_body=user_ids, **kwargs
        )

    @deprecated("get_users_in_group is deprecated; use get_users_in_group_validated instead")
    @typing_deprecated("get_users_in_group is deprecated; use get_users_in_group_validated instead")
    async def get_users_in_group(self, group_id: str) -> object:
        """Get all users in a group"""
        return await self._group_api.get_users_in_group(id=group_id)

    async def get_users_in_group_validated(
        self, group_id: str, **kwargs
    ) -> List[Optional[ConductorUserAdapter]]:
        """Get all users in a group and return a list of validated ConductorUserAdapters"""
        result = await self._group_api.get_users_in_group(id=group_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = [ConductorUserAdapter.from_dict(_item) for _item in result_dict]

        return result_model

    # Permission Operations (Only available operations)
    @deprecated("grant_permissions is deprecated; use grant_permissions_validated instead")
    @typing_deprecated("grant_permissions is deprecated; use grant_permissions_validated instead")
    async def grant_permissions(self, authorization_request: AuthorizationRequestAdapter) -> object:
        """Grant permissions to users or groups"""
        return await self._authorization_api.grant_permissions(
            authorization_request=authorization_request
        )

    async def grant_permissions_validated(
        self, authorization_request: AuthorizationRequestAdapter, **kwargs
    ) -> None:
        """Grant permissions to users or groups and return None"""
        await self._authorization_api.grant_permissions(
            authorization_request=authorization_request, **kwargs
        )

    @deprecated("remove_permissions is deprecated; use remove_permissions_validated instead")
    @typing_deprecated("remove_permissions is deprecated; use remove_permissions_validated instead")
    async def remove_permissions(
        self, authorization_request: AuthorizationRequestAdapter
    ) -> object:
        """Remove permissions from users or groups"""
        return await self._authorization_api.remove_permissions(
            authorization_request=authorization_request
        )

    async def remove_permissions_validated(
        self, authorization_request: AuthorizationRequestAdapter, **kwargs
    ) -> None:
        """Remove permissions from users or groups and return None"""
        await self._authorization_api.remove_permissions(
            authorization_request=authorization_request, **kwargs
        )

    @deprecated("get_permissions is deprecated; use get_permissions_validated instead")
    @typing_deprecated("get_permissions is deprecated; use get_permissions_validated instead")
    async def get_permissions(self, entity_type: str, entity_id: str) -> object:
        """Get permissions for a specific entity (user, group, or application)"""
        return await self._authorization_api.get_permissions(type=entity_type, id=entity_id)

    async def get_permissions_validated(
        self, target: TargetRefAdapter, **kwargs
    ) -> Dict[str, List[SubjectRefAdapter]]:
        """Get permissions for a specific entity (user, group, or application) and return a dictionary of access types and validated SubjectRefAdapters"""
        result = await self._authorization_api.get_permissions(
            type=target.type, id=target.id, **kwargs
        )

        permissions = {}
        for access_type, subjects in result.items():
            subject_list = [SubjectRefAdapter(sub["id"], sub["type"]) for sub in subjects]
            permissions[access_type] = subject_list

        return permissions

    async def get_group_permissions(self, group_id: str, **kwargs) -> GrantedAccessResponseAdapter:
        """Get permissions granted to a group"""
        return await self._group_api.get_granted_permissions1(group_id=group_id, **kwargs)

    # Convenience Methods
    @deprecated("upsert_user is deprecated; use upsert_user_validated instead")
    @typing_deprecated("upsert_user is deprecated; use upsert_user_validated instead")
    async def upsert_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> object:
        """Alias for create_user/update_user"""
        result = await self.create_user(user_id, upsert_user_request)
        return result

    async def upsert_user_validated(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter, **kwargs
    ) -> Optional[ConductorUserAdapter]:
        """Alias for create_user_validated/update_user_validated"""
        result = await self.create_user_validated(user_id, upsert_user_request, **kwargs)
        return result

    async def upsert_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter, **kwargs
    ) -> Optional[GroupAdapter]:
        """Alias for create_group/update_group"""
        result = await self.create_group_validated(group_id, upsert_group_request, **kwargs)
        return result

    async def set_application_tags(
        self, tags: List[TagAdapter], application_id: str, **kwargs
    ) -> None:
        await self._application_api.put_tag_for_application(id=application_id, tag=tags, **kwargs)

    async def get_application_tags(self, application_id: str, **kwargs) -> List[TagAdapter]:
        return await self._application_api.get_tags_for_application(id=application_id, **kwargs)

    async def delete_application_tags(
        self, tags: List[TagAdapter], application_id: str, **kwargs
    ) -> None:
        await self._application_api.delete_tag_for_application(
            id=application_id, tag=tags, **kwargs
        )

    @deprecated("create_access_key is deprecated; use create_access_key_validated instead")
    @typing_deprecated("create_access_key is deprecated; use create_access_key_validated instead")
    async def create_access_key(self, application_id: str) -> object:
        key_obj = await self._application_api.create_access_key(application_id)
        return key_obj

    async def create_access_key_validated(
        self, application_id: str, **kwargs
    ) -> CreatedAccessKeyAdapter:
        """Create an access key and return a validated CreatedAccessKeyAdapter"""
        result = await self._application_api.create_access_key(id=application_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = CreatedAccessKeyAdapter.from_dict(result_dict)

        return result_model

    @deprecated("get_access_keys is deprecated; use get_access_keys_validated instead")
    @typing_deprecated("get_access_keys is deprecated; use get_access_keys_validated instead")
    async def get_access_keys(self, application_id: str) -> object:
        access_keys_obj = await self._application_api.get_access_keys(application_id)
        return access_keys_obj

    async def get_access_keys_validated(
        self, application_id: str, **kwargs
    ) -> List[AccessKeyAdapter]:
        """Get access keys for an application and return a list of validated AccessKeyAdapters"""
        result = await self._application_api.get_access_keys(application_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = [AccessKeyAdapter.from_dict(_item) for _item in result_dict]

        return result_model

    @deprecated(
        "toggle_access_key_status is deprecated; use toggle_access_key_status_validated instead"
    )
    @typing_deprecated(
        "toggle_access_key_status is deprecated; use toggle_access_key_status_validated instead"
    )
    async def toggle_access_key_status(self, application_id: str, key_id: str) -> object:
        key_obj = await self._application_api.toggle_access_key_status(application_id, key_id)
        return key_obj

    async def toggle_access_key_status_validated(
        self, application_id: str, key_id: str, **kwargs
    ) -> AccessKeyAdapter:
        """Toggle the status of an access key and return a validated AccessKeyAdapter"""
        result = await self._application_api.toggle_access_key_status(
            application_id=application_id, key_id=key_id, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = AccessKeyAdapter.from_dict(result_dict)

        return result_model

    async def delete_access_key(self, application_id: str, key_id: str, **kwargs) -> None:
        await self._application_api.delete_access_key(
            application_id=application_id, key_id=key_id, **kwargs
        )

    async def add_role_to_application_user(self, application_id: str, role: str, **kwargs) -> None:
        await self._application_api.add_role_to_application_user(
            application_id=application_id, role=role, **kwargs
        )

    async def remove_role_from_application_user(
        self, application_id: str, role: str, **kwargs
    ) -> None:
        await self._application_api.remove_role_from_application_user(
            application_id=application_id, role=role, **kwargs
        )

    async def get_granted_permissions_for_group(
        self, group_id: str, **kwargs
    ) -> List[GrantedAccessAdapter]:
        granted_access_obj = await self.get_group_permissions(group_id=group_id, **kwargs)

        if not granted_access_obj.granted_access:
            return []

        granted_permissions = []
        for ga in granted_access_obj.granted_access:
            if not ga.target:
                continue

            target = TargetRefAdapter(type=ga.target.type, id=ga.target.id)
            access = ga.access
            granted_permissions.append(GrantedAccessAdapter(target=target, access=access))

        return granted_permissions

    async def get_granted_permissions_for_user(
        self, user_id: str, **kwargs
    ) -> List[GrantedAccessAdapter]:
        granted_access_obj = await self.get_user_permissions(user_id=user_id, **kwargs)

        if not granted_access_obj.granted_access:
            return []

        granted_permissions = []
        for ga in granted_access_obj.granted_access:
            target = TargetRefAdapter(type=ga.target.type, id=ga.target.id)
            access = ga.access
            granted_permissions.append(GrantedAccessAdapter(target=target, access=access))

        return granted_permissions

    async def get_app_by_access_key_id(
        self, access_key_id: str, **kwargs
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        result = await self._application_api.get_app_by_access_key_id(
            access_key_id=access_key_id, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    async def check_permissions(
        self, user_id: str, type: str, id: str, **kwargs
    ) -> Dict[str, bool]:
        result = await self._user_api.check_permissions(user_id=user_id, type=type, id=id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = {k: v for k, v in result_dict.items() if isinstance(v, bool)}

        return result_model
