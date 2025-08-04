import asyncio
import logging

import pytest

from conductor.client.adapters.models import (
    CreateOrUpdateApplicationRequestAdapter,
    ExtendedConductorApplicationAdapter,
)
from conductor.client.my_aiohttp_client import Configuration
from conductor.client.my_aiohttp_client.models.tag import Tag
from conductor.client.orkes.async_orkes_base_client import AsyncOrkesBaseClient

APP_ID = "5d860b70-a429-4b20-8d28-6b5198155882"
APP_NAME = "ut_application_name"
ACCESS_KEY_ID = "9c32f5b2-128d-42bd-988f-083857f4c541"
KEY_ID = "test-key-id"
ROLE = "USER"
TAG_NAME = "test-tag"
TAG_VALUE = "test-value"


@pytest.fixture(scope="module")
def configuration():
    return Configuration("http://localhost:8080/api")


@pytest.fixture(scope="module")
def async_client(configuration):
    return AsyncOrkesBaseClient(configuration)


@pytest.fixture(scope="module")
def create_application_request():
    return CreateOrUpdateApplicationRequestAdapter(name=APP_NAME)


@pytest.fixture(scope="module")
def extended_conductor_application():
    return ExtendedConductorApplicationAdapter(
        id=APP_ID,
        name=APP_NAME,
        create_time=1699236095031,
        created_by="test-user",
        update_time=1699236095031,
        updated_by="test-user",
        tags=[],
    )


@pytest.fixture(scope="module")
def tag():
    return Tag(key=TAG_NAME, value=TAG_VALUE)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.getLogger().setLevel(logging.ERROR)


def test_init(async_client):
    assert async_client is not None
    assert hasattr(async_client, "application_resource_api")
    assert async_client.application_resource_api is not None


@pytest.mark.asyncio
async def test_create_application(
    async_client, create_application_request, extended_conductor_application, mocker
):
    mock_create = mocker.patch.object(
        async_client.application_resource_api,
        "create_application",
        autospec=True,
    )
    mock_create.return_value = extended_conductor_application

    result = await async_client.application_resource_api.create_application(
        create_application_request
    )

    mock_create.assert_called_once_with(create_application_request)

    assert result == extended_conductor_application
    assert result.id == APP_ID
    assert result.name == APP_NAME


@pytest.mark.asyncio
async def test_get_application(async_client, extended_conductor_application, mocker):
    mock_get = mocker.patch.object(
        async_client.application_resource_api,
        "get_application",
        autospec=True,
    )
    mock_get.return_value = extended_conductor_application

    result = await async_client.application_resource_api.get_application(APP_ID)

    mock_get.assert_called_once_with(APP_ID)
    assert result == extended_conductor_application
    assert result.id == APP_ID
    assert result.name == APP_NAME


@pytest.mark.asyncio
async def test_list_applications(async_client, extended_conductor_application, mocker):
    mock_list = mocker.patch.object(
        async_client.application_resource_api,
        "list_applications",
        autospec=True,
    )
    mock_list.return_value = [extended_conductor_application]

    result = await async_client.application_resource_api.list_applications()

    mock_list.assert_called_once()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == extended_conductor_application
    assert result[0].id == APP_ID


@pytest.mark.asyncio
async def test_update_application(
    async_client, create_application_request, extended_conductor_application, mocker
):
    mock_update = mocker.patch.object(
        async_client.application_resource_api,
        "update_application",
        autospec=True,
    )
    mock_update.return_value = extended_conductor_application

    result = await async_client.application_resource_api.update_application(
        APP_ID, create_application_request
    )

    mock_update.assert_called_once_with(APP_ID, create_application_request)

    assert result == extended_conductor_application


@pytest.mark.asyncio
async def test_delete_application(async_client, mocker):
    mock_delete = mocker.patch.object(
        async_client.application_resource_api,
        "delete_application",
        autospec=True,
    )
    mock_delete.return_value = {"status": "deleted"}

    result = await async_client.application_resource_api.delete_application(APP_ID)

    mock_delete.assert_called_once_with(APP_ID)

    assert result == {"status": "deleted"}


@pytest.mark.asyncio
async def test_create_access_key(async_client, mocker):
    mock_create_key = mocker.patch.object(
        async_client.application_resource_api,
        "create_access_key",
        autospec=True,
    )
    mock_create_key.return_value = {"id": ACCESS_KEY_ID, "secret": "test-secret"}

    result = await async_client.application_resource_api.create_access_key(APP_ID)

    mock_create_key.assert_called_once_with(APP_ID)

    assert result == {"id": ACCESS_KEY_ID, "secret": "test-secret"}


@pytest.mark.asyncio
async def test_get_access_keys(async_client, mocker):
    mock_get_keys = mocker.patch.object(
        async_client.application_resource_api,
        "get_access_keys",
        autospec=True,
    )
    mock_get_keys.return_value = [{"id": ACCESS_KEY_ID, "status": "ACTIVE"}]

    result = await async_client.application_resource_api.get_access_keys(APP_ID)

    mock_get_keys.assert_called_once_with(APP_ID)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == ACCESS_KEY_ID


@pytest.mark.asyncio
async def test_delete_access_key(async_client, mocker):
    mock_delete_key = mocker.patch.object(
        async_client.application_resource_api,
        "delete_access_key",
        autospec=True,
    )
    mock_delete_key.return_value = {"status": "deleted"}

    result = await async_client.application_resource_api.delete_access_key(
        APP_ID, KEY_ID
    )

    mock_delete_key.assert_called_once_with(APP_ID, KEY_ID)

    assert result == {"status": "deleted"}


@pytest.mark.asyncio
async def test_toggle_access_key_status(async_client, mocker):
    mock_toggle = mocker.patch.object(
        async_client.application_resource_api,
        "toggle_access_key_status",
        autospec=True,
    )
    mock_toggle.return_value = {"id": KEY_ID, "status": "INACTIVE"}

    result = await async_client.application_resource_api.toggle_access_key_status(
        APP_ID, KEY_ID
    )

    mock_toggle.assert_called_once_with(APP_ID, KEY_ID)

    assert result == {"id": KEY_ID, "status": "INACTIVE"}


@pytest.mark.asyncio
async def test_add_role_to_application_user(async_client, mocker):
    mock_add_role = mocker.patch.object(
        async_client.application_resource_api,
        "add_role_to_application_user",
        autospec=True,
    )
    mock_add_role.return_value = {"status": "role_added"}

    result = await async_client.application_resource_api.add_role_to_application_user(
        APP_ID, ROLE
    )

    mock_add_role.assert_called_once_with(APP_ID, ROLE)

    assert result == {"status": "role_added"}


@pytest.mark.asyncio
async def test_remove_role_from_application_user(async_client, mocker):
    mock_remove_role = mocker.patch.object(
        async_client.application_resource_api,
        "remove_role_from_application_user",
        autospec=True,
    )
    mock_remove_role.return_value = {"status": "role_removed"}

    result = (
        await async_client.application_resource_api.remove_role_from_application_user(
            APP_ID, ROLE
        )
    )

    mock_remove_role.assert_called_once_with(APP_ID, ROLE)

    assert result == {"status": "role_removed"}


@pytest.mark.asyncio
async def test_get_tags_for_application(async_client, tag, mocker):
    mock_get_tags = mocker.patch.object(
        async_client.application_resource_api,
        "get_tags_for_application",
        autospec=True,
    )
    mock_get_tags.return_value = [tag]

    result = await async_client.application_resource_api.get_tags_for_application(
        APP_ID
    )

    mock_get_tags.assert_called_once_with(APP_ID)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == tag
    assert result[0].key == TAG_NAME


@pytest.mark.asyncio
async def test_put_tag_for_application(async_client, tag, mocker):
    mock_put_tags = mocker.patch.object(
        async_client.application_resource_api,
        "put_tag_for_application",
        autospec=True,
    )
    mock_put_tags.return_value = None

    result = await async_client.application_resource_api.put_tag_for_application(
        APP_ID, [tag]
    )

    mock_put_tags.assert_called_once_with(APP_ID, [tag])

    assert result is None


@pytest.mark.asyncio
async def test_delete_tag_for_application(async_client, tag, mocker):
    mock_delete_tags = mocker.patch.object(
        async_client.application_resource_api,
        "delete_tag_for_application",
        autospec=True,
    )
    mock_delete_tags.return_value = None

    result = await async_client.application_resource_api.delete_tag_for_application(
        APP_ID, [tag]
    )

    mock_delete_tags.assert_called_once_with(APP_ID, [tag])

    assert result is None


@pytest.mark.asyncio
async def test_get_app_by_access_key_id(
    async_client, extended_conductor_application, mocker
):
    mock_get_app = mocker.patch.object(
        async_client.application_resource_api,
        "get_app_by_access_key_id",
        autospec=True,
    )
    mock_get_app.return_value = extended_conductor_application

    result = await async_client.application_resource_api.get_app_by_access_key_id(
        ACCESS_KEY_ID
    )

    mock_get_app.assert_called_once_with(ACCESS_KEY_ID)

    assert result == extended_conductor_application
    assert result.id == APP_ID


@pytest.mark.asyncio
async def test_error_handling(async_client, mocker):
    mock_get = mocker.patch.object(
        async_client.application_resource_api,
        "get_application",
        autospec=True,
    )
    mock_get.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        await async_client.application_resource_api.get_application(APP_ID)

    mock_get.assert_called_once_with(APP_ID)


@pytest.mark.asyncio
async def test_multiple_concurrent_requests(
    async_client, extended_conductor_application, mocker
):
    mock_get = mocker.patch.object(
        async_client.application_resource_api,
        "get_application",
        autospec=True,
    )
    mock_get.return_value = extended_conductor_application

    tasks = [
        async_client.application_resource_api.get_application(f"{APP_ID}-{i}")
        for i in range(3)
    ]

    results = await asyncio.gather(*tasks)

    assert mock_get.call_count == 3
    assert len(results) == 3
    assert all(result == extended_conductor_application for result in results)


@pytest.mark.asyncio
async def test_request_timeout(async_client, mocker):
    mock_get = mocker.patch.object(
        async_client.application_resource_api,
        "get_application",
        autospec=True,
    )
    mock_get.side_effect = Exception("Timeout")

    with pytest.raises(Exception, match="Timeout"):
        await async_client.application_resource_api.get_application(
            APP_ID, _request_timeout=5.0
        )

    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert call_args[1]["_request_timeout"] == 5.0
