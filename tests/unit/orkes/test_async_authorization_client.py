import logging

import pytest

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.api.application_resource_api import (
    ApplicationResourceApiAdapter,
)
from conductor.asyncio_client.adapters.api.authorization_resource_api import (
    AuthorizationResourceApiAdapter,
)
from conductor.asyncio_client.adapters.api.group_resource_api import (
    GroupResourceApiAdapter,
)
from conductor.asyncio_client.adapters.api.user_resource_api import (
    UserResourceApiAdapter,
)
from conductor.asyncio_client.adapters.models.authorization_request_adapter import (
    AuthorizationRequestAdapter,
)
from conductor.asyncio_client.adapters.models.conductor_user_adapter import (
    ConductorUserAdapter,
)
from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import (
    ExtendedConductorApplicationAdapter,
)
from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter
from conductor.asyncio_client.adapters.models.permission_adapter import (
    PermissionAdapter,
)
from conductor.asyncio_client.adapters.models.role_adapter import RoleAdapter
from conductor.asyncio_client.adapters.models.subject_ref_adapter import (
    SubjectRefAdapter,
)
from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter
from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import (
    UpsertGroupRequestAdapter,
)
from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import (
    UpsertUserRequestAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_authorization_client import (
    OrkesAuthorizationClient,
)
from conductor.shared.http.enums import SubjectType, TargetType

APP_ID = "5d860b70-a429-4b20-8d28-6b5198155882"
APP_NAME = "ut_application_name"
USER_ID = "us_user@orkes.io"
USER_UUID = "ac8b5803-c391-4237-8d3d-90f74b07d5ad"
USER_NAME = "UT USER"
GROUP_ID = "ut_group"
GROUP_NAME = "Test Group"
WF_NAME = "workflow_name"


@pytest.fixture(scope="module")
def authorization_client():
    configuration = Configuration("http://localhost:8080/api")
    api_client = ApiClient(configuration)
    return OrkesAuthorizationClient(configuration, api_client=api_client)


@pytest.fixture(scope="module")
def conductor_application():
    return ExtendedConductorApplicationAdapter(
        id=APP_ID,
        name=APP_NAME,
        created_by=USER_ID,
        create_time=1699236095031,
        update_time=1699236095031,
        updated_by=USER_ID,
    )


@pytest.fixture(scope="module")
def extended_conductor_application_adapter():
    return ExtendedConductorApplicationAdapter(
        id=APP_ID,
        name=APP_NAME,
        created_by=USER_ID,
        create_time=1699236095031,
        update_time=1699236095031,
        updated_by=USER_ID,
    )


@pytest.fixture(scope="module")
def roles():
    return [
        RoleAdapter(
            name="USER",
            permissions=[
                PermissionAdapter(name="METADATA_MANAGEMENT"),
                PermissionAdapter(name="WORKFLOW_MANAGEMENT"),
                PermissionAdapter(name="METADATA_VIEW"),
            ],
        )
    ]


@pytest.fixture(scope="module")
def conductor_user(roles):
    return ConductorUserAdapter(
        id=USER_ID,
        name=USER_NAME,
        uuid=USER_UUID,
        roles=roles,
        application_user=False,
        encrypted_id=False,
        encrypted_id_display_value=USER_ID,
    )


@pytest.fixture(scope="module")
def conductor_user_adapter(roles):
    return ConductorUserAdapter(
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
        RoleAdapter(
            name="USER",
            permissions=[
                PermissionAdapter(name="CREATE_TASK_DEF"),
                PermissionAdapter(name="CREATE_WORKFLOW_DEF"),
                PermissionAdapter(name="WORKFLOW_SEARCH"),
            ],
        )
    ]


@pytest.fixture(scope="module")
def group_adapter(group_roles):
    return GroupAdapter(id=GROUP_ID, description=GROUP_NAME, roles=group_roles)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def test_init(authorization_client):
    message = "application_api is not of type ApplicationResourceApi"
    assert isinstance(authorization_client._application_api, ApplicationResourceApiAdapter), message
    message = "user_api is not of type UserResourceApi"
    assert isinstance(authorization_client._user_api, UserResourceApiAdapter), message
    message = "group_api is not of type GroupResourceApi"
    assert isinstance(authorization_client._group_api, GroupResourceApiAdapter), message
    message = "authorization_api is not of type AuthorizationResourceApi"
    assert isinstance(authorization_client._authorization_api, AuthorizationResourceApiAdapter), (
        message
    )


@pytest.mark.asyncio
async def test_create_application(
    mocker, authorization_client, extended_conductor_application_adapter
):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "create_application")
    mock.return_value = extended_conductor_application_adapter
    app = await authorization_client.create_application(extended_conductor_application_adapter)
    mock.assert_called_with(
        create_or_update_application_request=extended_conductor_application_adapter
    )
    assert app == extended_conductor_application_adapter


@pytest.mark.asyncio
async def test_get_application(
    mocker, authorization_client, extended_conductor_application_adapter
):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "get_application")
    mock.return_value = extended_conductor_application_adapter
    app = await authorization_client.get_application(APP_ID)
    mock.assert_called_with(id=APP_ID)
    assert app == extended_conductor_application_adapter


@pytest.mark.asyncio
async def test_list_applications(
    mocker, authorization_client, extended_conductor_application_adapter
):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "list_applications")
    mock.return_value = [extended_conductor_application_adapter]
    app_names = await authorization_client.list_applications()
    assert mock.called
    assert app_names == [extended_conductor_application_adapter]


@pytest.mark.asyncio
async def test_delete_application(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "delete_application")
    await authorization_client.delete_application(APP_ID)
    mock.assert_called_with(id=APP_ID)


@pytest.mark.asyncio
async def test_update_application(
    mocker, authorization_client, extended_conductor_application_adapter
):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "update_application")
    mock.return_value = extended_conductor_application_adapter
    app = await authorization_client.update_application(
        APP_ID, extended_conductor_application_adapter
    )
    assert app == extended_conductor_application_adapter
    mock.assert_called_with(
        id=APP_ID,
        create_or_update_application_request=extended_conductor_application_adapter,
    )


@pytest.mark.asyncio
async def test_create_user(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "upsert_user")
    upsert_req = UpsertUserRequestAdapter(name=USER_NAME, roles=["ADMIN"])
    mock.return_value = conductor_user_adapter
    user = await authorization_client.create_user(USER_ID, upsert_req)
    mock.assert_called_with(id=USER_ID, upsert_user_request=upsert_req)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID


@pytest.mark.asyncio
async def test_update_user(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "upsert_user")
    upsert_req = UpsertUserRequestAdapter(name=USER_NAME, roles=["ADMIN"])
    mock.return_value = conductor_user_adapter
    user = await authorization_client.update_user(USER_ID, upsert_req)
    mock.assert_called_with(id=USER_ID, upsert_user_request=upsert_req)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID


@pytest.mark.asyncio
async def test_get_user(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "get_user")
    mock.return_value = conductor_user_adapter
    user = await authorization_client.get_user(USER_ID)
    mock.assert_called_with(id=USER_ID)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID


@pytest.mark.asyncio
async def test_get_user_with_empty_string(mocker, authorization_client, conductor_user_adapter):
    from conductor.asyncio_client.http.api import UserResourceApi
    mock = mocker.patch.object(UserResourceApi, "get_user")
    mock.return_value = conductor_user_adapter
    await authorization_client.get_user("")
    mock.assert_called_with(None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_delete_user(mocker, authorization_client):
    mock = mocker.patch.object(UserResourceApiAdapter, "delete_user")
    await authorization_client.delete_user(USER_ID)
    mock.assert_called_with(id=USER_ID)


@pytest.mark.asyncio
async def test_delete_user_with_empty_string(mocker, authorization_client):
    from conductor.asyncio_client.http.api import UserResourceApi
    mock = mocker.patch.object(UserResourceApi, "delete_user")
    await authorization_client.delete_user("")
    mock.assert_called_with(None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_list_users_with_apps(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "list_users")
    mock.return_value = [conductor_user_adapter]
    users = await authorization_client.list_users(include_apps=True)
    mock.assert_called_with(apps=True)
    assert users == [conductor_user_adapter]


@pytest.mark.asyncio
async def test_list_users(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "list_users")
    mock.return_value = [conductor_user_adapter]
    users = await authorization_client.list_users()
    mock.assert_called_with(apps=False)
    assert users == [conductor_user_adapter]


@pytest.mark.asyncio
async def test_upsert_user(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "upsert_user")
    upsert_req = UpsertUserRequestAdapter(name=USER_NAME, roles=["ADMIN"])
    mock.return_value = conductor_user_adapter
    user = await authorization_client.upsert_user(USER_ID, upsert_req)
    mock.assert_called_with(id=USER_ID, upsert_user_request=upsert_req)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID


@pytest.mark.asyncio
async def test_upsert_user_with_empty_string(mocker, authorization_client, conductor_user_adapter):
    from conductor.asyncio_client.http.api import UserResourceApi
    mock = mocker.patch.object(UserResourceApi, "upsert_user")
    upsert_req = UpsertUserRequestAdapter(name=USER_NAME, roles=["ADMIN"])
    mock.return_value = conductor_user_adapter
    await authorization_client.upsert_user("", upsert_req)
    mock.assert_called_with(None, upsert_req, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_create_group(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "upsert_group")
    upsert_req = UpsertGroupRequestAdapter(description=GROUP_NAME, roles=["USER"])
    mock.return_value = group_adapter
    group = await authorization_client.create_group(GROUP_ID, upsert_req)
    mock.assert_called_with(id=GROUP_ID, upsert_group_request=upsert_req)
    assert group == group_adapter
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID


@pytest.mark.asyncio
async def test_update_group(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "upsert_group")
    upsert_req = UpsertGroupRequestAdapter(description=GROUP_NAME, roles=["USER"])
    mock.return_value = group_adapter
    group = await authorization_client.update_group(GROUP_ID, upsert_req)
    mock.assert_called_with(id=GROUP_ID, upsert_group_request=upsert_req)
    assert group == group_adapter
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID


@pytest.mark.asyncio
async def test_get_group(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "get_group")
    mock.return_value = group_adapter
    group = await authorization_client.get_group(GROUP_ID)
    mock.assert_called_with(id=GROUP_ID)
    assert group == group_adapter
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID


@pytest.mark.asyncio
async def test_list_groups(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "list_groups")
    mock.return_value = [group_adapter]
    groups = await authorization_client.list_groups()
    assert mock.called
    assert groups == [group_adapter]


@pytest.mark.asyncio
async def test_delete_group(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApiAdapter, "delete_group")
    await authorization_client.delete_group(GROUP_ID)
    mock.assert_called_with(id=GROUP_ID)


@pytest.mark.asyncio
async def test_upsert_group(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "upsert_group")
    upsert_req = UpsertGroupRequestAdapter(description=GROUP_NAME, roles=["USER"])
    mock.return_value = group_adapter
    group = await authorization_client.upsert_group(GROUP_ID, upsert_req)
    mock.assert_called_with(id=GROUP_ID, upsert_group_request=upsert_req)
    assert group == group_adapter
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID


@pytest.mark.asyncio
async def test_add_user_to_group(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "add_user_to_group")
    mock.return_value = group_adapter
    await authorization_client.add_user_to_group(GROUP_ID, USER_ID)
    mock.assert_called_with(group_id=GROUP_ID, user_id=USER_ID)


@pytest.mark.asyncio
async def test_remove_user_from_group(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApiAdapter, "remove_user_from_group")
    await authorization_client.remove_user_from_group(GROUP_ID, USER_ID)
    mock.assert_called_with(group_id=GROUP_ID, user_id=USER_ID)


@pytest.mark.asyncio
async def test_add_users_to_group(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApiAdapter, "add_users_to_group")
    user_ids = [USER_ID, "user2@orkes.io"]
    await authorization_client.add_users_to_group(GROUP_ID, user_ids)
    mock.assert_called_with(group_id=GROUP_ID, request_body=user_ids)


@pytest.mark.asyncio
async def test_remove_users_from_group(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApiAdapter, "remove_users_from_group")
    user_ids = [USER_ID, "user2@orkes.io"]
    await authorization_client.remove_users_from_group(GROUP_ID, user_ids)
    mock.assert_called_with(group_id=GROUP_ID, request_body=user_ids)


@pytest.mark.asyncio
async def test_get_users_in_group(mocker, authorization_client, conductor_user_adapter, roles):
    mock = mocker.patch.object(GroupResourceApiAdapter, "get_users_in_group")
    mock.return_value = [conductor_user_adapter]
    users = await authorization_client.get_users_in_group(GROUP_ID)
    mock.assert_called_with(id=GROUP_ID)
    assert users == [conductor_user_adapter]


@pytest.mark.asyncio
async def test_grant_permissions(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApiAdapter, "grant_permissions")
    auth_request = AuthorizationRequestAdapter(
        subject=SubjectRefAdapter(type=SubjectType.USER, id=USER_ID),
        target=TargetRefAdapter(type=TargetType.WORKFLOW_DEF, id=WF_NAME),
        access=["READ", "EXECUTE"],
    )
    await authorization_client.grant_permissions(auth_request)
    mock.assert_called_with(authorization_request=auth_request)


@pytest.mark.asyncio
async def test_remove_permissions(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApiAdapter, "remove_permissions")
    auth_request = AuthorizationRequestAdapter(
        subject=SubjectRefAdapter(type=SubjectType.USER, id=USER_ID),
        target=TargetRefAdapter(type=TargetType.WORKFLOW_DEF, id=WF_NAME),
        access=["READ", "EXECUTE"],
    )
    await authorization_client.remove_permissions(auth_request)
    mock.assert_called_with(authorization_request=auth_request)


@pytest.mark.asyncio
async def test_get_permissions(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApiAdapter, "get_permissions")
    mock.return_value = {
        "EXECUTE": [
            {"type": "USER", "id": USER_ID},
        ],
        "READ": [
            {"type": "USER", "id": USER_ID},
            {"type": "GROUP", "id": GROUP_ID},
        ],
    }
    permissions = await authorization_client.get_permissions("USER", USER_ID)
    mock.assert_called_with(type="USER", id=USER_ID)
    assert permissions == {
        "EXECUTE": [
            {"type": "USER", "id": USER_ID},
        ],
        "READ": [
            {"type": "USER", "id": USER_ID},
            {"type": "GROUP", "id": GROUP_ID},
        ],
    }


@pytest.mark.asyncio
async def test_get_group_permissions(mocker, authorization_client: OrkesAuthorizationClient):
    mock = mocker.patch.object(GroupResourceApiAdapter, "get_granted_permissions1")
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
    perms = await authorization_client.get_group_permissions(GROUP_ID)
    mock.assert_called_with(group_id=GROUP_ID)
    assert perms == {
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


@pytest.mark.asyncio
async def test_get_granted_permissions_for_user_with_empty_string(mocker, authorization_client):
    from conductor.asyncio_client.http.api import UserResourceApi
    mock = mocker.patch.object(UserResourceApi, "get_granted_permissions")
    mock.return_value = {"grantedAccess": []}
    await authorization_client.get_granted_permissions_for_user("")
    mock.assert_called_with(None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_create_access_key_empty_string_converts_to_none(mocker, authorization_client):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "create_access_key")
    mock.return_value = {
        "id": "test-key-id",
        "secret": "test-secret",
    }
    await authorization_client.create_access_key("")
    mock.assert_called_with(None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_add_role_to_application_user_empty_strings_convert_to_none(
    mocker, authorization_client
):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "add_role_to_application_user")
    await authorization_client.add_role_to_application_user("", "")
    mock.assert_called_with(None, None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_delete_access_key_empty_strings_convert_to_none(mocker, authorization_client):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "delete_access_key")
    await authorization_client.delete_access_key("", "")
    mock.assert_called_with(None, None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_remove_role_from_application_user_empty_strings_convert_to_none(
    mocker, authorization_client
):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "remove_role_from_application_user")
    await authorization_client.remove_role_from_application_user("", "")
    mock.assert_called_with(None, None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_get_app_by_access_key_id_empty_string_converts_to_none(
    mocker, authorization_client, extended_conductor_application_adapter
):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "get_app_by_access_key_id")
    mock.return_value = extended_conductor_application_adapter
    await authorization_client.get_app_by_access_key_id("")
    mock.assert_called_with(None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_get_access_keys_empty_string_converts_to_none(mocker, authorization_client):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "get_access_keys")
    mock.return_value = []
    await authorization_client.get_access_keys("")
    mock.assert_called_with(None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_toggle_access_key_status_empty_strings_convert_to_none(mocker, authorization_client):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "toggle_access_key_status")
    mock.return_value = {
        "id": "test-key-id",
        "createdAt": 1698926045112,
        "status": "INACTIVE",
    }
    await authorization_client.toggle_access_key_status("", "")
    mock.assert_called_with(None, None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_get_tags_for_application_empty_string_converts_to_none(mocker, authorization_client):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "get_tags_for_application")
    mock.return_value = []
    await authorization_client.get_application_tags("")
    mock.assert_called_with(None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_delete_tag_for_application_empty_strings_convert_to_none(
    mocker, authorization_client
):
    from conductor.asyncio_client.http.api.application_resource_api import (
        ApplicationResourceApi,
    )

    mock = mocker.patch.object(ApplicationResourceApi, "delete_tag_for_application")
    await authorization_client.delete_application_tags([], "")
    mock.assert_called_with(None, None, _request_timeout=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)


@pytest.mark.asyncio
async def test_create_user_validated(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "upsert_user")
    upsert_req = UpsertUserRequestAdapter(name=USER_NAME, roles=["ADMIN"])
    user_dict = {
        "id": USER_ID,
        "name": USER_NAME,
        "uuid": USER_UUID,
        "roles": [{"name": "USER", "permissions": []}],
        "applicationUser": False,
        "encryptedId": False,
        "encryptedIdDisplayValue": USER_ID,
    }
    mock.return_value = user_dict
    user = await authorization_client.create_user_validated(USER_ID, upsert_req)
    mock.assert_called_with(id=USER_ID, upsert_user_request=upsert_req)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID


@pytest.mark.asyncio
async def test_update_user_validated(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "upsert_user")
    upsert_req = UpsertUserRequestAdapter(name=USER_NAME, roles=["ADMIN"])
    user_dict = {
        "id": USER_ID,
        "name": USER_NAME,
        "uuid": USER_UUID,
        "roles": [{"name": "USER", "permissions": []}],
        "applicationUser": False,
        "encryptedId": False,
        "encryptedIdDisplayValue": USER_ID,
    }
    mock.return_value = user_dict
    user = await authorization_client.update_user_validated(USER_ID, upsert_req)
    mock.assert_called_with(id=USER_ID, upsert_user_request=upsert_req)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID


@pytest.mark.asyncio
async def test_get_user_validated(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(UserResourceApiAdapter, "get_user")
    user_dict = {
        "id": USER_ID,
        "name": USER_NAME,
        "uuid": USER_UUID,
        "roles": [{"name": "USER", "permissions": []}],
        "applicationUser": False,
        "encryptedId": False,
        "encryptedIdDisplayValue": USER_ID,
    }
    mock.return_value = user_dict
    user = await authorization_client.get_user(USER_ID)
    mock.assert_called_with(id=USER_ID)
    assert user.name == USER_NAME
    assert user.id == USER_ID
    assert user.uuid == USER_UUID


@pytest.mark.asyncio
async def test_get_user_permissions(mocker, authorization_client):
    mock = mocker.patch.object(UserResourceApiAdapter, "get_granted_permissions")
    permissions_dict = {
        "grantedAccess": [
            {
                "target": {"type": "WORKFLOW_DEF", "id": WF_NAME},
                "access": ["EXECUTE", "READ"],
            }
        ]
    }
    mock.return_value = permissions_dict
    result = await authorization_client.get_user_permissions(USER_ID)
    mock.assert_called_with(USER_ID)
    assert result.granted_access is not None
    assert len(result.granted_access) == 1


@pytest.mark.asyncio
async def test_create_application_validated(mocker, authorization_client, extended_conductor_application_adapter):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "create_application")
    app_dict = {
        "id": APP_ID,
        "name": APP_NAME,
        "createdBy": USER_ID,
        "createTime": 1699236095031,
        "updateTime": 1699236095031,
        "updatedBy": USER_ID,
    }
    mock.return_value = app_dict
    app = await authorization_client.create_application(extended_conductor_application_adapter)
    mock.assert_called_with(create_or_update_application_request=extended_conductor_application_adapter)
    assert app.name == APP_NAME
    assert app.id == APP_ID


@pytest.mark.asyncio
async def test_update_application_validated(mocker, authorization_client, extended_conductor_application_adapter):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "update_application")
    app_dict = {
        "id": APP_ID,
        "name": APP_NAME,
        "createdBy": USER_ID,
        "createTime": 1699236095031,
        "updateTime": 1699236095031,
        "updatedBy": USER_ID,
    }
    mock.return_value = app_dict
    app = await authorization_client.update_application(APP_ID, extended_conductor_application_adapter)
    mock.assert_called_with(id=APP_ID, create_or_update_application_request=extended_conductor_application_adapter)
    assert app.name == APP_NAME
    assert app.id == APP_ID


@pytest.mark.asyncio
async def test_get_application_validated(mocker, authorization_client, extended_conductor_application_adapter):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "get_application")
    app_dict = {
        "id": APP_ID,
        "name": APP_NAME,
        "createdBy": USER_ID,
        "createTime": 1699236095031,
        "updateTime": 1699236095031,
        "updatedBy": USER_ID,
    }
    mock.return_value = app_dict
    app = await authorization_client.get_application(APP_ID)
    mock.assert_called_with(id=APP_ID)
    assert app.name == APP_NAME
    assert app.id == APP_ID


@pytest.mark.asyncio
async def test_create_group_validated(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "upsert_group")
    upsert_req = UpsertGroupRequestAdapter(description=GROUP_NAME, roles=["USER"])
    group_dict = {
        "id": GROUP_ID,
        "description": GROUP_NAME,
        "roles": [{"name": "USER", "permissions": []}],
    }
    mock.return_value = group_dict
    group = await authorization_client.create_group_validated(GROUP_ID, upsert_req)
    mock.assert_called_with(id=GROUP_ID, upsert_group_request=upsert_req)
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID


@pytest.mark.asyncio
async def test_get_group_validated(mocker, authorization_client, group_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "get_group")
    group_dict = {
        "id": GROUP_ID,
        "description": GROUP_NAME,
        "roles": [{"name": "USER", "permissions": []}],
    }
    mock.return_value = group_dict
    group = await authorization_client.get_group(GROUP_ID)
    mock.assert_called_with(id=GROUP_ID)
    assert group.description == GROUP_NAME
    assert group.id == GROUP_ID


@pytest.mark.asyncio
async def test_add_user_to_group_validated(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApiAdapter, "add_user_to_group")
    await authorization_client.add_user_to_group_validated(GROUP_ID, USER_ID)
    mock.assert_called_with(group_id=GROUP_ID, user_id=USER_ID)


@pytest.mark.asyncio
async def test_remove_user_from_group_validated(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApiAdapter, "remove_user_from_group")
    await authorization_client.remove_user_from_group_validated(GROUP_ID, USER_ID)
    mock.assert_called_with(group_id=GROUP_ID, user_id=USER_ID)


@pytest.mark.asyncio
async def test_add_users_to_group_validated(mocker, authorization_client):
    mock = mocker.patch.object(GroupResourceApiAdapter, "add_users_to_group")
    user_ids = [USER_ID, "user2@orkes.io"]
    await authorization_client.add_users_to_group_validated(GROUP_ID, user_ids)
    mock.assert_called_with(group_id=GROUP_ID, request_body=user_ids)


@pytest.mark.asyncio
async def test_get_users_in_group_validated(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(GroupResourceApiAdapter, "get_users_in_group")
    user_dict = {
        "id": USER_ID,
        "name": USER_NAME,
        "uuid": USER_UUID,
        "roles": [{"name": "USER", "permissions": []}],
        "applicationUser": False,
        "encryptedId": False,
        "encryptedIdDisplayValue": USER_ID,
    }
    mock.return_value = [user_dict]
    users = await authorization_client.get_users_in_group_validated(GROUP_ID)
    mock.assert_called_with(id=GROUP_ID)
    assert len(users) == 1
    assert users[0].name == USER_NAME
    assert users[0].id == USER_ID


@pytest.mark.asyncio
async def test_grant_permissions_validated(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApiAdapter, "grant_permissions")
    auth_request = AuthorizationRequestAdapter(
        subject=SubjectRefAdapter(type=SubjectType.USER, id=USER_ID),
        target=TargetRefAdapter(type=TargetType.WORKFLOW_DEF, id=WF_NAME),
        access=["READ", "EXECUTE"],
    )
    await authorization_client.grant_permissions_validated(auth_request)
    mock.assert_called_with(authorization_request=auth_request)


@pytest.mark.asyncio
async def test_remove_permissions_validated(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApiAdapter, "remove_permissions")
    auth_request = AuthorizationRequestAdapter(
        subject=SubjectRefAdapter(type=SubjectType.USER, id=USER_ID),
        target=TargetRefAdapter(type=TargetType.WORKFLOW_DEF, id=WF_NAME),
        access=["READ", "EXECUTE"],
    )
    await authorization_client.remove_permissions_validated(auth_request)
    mock.assert_called_with(authorization_request=auth_request)


@pytest.mark.asyncio
async def test_get_permissions_validated(mocker, authorization_client):
    mock = mocker.patch.object(AuthorizationResourceApiAdapter, "get_permissions")
    mock.return_value = {
        "EXECUTE": [
            {"type": "USER", "id": USER_ID},
        ],
        "READ": [
            {"type": "USER", "id": USER_ID},
            {"type": "GROUP", "id": GROUP_ID},
        ],
    }
    target = TargetRefAdapter(type=TargetType.WORKFLOW_DEF, id=WF_NAME)
    permissions = await authorization_client.get_permissions_validated(target)
    mock.assert_called_with(type=TargetType.WORKFLOW_DEF, id=WF_NAME)
    assert "EXECUTE" in permissions
    assert "READ" in permissions
    assert len(permissions["EXECUTE"]) == 1
    assert len(permissions["READ"]) == 2
    assert permissions["EXECUTE"][0].id == USER_ID
    assert permissions["READ"][0].id == USER_ID
    assert permissions["READ"][1].id == GROUP_ID


@pytest.mark.asyncio
async def test_upsert_user_validated(mocker, authorization_client, conductor_user_adapter):
    mock = mocker.patch.object(authorization_client, "create_user_validated")
    upsert_req = UpsertUserRequestAdapter(name=USER_NAME, roles=["ADMIN"])
    mock.return_value = conductor_user_adapter
    user = await authorization_client.upsert_user(USER_ID, upsert_req)
    mock.assert_called_with(USER_ID, upsert_req)
    assert user == conductor_user_adapter


@pytest.mark.asyncio
async def test_create_access_key_validated(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "create_access_key")
    key_dict = {
        "id": "test-key-id",
        "secret": "test-secret",
    }
    mock.return_value = key_dict
    key = await authorization_client.create_access_key_validated(APP_ID)
    mock.assert_called_with(id=APP_ID)
    assert key.id == "test-key-id"
    assert key.secret == "test-secret"


@pytest.mark.asyncio
async def test_get_access_keys_validated(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "get_access_keys")
    keys_list = [
        {"id": "key1", "createdAt": 1698926045112, "status": "ACTIVE"},
        {"id": "key2", "createdAt": 1699100552620, "status": "ACTIVE"},
    ]
    mock.return_value = keys_list
    keys = await authorization_client.get_access_keys_validated(APP_ID)
    mock.assert_called_with(APP_ID)
    assert len(keys) == 2
    assert keys[0].id == "key1"
    assert keys[1].id == "key2"


@pytest.mark.asyncio
async def test_toggle_access_key_status_validated(mocker, authorization_client):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "toggle_access_key_status")
    key_dict = {
        "id": "test-key-id",
        "createdAt": 1698926045112,
        "status": "INACTIVE",
    }
    mock.return_value = key_dict
    key = await authorization_client.toggle_access_key_status_validated(APP_ID, "test-key-id")
    mock.assert_called_with(application_id=APP_ID, key_id="test-key-id")
    assert key.id == "test-key-id"


@pytest.mark.asyncio
async def test_check_permissions(mocker, authorization_client):
    mock = mocker.patch.object(UserResourceApiAdapter, "check_permissions")
    permissions_result = {
        "READ": True,
        "EXECUTE": False,
        "UPDATE": True,
    }
    mock.return_value = permissions_result
    result = await authorization_client.check_permissions(USER_ID, "WORKFLOW_DEF", WF_NAME)
    mock.assert_called_with(user_id=USER_ID, type="WORKFLOW_DEF", id=WF_NAME)
    assert result["READ"] is True
    assert result["EXECUTE"] is False
    assert result["UPDATE"] is True
