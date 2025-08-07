import logging

import pytest

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
    return OrkesAuthorizationClient(configuration)


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
    assert isinstance(
        authorization_client.application_api, ApplicationResourceApiAdapter
    ), message
    message = "user_api is not of type UserResourceApi"
    assert isinstance(authorization_client.user_api, UserResourceApiAdapter), message
    message = "group_api is not of type GroupResourceApi"
    assert isinstance(authorization_client.group_api, GroupResourceApiAdapter), message
    message = "authorization_api is not of type AuthorizationResourceApi"
    assert isinstance(
        authorization_client.authorization_api, AuthorizationResourceApiAdapter
    ), message


@pytest.mark.asyncio
async def test_create_application(
    mocker, authorization_client, extended_conductor_application_adapter
):
    mock = mocker.patch.object(ApplicationResourceApiAdapter, "create_application")
    mock.return_value = extended_conductor_application_adapter
    app = await authorization_client.create_application(
        extended_conductor_application_adapter
    )
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
async def test_delete_user(mocker, authorization_client):
    mock = mocker.patch.object(UserResourceApiAdapter, "delete_user")
    await authorization_client.delete_user(USER_ID)
    mock.assert_called_with(id=USER_ID)


@pytest.mark.asyncio
async def test_list_users_with_apps(
    mocker, authorization_client, conductor_user_adapter
):
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
async def test_get_users_in_group(
    mocker, authorization_client, conductor_user_adapter, roles
):
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
async def test_get_group_permissions(mocker, authorization_client):
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
