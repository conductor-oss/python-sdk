from __future__ import annotations

from typing import Dict, List, Optional

from conductor.asyncio_client.adapters.models.authorization_request_adapter import (
    AuthorizationRequestAdapter as AuthorizationRequest,
)
from conductor.asyncio_client.adapters.models.conductor_user_adapter import (
    ConductorUserAdapter as ConductorUser,
)
from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import (
    ExtendedConductorApplicationAdapter as ExtendedConductorApplication,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter as Tag
from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter as Group
from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import (
    UpsertGroupRequestAdapter as UpsertGroupRequest,
)
from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import (
    UpsertUserRequestAdapter as UpsertUserRequest,
)
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient
from conductor.asyncio_client.adapters.models.create_or_update_application_request_adapter import (
    CreateOrUpdateApplicationRequestAdapter,
)
from conductor.client.orkes.models.access_key import AccessKey
from conductor.client.orkes.models.access_type import AccessType
from conductor.asyncio_client.adapters.models.subject_ref_adapter import (
    SubjectRefAdapter as SubjectRef,
)
from conductor.asyncio_client.adapters.models.target_ref_adapter import (
    TargetRefAdapter as TargetRef,
)
from conductor.asyncio_client.adapters.models.granted_access_adapter import (
    GrantedAccessAdapter as GrantedAccess,
)


class OrkesAuthorizationClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # User Operations
    async def create_application(
        self,
        create_or_update_application_request: CreateOrUpdateApplicationRequestAdapter,
    ) -> ExtendedConductorApplication:
        app_obj = await self.application_api.create_application(
            create_or_update_application_request
        )
        return ExtendedConductorApplication.from_dict(app_obj)

    async def get_application(
        self, application_id: str
    ) -> ExtendedConductorApplication:
        app_obj = await self.application_api.get_application(application_id)
        return ExtendedConductorApplication.from_dict(app_obj)

    async def list_applications(self) -> List[ExtendedConductorApplication]:
        return await self.application_api.list_applications()

    async def update_application(
        self,
        create_or_update_application_request: CreateOrUpdateApplicationRequestAdapter,
        application_id: str,
    ) -> ExtendedConductorApplication:
        app_obj = await self.application_api.update_application(
            application_id, create_or_update_application_request
        )
        return ExtendedConductorApplication.from_dict(app_obj)

    async def delete_application(self, application_id: str):
        await self.application_api.delete_application(application_id)

    async def add_role_to_application_user(self, application_id: str, role: str):
        await self.application_api.add_role_to_application_user(application_id, role)

    async def remove_role_from_application_user(self, application_id: str, role: str):
        await self.application_api.remove_role_from_application_user(
            application_id, role
        )

    async def set_application_tags(self, tags: List[Tag], application_id: str):
        await self.application_api.put_tag_for_application(application_id, tags)

    async def get_application_tags(self, application_id: str) -> List[Tag]:
        return await self.application_api.get_tags_for_application(application_id)

    async def delete_application_tags(self, tags: List[Tag], application_id: str):
        await self.application_api.delete_tag_for_application(tags, application_id)

    async def create_access_key(self, application_id: str) -> AccessKey:
        key_obj = await self.application_api.create_access_key(application_id)
        return key_obj

    async def get_access_keys(self, application_id: str) -> List[AccessKey]:
        access_keys_obj = await self.application_api.get_access_keys(application_id)

        access_keys = []
        for key_obj in access_keys_obj:
            access_keys.append(key_obj)

        return access_keys

    async def toggle_access_key_status(
        self, application_id: str, key_id: str
    ) -> AccessKey:
        key_obj = await self.application_api.toggle_access_key_status(
            application_id, key_id
        )
        return key_obj

    async def delete_access_key(self, application_id: str, key_id: str):
        await self.application_api.delete_access_key(application_id, key_id)

    # Users

    async def upsert_user(
        self, upsert_user_request: UpsertUserRequest, user_id: str
    ) -> ConductorUser:
        user_obj = await self.user_api.upsert_user(user_id, upsert_user_request)
        return ConductorUser.from_dict(user_obj)

    async def get_user(self, user_id: str) -> ConductorUser:
        user_obj = await self.user_api.get_user(user_id)
        return ConductorUser.from_dict(user_obj)

    async def list_users(self, apps: Optional[bool] = False) -> List[ConductorUser]:
        kwargs = {"apps": apps}
        return await self.user_api.list_users(**kwargs)

    async def delete_user(self, user_id: str):
        await self.user_api.delete_user(user_id)

    # Groups

    async def upsert_group(
        self, upsert_group_request: UpsertGroupRequest, group_id: str
    ) -> Group:
        group_obj = await self.group_api.upsert_group(group_id, upsert_group_request)
        return Group.from_dict(group_obj)

    async def get_group(self, group_id: str) -> Group:
        group_obj = await self.group_api.get_group(group_id)
        return Group.from_dict(group_obj)

    async def list_groups(self) -> List[Group]:
        return await self.group_api.list_groups()

    async def delete_group(self, group_id: str):
        await self.group_api.delete_group(group_id)

    async def add_user_to_group(self, group_id: str, user_id: str):
        await self.group_api.add_user_to_group(group_id, user_id)

    async def get_users_in_group(self, group_id: str) -> List[ConductorUser]:
        user_objs = await self.group_api.get_users_in_group(group_id)
        group_users = []
        for u in user_objs:
            c_user = ConductorUser.from_dict(u)
            group_users.append(c_user)

        return group_users

    async def remove_user_from_group(self, group_id: str, user_id: str):
        await self.group_api.remove_user_from_group(group_id, user_id)

    # Permissions

    async def grant_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType]
    ):
        req = AuthorizationRequest(access=access, subject=subject, target=target)
        await self.authorization_api.grant_permissions(req)

    async def get_permissions(self, target: TargetRef) -> Dict[str, List[SubjectRef]]:
        resp_obj = await self.authorization_api.get_permissions(
            target.type, target.id
        )
        permissions = {}
        for access_type, subjects in resp_obj.items():
            subject_list = [
                SubjectRef(type=sub["type"], id=sub["id"]) for sub in subjects
            ]
            permissions[access_type] = subject_list
        return permissions

    async def get_granted_permissions_for_group(
        self, group_id: str
    ) -> List[GrantedAccess]:
        granted_access_obj = await self.group_api.get_granted_permissions1(group_id)
        granted_permissions = []
        for ga in granted_access_obj.granted_access:
            target = TargetRef(type=ga.target.type, id=ga.target.id)
            access = ga.access
            granted_permissions.append(GrantedAccess(target=target, access=access))
        return granted_permissions

    async def get_granted_permissions_for_user(
        self, user_id: str
    ) -> List[GrantedAccess]:
        granted_access_obj = await self.user_api.get_granted_permissions(user_id)
        granted_permissions = []
        for ga in granted_access_obj["grantedAccess"]:
            target = TargetRef(type=ga["target"]["type"], id=ga["target"]["id"])
            access = ga["access"]
            granted_permissions.append(GrantedAccess(target=target, access=access))
        return granted_permissions

    async def remove_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType]
    ):
        req = AuthorizationRequest(subject=subject, target=target, access=access)
        await self.authorization_api.remove_permissions(req)
