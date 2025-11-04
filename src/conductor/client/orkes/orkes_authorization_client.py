from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from conductor.client.authorization_client import AuthorizationClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import ExtendedConductorApplication
from conductor.client.http.models.authorization_request import AuthorizationRequest
from conductor.client.http.models.conductor_application import ConductorApplication
from conductor.client.http.models.conductor_user import ConductorUser
from conductor.client.http.models.create_or_update_application_request import (
    CreateOrUpdateApplicationRequest,
)
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
        super().__init__(configuration)

    # Applications
    def create_application(
        self, create_or_update_application_request: CreateOrUpdateApplicationRequest, **kwargs
    ) -> ConductorApplication:
        app_obj = self._application_api.create_application(
            body=create_or_update_application_request, **kwargs
        )
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def get_application(self, application_id: str, **kwargs) -> ConductorApplication:
        app_obj = self._application_api.get_application(id=application_id, **kwargs)
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def get_app_by_access_key_id(self, access_key_id: str, **kwargs) -> ConductorApplication:
        app_obj = self._application_api.get_app_by_access_key_id(
            access_key_id=access_key_id, **kwargs
        )
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def list_applications(self, **kwargs) -> List[ExtendedConductorApplication]:
        return self._application_api.list_applications(**kwargs)

    def update_application(
        self,
        create_or_update_application_request: CreateOrUpdateApplicationRequest,
        application_id: str,
        **kwargs,
    ) -> ConductorApplication:
        app_obj = self._application_api.update_application(
            body=create_or_update_application_request, id=application_id, **kwargs
        )
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def delete_application(self, application_id: str, **kwargs) -> None:
        self._application_api.delete_application(id=application_id, **kwargs)

    def add_role_to_application_user(self, application_id: str, role: str, **kwargs) -> None:
        self._application_api.add_role_to_application_user(
            application_id=application_id, role=role, **kwargs
        )

    def remove_role_from_application_user(self, application_id: str, role: str, **kwargs) -> None:
        self._application_api.remove_role_from_application_user(
            application_id=application_id, role=role, **kwargs
        )

    def set_application_tags(self, tags: List[MetadataTag], application_id: str, **kwargs) -> None:
        self._application_api.put_tag_for_application(tag=tags, id=application_id, **kwargs)

    def get_application_tags(self, application_id: str, **kwargs) -> List[MetadataTag]:
        return self._application_api.get_tags_for_application(
            application_id=application_id, **kwargs
        )

    def delete_application_tags(
        self, tags: List[MetadataTag], application_id: str, **kwargs
    ) -> None:
        self._application_api.delete_tag_for_application(tag=tags, id=application_id, **kwargs)

    def create_access_key(self, application_id: str, **kwargs) -> CreatedAccessKey:
        key_obj = self._application_api.create_access_key(id=application_id, **kwargs)

        key_obj_dict = cast(Dict[str, Any], key_obj)
        result_model = CreatedAccessKey.from_dict(key_obj_dict)

        return result_model

    def get_access_keys(self, application_id: str, **kwargs) -> List[AccessKey]:
        access_keys_obj = self._application_api.get_access_keys(id=application_id, **kwargs)

        access_keys_dict = cast(List[Dict[str, Any]], access_keys_obj)
        result_model = [AccessKey.from_dict(_item) for _item in access_keys_dict]

        return result_model

    def toggle_access_key_status(self, application_id: str, key_id: str, **kwargs) -> AccessKey:
        key_obj = self._application_api.toggle_access_key_status(
            application_id=application_id, key_id=key_id, **kwargs
        )

        key_obj_dict = cast(Dict[str, Any], key_obj)
        result_model = AccessKey.from_dict(key_obj_dict)

        return result_model

    def delete_access_key(self, application_id: str, key_id: str, **kwargs) -> None:
        self._application_api.delete_access_key(
            application_id=application_id, key_id=key_id, **kwargs
        )

    # Users
    def upsert_user(
        self, upsert_user_request: UpsertUserRequest, user_id: str, **kwargs
    ) -> ConductorUser:
        user_obj = self._user_api.upsert_user(
            upsert_user_request=upsert_user_request, id=user_id, **kwargs
        )
        return self.api_client.deserialize_class(user_obj, "ConductorUser")

    def get_user(self, user_id: str, **kwargs) -> ConductorUser:
        user_obj = self._user_api.get_user(id=user_id, **kwargs)
        return self.api_client.deserialize_class(user_obj, "ConductorUser")

    def list_users(self, apps: Optional[bool] = False, **kwargs) -> List[ConductorUser]:
        kwargs["apps"] = apps
        return self._user_api.list_users(**kwargs)

    def delete_user(self, user_id: str, **kwargs) -> None:
        self._user_api.delete_user(id=user_id, **kwargs)

    # Groups
    def upsert_group(
        self, upsert_group_request: UpsertGroupRequest, group_id: str, **kwargs
    ) -> Group:
        group_obj = self._group_api.upsert_group(body=upsert_group_request, id=group_id, **kwargs)
        return self.api_client.deserialize_class(group_obj, "Group")

    def get_group(self, group_id: str, **kwargs) -> Group:
        group_obj = self._group_api.get_group(id=group_id, **kwargs)
        return self.api_client.deserialize_class(group_obj, "Group")

    def list_groups(self, **kwargs) -> List[Group]:
        return self._group_api.list_groups(**kwargs)

    def delete_group(self, group_id: str, **kwargs) -> None:
        self._group_api.delete_group(id=group_id, **kwargs)

    def add_user_to_group(self, group_id: str, user_id: str, **kwargs) -> None:
        self._group_api.add_user_to_group(group_id=group_id, user_id=user_id, **kwargs)

    def get_users_in_group(self, group_id: str, **kwargs) -> List[ConductorUser]:
        user_objs = self._group_api.get_users_in_group(id=group_id, **kwargs)
        group_users: List[ConductorUser] = []
        for u in user_objs:
            c_user = self.api_client.deserialize_class(u, "ConductorUser")
            group_users.append(c_user)

        return group_users

    def remove_user_from_group(self, group_id: str, user_id: str, **kwargs) -> None:
        self._group_api.remove_user_from_group(group_id=group_id, user_id=user_id, **kwargs)

    # Permissions

    def grant_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType]
    ) -> None:
        req = AuthorizationRequest(subject, target, access)
        self._authorization_api.grant_permissions(body=req)

    def get_permissions(self, target: TargetRef, **kwargs) -> Dict[str, List[SubjectRef]]:
        resp_obj = self._authorization_api.get_permissions(
            type=target.type.name, id=target.id, **kwargs
        )
        permissions: Dict[str, List[SubjectRef]] = {}

        for access_type, subjects in resp_obj.items():
            subject_list = [SubjectRef(sub["id"], sub["type"]) for sub in subjects]
            permissions[access_type] = subject_list

        return permissions

    def get_granted_permissions_for_group(self, group_id: str, **kwargs) -> List[GrantedPermission]:
        granted_access_obj = self._group_api.get_granted_permissions1(group_id=group_id, **kwargs)
        granted_permissions: List[GrantedPermission] = []

        for ga in granted_access_obj.granted_access:
            target = TargetRef(ga.target.id, ga.target.type)
            access = ga.access
            granted_permissions.append(GrantedPermission(target, access))

        return granted_permissions

    def get_granted_permissions_for_user(self, user_id: str, **kwargs) -> List[GrantedPermission]:
        granted_access_obj = self._user_api.get_granted_permissions(user_id=user_id, **kwargs)
        granted_permissions = []
        for ga in granted_access_obj["grantedAccess"]:
            target = TargetRef(ga["target"]["id"], ga["target"]["type"])
            access = ga["access"]
            granted_permissions.append(GrantedPermission(target, access))
        return granted_permissions

    def remove_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType], **kwargs
    ) -> None:
        req = AuthorizationRequest(subject, target, access)
        self._authorization_api.remove_permissions(body=req, **kwargs)

    def add_users_to_group(self, body: List[str], group_id: str, **kwargs) -> None:
        self._group_api.add_users_to_group(body=body, group_id=group_id, **kwargs)

    def remove_users_from_group(self, body: List[str], group_id: str, **kwargs) -> None:
        self._group_api.remove_users_from_group(body=body, group_id=group_id, **kwargs)

    def check_permissions(self, user_id: str, type: str, id: str, **kwargs) -> Dict[str, bool]:
        result = self._user_api.check_permissions(user_id=user_id, type=type, id=id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = {k: v for k, v in result_dict.items() if isinstance(v, bool)}

        return result_model
