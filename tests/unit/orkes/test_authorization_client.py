import logging
import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.application_resource_api import ApplicationResourceApi
from conductor.client.http.api.authorization_resource_api import AuthorizationResourceApi
from conductor.client.http.api.group_resource_api import GroupResourceApi
from conductor.client.http.api.user_resource_api import UserResourceApi
from conductor.client.http.models.authorization_request import AuthorizationRequest
from conductor.client.http.models.conductor_application import ConductorApplication
from conductor.client.http.models.conductor_user import ConductorUser
from conductor.client.http.models.create_or_update_application_request import (
    CreateOrUpdateApplicationRequest,
)
from conductor.client.http.models.group import Group
from conductor.client.http.models.permission import Permission
from conductor.client.http.models.role import Role
from conductor.client.http.models.subject_ref import SubjectRef, SubjectType
from conductor.client.http.models.target_ref import TargetRef, TargetType
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.orkes.models.access_key import AccessKey
from conductor.client.orkes.models.access_key_status import AccessKeyStatus
from conductor.client.orkes.models.access_type import AccessType
from conductor.client.orkes.models.created_access_key import CreatedAccessKey
from conductor.client.orkes.models.granted_permission import GrantedPermission
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient

APP_ID = "5d860b70-a429-4b20-8d28-6b5198155882"
APP_NAME = "ut_application_name"
ACCESS_KEY_ID = "9c32f5b2-128d-42bd-988f-083857f4c541"
ACCESS_KEY_ID_2 = "be41f18c-be18-4c68-9847-8fd91f3c21bc"
ACCESS_KEY_SECRET = "iSEONALN8Lz91uXraPBcyEau28luuOtMGnGA7mUSbJTZ76fb"
USER_ID = "us_user@orkes.io"
USER_UUID = "ac8b5803-c391-4237-8d3d-90f74b07d5ad"
USER_NAME = "UT USER"
GROUP_ID = "ut_group"
GROUP_NAME = "Test Group"
WF_NAME = "workflow_name"
ERROR_BODY = '{"message":"No such application found by id"}'


@pytest.fixture(scope="module")
def authorization_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesAuthorizationClient(configuration)


@pytest.fixture(scope="module")
def conductor_application():
    return ConductorApplication(
        APP_ID, APP_NAME, USER_ID, 1699236095031, 1699236095031, USER_ID
    )


@pytest.fixture(scope="module")
def access_key():
    return CreatedAccessKey(ACCESS_KEY_ID, ACCESS_KEY_SECRET)


@pytest.fixture(scope="module")
def app_keys():
    return [
        AccessKey(ACCESS_KEY_ID, AccessKeyStatus.ACTIVE, 1698926045112),
        AccessKey(ACCESS_KEY_ID_2, AccessKeyStatus.ACTIVE, 1699100552620),
    ]


@pytest.fixture(scope="module")
def roles():
    return [
        Role(
            "USER",
            [
                Permission(name="METADATA_MANAGEMENT"),
                Permission(name="WORKFLOW_MANAGEMENT"),
                Permission(name="METADATA_VIEW"),
            ],
        )
    ]


@pytest.fixture(scope="module")
def conductor_user(roles):
    return ConductorUser(
        id=USER_ID,
        name=USER_NAME,
        uuid=USER_UUID,
        roles=roles,
        application_user=False,
        encrypted_id=False,
        encrypted_id_display_value=USER_ID,
    )


@pytest.fixture(scope="module")
def group_roles():
    return [
        Role(
            "USER",
            [
                Permission(name="CREATE_TASK_DEF"),
                Permission(name="CREATE_WORKFLOW_DEF"),
                Permission(name="WORKFLOW_SEARCH"),
            ],
        )
    ]


@pytest.fixture(scope="module")
def conductor_group(group_roles):
    return Group(GROUP_ID, GROUP_NAME, group_roles)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def test_init(authorization_client):
    message = "applicationResourceApi is not of type ApplicationResourceApi"
    assert isinstance(
        authorization_client.applicationResourceApi, ApplicationResourceApi
    ), message
    message = "userResourceApi is not of type UserResourceApi"
    assert isinstance(
        authorization_client.userResourceApi, UserResourceApi
    ), message
    message = "groupResourceApi is not of type GroupResourceApi"
    assert isinstance(
        authorization_client.groupResourceApi, GroupResourceApi
    ), message
    message = "authorizationResourceApi is not of type AuthorizationResourceApi"
    assert isinstance(
        authorization_client.authorizationResourceApi, AuthorizationResourceApi
    ), message


def test_create_application(mocker, authorization_client, conductor_application):
    mock = mocker.patch.object(ApplicationResourceApi, "create_application")
    createReq = CreateOrUpdateApplicationRequest()
    mock.return_value = {
        "id": APP_ID,
        "name": APP_NAME,
        "createdBy": USER_ID,
        "updatedBy": USER_ID,
        "createTime": 1699236095031,
        "updateTime": 1699236095031,
    }
    app = authorization_client.create_application(createReq)
    mock.assert_called_with(createReq)
    assert app == conductor_application


def test_get_application(mocker, authorization_client, conductor_application):
    mock = mocker.patch.object(ApplicationResourceApi, "get_application")
    mock.return_value = {
        "id": APP_ID,
        "name": APP_NAME,
        "createdBy": USER_ID,
        "updatedBy": USER_ID,
        "createTime": 1699236095031,
        "updateTime": 1699236095031,
    }
    app = authorization_client.get_application(APP_ID)
    mock.assert_called_with(APP_ID)
    assert app == conductor_application


def test_list_applications(mocker, authorization_client, conductor_application):
    mock = mocker.patch.object(ApplicationResourceApi, "list_applications")
    mock.return_value = [conductor_application]
    app_names = authorization_client.list_applications()
    assert mock.called
    assert app_names == [conductor_application]


def test_delete_application(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApi, "delete_application")
    authorization_client.delete_application(APP_ID)
    mock.assert_called_with(APP_ID)


def test_update_application(mocker, authorization_client, conductor_application):
    mock = mocker.patch.object(ApplicationResourceApi, "update_application")
    updateReq = CreateOrUpdateApplicationRequest(APP_NAME)
    mock.return_value = {
        "id": APP_ID,
        "name": APP_NAME,
        "createdBy": USER_ID,
        "updatedBy": USER_ID,
        "createTime": 1699236095031,
        "updateTime": 1699236095031,
    }
    app = authorization_client.update_application(updateReq, APP_ID)
    assert app == conductor_application
    mock.assert_called_with(updateReq, APP_ID)


def test_add_role_to_application_user(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApi, "add_role_to_application_user")
    authorization_client.add_role_to_application_user(APP_ID, "USER")
    mock.assert_called_with(APP_ID, "USER")


def test_remove_role_from_application_user(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApi, "remove_role_from_application_user")
    authorization_client.remove_role_from_application_user(APP_ID, "USER")
    mock.assert_called_with(APP_ID, "USER")


def test_set_application_tags(mocker, authorization_client, conductor_application):
    mock = mocker.patch.object(ApplicationResourceApi, "put_tags_for_application")
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    tags = [tag1, tag2]
    authorization_client.set_application_tags(tags, APP_ID)
    mock.assert_called_with(tags, APP_ID)


def test_get_application_tags(mocker, authorization_client, conductor_application):
    mock = mocker.patch.object(ApplicationResourceApi, "get_tags_for_application")
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    mock.return_value = [tag1, tag2]
    tags = authorization_client.get_application_tags(APP_ID)
    mock.assert_called_with(APP_ID)
    assert len(tags) == 2


def test_delete_application_tags(mocker, authorization_client, conductor_application):
    mock = mocker.patch.object(ApplicationResourceApi, "delete_tags_for_application")
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    tags = [tag1, tag2]
    authorization_client.delete_application_tags(tags, APP_ID)
    mock.assert_called_with(tags, APP_ID)


def test_create_access_key(mocker, authorization_client, access_key):
    mock = mocker.patch.object(ApplicationResourceApi, "create_access_key")
    mock.return_value = {
        "id": ACCESS_KEY_ID,
        "secret": ACCESS_KEY_SECRET,
    }
    created_key = authorization_client.create_access_key(APP_ID)
    mock.assert_called_with(APP_ID)
    assert created_key == access_key


def test_get_access_keys(mocker, authorization_client, app_keys):
    mock = mocker.patch.object(ApplicationResourceApi, "get_access_keys")
    mock.return_value = [
        {
            "id": ACCESS_KEY_ID,
            "createdAt": 1698926045112,
            "status": "ACTIVE",
        },
        {
            "id": ACCESS_KEY_ID_2,
            "createdAt": 1699100552620,
            "status": "ACTIVE",
        },
    ]
    access_keys = authorization_client.get_access_keys(APP_ID)
    mock.assert_called_with(APP_ID)
    assert access_keys == app_keys


def test_toggle_access_key_status(mocker, authorization_client, access_key):
    mock = mocker.patch.object(ApplicationResourceApi, "toggle_access_key_status")
    mock.return_value = {
        "id": ACCESS_KEY_ID,
        "createdAt": 1698926045112,
        "status": "INACTIVE",
    }
    access_key = authorization_client.toggle_access_key_status(
        APP_ID, ACCESS_KEY_ID
    )
    mock.assert_called_with(APP_ID, ACCESS_KEY_ID)
    assert access_key.status == AccessKeyStatus.INACTIVE


def test_delete_access_key(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApi, "delete_access_key")
    authorization_client.delete_access_key(APP_ID, ACCESS_KEY_ID)
    mock.assert_called_with(APP_ID, ACCESS_KEY_ID)


def test_upsert_user(mocker, authorization_client, conductor_user, roles):
    mock = mocker.patch.object(UserResourceApi, "upsert_user")
    upsertReq = UpsertUserRequest(USER_NAME, ["ADMIN"])
    mock.return_value = conductor_user.to_dict()
    user = authorization_client.upsert_user(upsertReq, USER_ID)
    mock.assert_called_with(upsertReq, USER_ID)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID
    assert user.roles == roles


def test_get_user(mocker, authorization_client, conductor_user, roles):
    mock = mocker.patch.object(UserResourceApi, "get_user")
    mock.return_value = conductor_user.to_dict()
    user = authorization_client.get_user(USER_ID)
    mock.assert_called_with(USER_ID)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID
    assert user.roles == roles


def test_list_users_with_apps(mocker, authorization_client, conductor_user):
    mock = mocker.patch.object(UserResourceApi, "list_users")
    mock.return_value = [conductor_user]
    users = authorization_client.list_users(apps=True)
    mock.assert_called_with(apps=True)
    assert users == [conductor_user]


def test_list_users(mocker, authorization_client, conductor_user):
    mock = mocker.patch.object(UserResourceApi, "list_users")
    mock.return_value = [conductor_user]
    users = authorization_client.list_users()
    mock.assert_called_with(apps=False)
    assert users == [conductor_user]


def test_delete_user(mocker, authorization_client):
    mock = mocker.patch.object(UserResourceApi, "delete_user")
    authorization_client.delete_user(USER_ID)
    mock.assert_called_with(USER_ID)


def test_upsert_group(mocker, authorization_client, conductor_group, group_roles):
    mock = mocker.patch.object(GroupResourceApi, "upsert_group")
    upsertReq = UpsertGroupRequest(GROUP_NAME, ["USER"])
    mock.return_value = conductor_group.to_dict()
    group = authorization_client.upsert_group(upsertReq, GROUP_ID)
    mock.assert_called_with(upsertReq, GROUP_ID)
    assert group == conductor_group
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID
    assert group.roles == group_roles


def test_get_group(mocker, authorization_client, conductor_group, group_roles):
    mock = mocker.patch.object(GroupResourceApi, "get_group")
    mock.return_value = conductor_group.to_dict()
    group = authorization_client.get_group(GROUP_ID)
    mock.assert_called_with(GROUP_ID)
    assert group == conductor_group
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID
    assert group.roles == group_roles


def test_list_groups(mocker, authorization_client, conductor_group):
    mock = mocker.patch.object(GroupResourceApi, "list_groups")
    mock.return_value = [conductor_group]
    groups = authorization_client.list_groups()
    assert mock.called
    assert groups == [conductor_group]


def test_delete_group(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApi, "delete_group")
    authorization_client.delete_group(GROUP_ID)
    mock.assert_called_with(GROUP_ID)


def test_add_user_to_group(mocker, authorization_client, conductor_group):
    mock = mocker.patch.object(GroupResourceApi, "add_user_to_group")
    mock.return_value = conductor_group
    authorization_client.add_user_to_group(GROUP_ID, USER_ID)
    mock.assert_called_with(GROUP_ID, USER_ID)


def test_get_users_in_group(mocker, authorization_client, conductor_user, roles):
    mock = mocker.patch.object(GroupResourceApi, "get_users_in_group")
    mock.return_value = [conductor_user.to_dict()]
    users = authorization_client.get_users_in_group(GROUP_ID)
    mock.assert_called_with(GROUP_ID)
    assert len(users) == 1
    assert users[0].name == USER_NAME
    assert users[0].id == USER_ID
    assert users[0].uuid == USER_UUID
    assert users[0].roles == roles


def test_remove_user_from_group(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApi, "remove_user_from_group")
    authorization_client.remove_user_from_group(GROUP_ID, USER_ID)
    mock.assert_called_with(GROUP_ID, USER_ID)


def test_get_granted_permissions_for_group(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApi, "get_granted_permissions1")
    mock.return_value = {
        "grantedAccess": [
            {
                "target": {
                    "type": "WORKFLOW_DEF",
                    "id": WF_NAME,
                },
                "access": [
                    "EXECUTE",
                    "UPDATE",
                    "READ",
                ],
            }
        ]
    }
    perms = authorization_client.get_granted_permissions_for_group(GROUP_ID)
    mock.assert_called_with(GROUP_ID)
    expected_perm = GrantedPermission(
        target=TargetRef(TargetType.WORKFLOW_DEF, WF_NAME),
        access=["EXECUTE", "UPDATE", "READ"],
    )
    assert perms == [expected_perm]


def test_get_granted_permissions_for_user(mocker, authorization_client):
    mock = mocker.patch.object(UserResourceApi, "get_granted_permissions")
    mock.return_value = {
        "grantedAccess": [
            {
                "target": {
                    "type": "WORKFLOW_DEF",
                    "id": WF_NAME,
                },
                "access": [
                    "EXECUTE",
                    "UPDATE",
                    "READ",
                ],
            }
        ]
    }
    perms = authorization_client.get_granted_permissions_for_user(USER_ID)
    mock.assert_called_with(USER_ID)
    expected_perm = GrantedPermission(
        target=TargetRef(TargetType.WORKFLOW_DEF, WF_NAME),
        access=["EXECUTE", "UPDATE", "READ"],
    )
    assert perms == [expected_perm]


def test_get_permissions(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApi, "get_permissions")
    mock.return_value = {
        "EXECUTE": [
            {"type": "USER", "id": USER_ID},
        ],
        "READ": [
            {"type": "USER", "id": USER_ID},
            {"type": "GROUP", "id": GROUP_ID},
        ],
    }
    permissions = authorization_client.get_permissions(
        TargetRef(TargetType.WORKFLOW_DEF, WF_NAME)
    )
    mock.assert_called_with(TargetType.WORKFLOW_DEF.name, "workflow_name")
    expected_permissions_dict = {
        AccessType.EXECUTE.name: [
            SubjectRef(SubjectType.USER, USER_ID),
        ],
        AccessType.READ.name: [
            SubjectRef(SubjectType.USER, USER_ID),
            SubjectRef(SubjectType.GROUP, GROUP_ID),
        ],
    }
    assert permissions == expected_permissions_dict


def test_grant_permissions(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApi, "grant_permissions")
    subject = SubjectRef(SubjectType.USER, USER_ID)
    target = TargetRef(TargetType.WORKFLOW_DEF, WF_NAME)
    access = [AccessType.READ, AccessType.EXECUTE]
    authorization_client.grant_permissions(subject, target, access)
    mock.assert_called_with(AuthorizationRequest(subject, target, access))


def test_remove_permissions(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApi, "remove_permissions")
    subject = SubjectRef(SubjectType.USER, USER_ID)
    target = TargetRef(TargetType.WORKFLOW_DEF, WF_NAME)
    access = [AccessType.READ, AccessType.EXECUTE]
    authorization_client.remove_permissions(subject, target, access)
    mock.assert_called_with(AuthorizationRequest(subject, target, access))
