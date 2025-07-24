from __future__ import annotations
from typing import Dict, List, Optional

from conductor.client.authorization_client import AuthorizationClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.authorization_request import AuthorizationRequest
from conductor.client.http.models.conductor_application import ConductorApplication
from conductor.client.http.models.conductor_user import ConductorUser
from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest
from conductor.client.http.models.group import Group
from conductor.client.http.models.subject_ref import SubjectRef
from conductor.client.http.models.target_ref import TargetRef
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.orkes.models.access_key import AccessKey
from conductor.client.orkes.models.access_type import AccessType
from conductor.client.orkes.models.created_access_key import CreatedAccessKey
from conductor.client.orkes.models.granted_permission import GrantedPermission
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient


class OrkesAuthorizationClient(OrkesBaseClient, AuthorizationClient):
    def __init__(self, configuration: Configuration):
        super(OrkesAuthorizationClient, self).__init__(configuration)

    # Applications
    def create_application(
            self,
            create_or_update_application_request: CreateOrUpdateApplicationRequest
    ) -> ConductorApplication:
        app_obj = self.applicationResourceApi.create_application(create_or_update_application_request)
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def get_application(self, application_id: str) -> ConductorApplication:
        app_obj = self.applicationResourceApi.get_application(application_id)
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def list_applications(self) -> List[ConductorApplication]:
        return self.applicationResourceApi.list_applications()

    def update_application(
            self,
            create_or_update_application_request: CreateOrUpdateApplicationRequest,
            application_id: str
    ) -> ConductorApplication:
        app_obj = self.applicationResourceApi.update_application(
            create_or_update_application_request, application_id
        )
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def delete_application(self, application_id: str):
        self.applicationResourceApi.delete_application(application_id)

    def add_role_to_application_user(self, application_id: str, role: str):
        self.applicationResourceApi.add_role_to_application_user(application_id, role)

    def remove_role_from_application_user(self, application_id: str, role: str):
        self.applicationResourceApi.remove_role_from_application_user(application_id, role)

    def set_application_tags(self, tags: List[MetadataTag], application_id: str):
        self.applicationResourceApi.put_tags_for_application(tags, application_id)

    def get_application_tags(self, application_id: str) -> List[MetadataTag]:
        return self.applicationResourceApi.get_tags_for_application(application_id)

    def delete_application_tags(self, tags: List[MetadataTag], application_id: str):
        self.applicationResourceApi.delete_tags_for_application(tags, application_id)

    def create_access_key(self, application_id: str) -> CreatedAccessKey:
        key_obj = self.applicationResourceApi.create_access_key(application_id)
        created_access_key = CreatedAccessKey(key_obj["id"], key_obj["secret"])
        return created_access_key

    def get_access_keys(self, application_id: str) -> List[AccessKey]:
        access_keys_obj = self.applicationResourceApi.get_access_keys(application_id)

        access_keys = []
        for key_obj in access_keys_obj:
            access_key = AccessKey(key_obj["id"], key_obj["status"], key_obj["createdAt"])
            access_keys.append(access_key)

        return access_keys

    def toggle_access_key_status(self, application_id: str, key_id: str) -> AccessKey:
        key_obj = self.applicationResourceApi.toggle_access_key_status(application_id, key_id)
        return AccessKey(key_obj["id"], key_obj["status"], key_obj["createdAt"])

    def delete_access_key(self, application_id: str, key_id: str):
        self.applicationResourceApi.delete_access_key(application_id, key_id)

    # Users

    def upsert_user(self, upsert_user_request: UpsertUserRequest, user_id: str) -> ConductorUser:
        user_obj = self.userResourceApi.upsert_user(upsert_user_request, user_id)
        return self.api_client.deserialize_class(user_obj, "ConductorUser")

    def get_user(self, user_id: str) -> ConductorUser:
        user_obj = self.userResourceApi.get_user(user_id)
        return self.api_client.deserialize_class(user_obj, "ConductorUser")

    def list_users(self, apps: Optional[bool] = False) -> List[ConductorUser]:
        kwargs = {"apps": apps}
        return self.userResourceApi.list_users(**kwargs)

    def delete_user(self, user_id: str):
        self.userResourceApi.delete_user(user_id)

    # Groups

    def upsert_group(self, upsert_group_request: UpsertGroupRequest, group_id: str) -> Group:
        group_obj = self.groupResourceApi.upsert_group(upsert_group_request, group_id)
        return self.api_client.deserialize_class(group_obj, "Group")

    def get_group(self, group_id: str) -> Group:
        group_obj = self.groupResourceApi.get_group(group_id)
        return self.api_client.deserialize_class(group_obj, "Group")

    def list_groups(self) -> List[Group]:
        return self.groupResourceApi.list_groups()

    def delete_group(self, group_id: str):
        self.groupResourceApi.delete_group(group_id)

    def add_user_to_group(self, group_id: str, user_id: str):
        self.groupResourceApi.add_user_to_group(group_id, user_id)

    def get_users_in_group(self, group_id: str) -> List[ConductorUser]:
        user_objs = self.groupResourceApi.get_users_in_group(group_id)
        group_users = []
        for u in user_objs:
            c_user = self.api_client.deserialize_class(u, "ConductorUser")
            group_users.append(c_user)

        return group_users

    def remove_user_from_group(self, group_id: str, user_id: str):
        self.groupResourceApi.remove_user_from_group(group_id, user_id)

    # Permissions

    def grant_permissions(self, subject: SubjectRef, target: TargetRef, access: List[AccessType]):
        req = AuthorizationRequest(subject, target, access)
        self.authorizationResourceApi.grant_permissions(req)

    def get_permissions(self, target: TargetRef) -> Dict[str, List[SubjectRef]]:
        resp_obj = self.authorizationResourceApi.get_permissions(target.type.name, target.id)
        permissions = {}
        for access_type, subjects in resp_obj.items():
            subject_list = [SubjectRef(sub["type"], sub["id"]) for sub in subjects]
            permissions[access_type] = subject_list
        return permissions

    def get_granted_permissions_for_group(self, group_id: str) -> List[GrantedPermission]:
        granted_access_obj = self.groupResourceApi.get_granted_permissions1(group_id)
        granted_permissions = []
        for ga in granted_access_obj['grantedAccess']:
            target = TargetRef(ga["target"]["type"], ga["target"]["id"])
            access = ga["access"]
            granted_permissions.append(GrantedPermission(target, access))
        return granted_permissions

    def get_granted_permissions_for_user(self, user_id: str) -> List[GrantedPermission]:
        granted_access_obj = self.userResourceApi.get_granted_permissions(user_id)
        granted_permissions = []
        for ga in granted_access_obj['grantedAccess']:
            target = TargetRef(ga["target"]["type"], ga["target"]["id"])
            access = ga["access"]
            granted_permissions.append(GrantedPermission(target, access))
        return granted_permissions

    def remove_permissions(self, subject: SubjectRef, target: TargetRef, access: List[AccessType]):
        req = AuthorizationRequest(subject, target, access)
        self.authorizationResourceApi.remove_permissions(req)
