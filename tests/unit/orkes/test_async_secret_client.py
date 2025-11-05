import logging
import pytest

from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters.api.secret_resource_api import SecretResourceApiAdapter
from conductor.asyncio_client.adapters.models.extended_secret_adapter import (
    ExtendedSecretAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_secret_client import OrkesSecretClient
from conductor.asyncio_client.adapters import ApiClient

SECRET_KEY = "ut_secret_key"
SECRET_VALUE = "ut_secret_value"
ERROR_BODY = '{"message":"No such secret found by key"}'


@pytest.fixture(scope="module")
def secret_client():
    configuration = Configuration("http://localhost:8080/api")
    api_client = ApiClient(configuration)
    return OrkesSecretClient(configuration, api_client=api_client)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def tag_adapter():
    return TagAdapter(key="tag1", value="val1")


@pytest.fixture
def tag_list():
    return [
        TagAdapter(key="tag1", value="val1"),
        TagAdapter(key="tag2", value="val2"),
    ]


@pytest.fixture
def extended_secret():
    return ExtendedSecretAdapter(
        name="secret", tags=[TagAdapter(key="tag1", value="val1")]
    )


@pytest.mark.asyncio
async def test_init(secret_client):
    message = "secret_api is not of type SecretResourceApiAdapter"
    assert isinstance(secret_client._secret_api, SecretResourceApiAdapter), message


@pytest.mark.asyncio
async def test_put_secret(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_secret")
    mock.return_value = {"status": "success"}
    result = await secret_client.put_secret(SECRET_KEY, SECRET_VALUE)
    mock.assert_called_with(SECRET_KEY, SECRET_VALUE)
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_get_secret(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "get_secret")
    mock.return_value = SECRET_VALUE
    result = await secret_client.get_secret(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert result == SECRET_VALUE


@pytest.mark.asyncio
async def test_delete_secret(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "delete_secret")
    mock.return_value = {"status": "deleted"}
    result = await secret_client.delete_secret(SECRET_KEY)
    mock.assert_called_with(SECRET_KEY)
    assert result == {"status": "deleted"}


@pytest.mark.asyncio
async def test_secret_exists_true(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "secret_exists")
    mock.return_value = True
    result = await secret_client.secret_exists(SECRET_KEY)
    mock.assert_called_with(SECRET_KEY)
    assert result is True


@pytest.mark.asyncio
async def test_secret_exists_false(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "secret_exists")
    mock.return_value = False
    result = await secret_client.secret_exists(SECRET_KEY)
    mock.assert_called_with(SECRET_KEY)
    assert result is False


@pytest.mark.asyncio
async def test_list_all_secret_names(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "list_all_secret_names")
    secret_list = ["TEST_SECRET_1", "TEST_SECRET_2"]
    mock.return_value = secret_list
    result = await secret_client.list_all_secret_names()
    assert mock.called
    assert result == secret_list


@pytest.mark.asyncio
async def test_list_secrets_that_user_can_grant_access_to(mocker, secret_client):
    mock = mocker.patch.object(
        SecretResourceApiAdapter, "list_secrets_that_user_can_grant_access_to"
    )
    accessible_secrets = ["secret1", "secret2"]
    mock.return_value = accessible_secrets
    result = await secret_client.list_secrets_that_user_can_grant_access_to()
    assert mock.called
    assert result == accessible_secrets


@pytest.mark.asyncio
async def test_list_secrets_with_tags_that_user_can_grant_access_to(
    mocker, secret_client, extended_secret
):
    mock = mocker.patch.object(
        SecretResourceApiAdapter, "list_secrets_with_tags_that_user_can_grant_access_to"
    )
    extended_secrets = [
        ExtendedSecretAdapter(name="secret1", tags=[TagAdapter(key="tag1", value="val1")]),
        ExtendedSecretAdapter(name="secret2", tags=[TagAdapter(key="tag2", value="val2")]),
    ]
    mock.return_value = extended_secrets
    result = await secret_client.list_secrets_with_tags_that_user_can_grant_access_to()
    assert mock.called
    assert result == extended_secrets


@pytest.mark.asyncio
async def test_put_tag_for_secret(mocker, secret_client, tag_list):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_tag_for_secret")
    await secret_client.put_tag_for_secret(SECRET_KEY, tag_list)
    mock.assert_called_with(key=SECRET_KEY, tag=tag_list)


@pytest.mark.asyncio
async def test_get_tags(mocker, secret_client, tag_list):
    mock = mocker.patch.object(SecretResourceApiAdapter, "get_tags")
    mock.return_value = tag_list
    result = await secret_client.get_tags(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert result == tag_list


@pytest.mark.asyncio
async def test_delete_tag_for_secret(mocker, secret_client, tag_list):
    mock = mocker.patch.object(SecretResourceApiAdapter, "delete_tag_for_secret")
    await secret_client.delete_tag_for_secret(SECRET_KEY, tag_list)
    mock.assert_called_with(key=SECRET_KEY, tag=tag_list)


@pytest.mark.asyncio
async def test_clear_local_cache(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "clear_local_cache")
    mock.return_value = {"cleared": "local"}
    result = await secret_client.clear_local_cache()
    assert mock.called
    assert result == {"cleared": "local"}


@pytest.mark.asyncio
async def test_clear_redis_cache(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "clear_redis_cache")
    mock.return_value = {"cleared": "redis"}
    result = await secret_client.clear_redis_cache()
    assert mock.called
    assert result == {"cleared": "redis"}


@pytest.mark.asyncio
async def test_list_secrets(mocker, secret_client):
    mock = mocker.patch.object(secret_client, "list_all_secret_names")
    secret_list = ["secret1", "secret2"]
    mock.return_value = secret_list
    result = await secret_client.list_secrets()
    mock.assert_called_with()
    assert result == secret_list


@pytest.mark.asyncio
async def test_update_secret(mocker, secret_client):
    mock = mocker.patch.object(secret_client, "put_secret")
    mock.return_value = {"status": "updated"}
    result = await secret_client.update_secret(SECRET_KEY, SECRET_VALUE)
    mock.assert_called_with(SECRET_KEY, SECRET_VALUE)
    assert result == {"status": "updated"}


@pytest.mark.asyncio
async def test_has_secret(mocker, secret_client):
    mock = mocker.patch.object(secret_client, "secret_exists")
    mock.return_value = True
    result = await secret_client.has_secret(SECRET_KEY)
    mock.assert_called_with(SECRET_KEY)
    assert result is True


@pytest.mark.asyncio
async def test_get_secret_api_exception(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "get_secret")
    mock.side_effect = ApiException(status=404, body=ERROR_BODY)
    with pytest.raises(ApiException):
        await secret_client.get_secret(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)


@pytest.mark.asyncio
async def test_put_secret_api_exception(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_secret")
    mock.side_effect = ApiException(status=400, body="Bad request")
    with pytest.raises(ApiException):
        await secret_client.put_secret(SECRET_KEY, SECRET_VALUE)
    mock.assert_called_with(SECRET_KEY, SECRET_VALUE)


@pytest.mark.asyncio
async def test_delete_secret_api_exception(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "delete_secret")
    mock.side_effect = ApiException(status=404, body=ERROR_BODY)
    with pytest.raises(ApiException):
        await secret_client.delete_secret(SECRET_KEY)
    mock.assert_called_with(SECRET_KEY)


@pytest.mark.asyncio
async def test_put_tag_for_secret_api_exception(mocker, secret_client, tag_list):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_tag_for_secret")
    mock.side_effect = ApiException(status=400, body="Bad request")
    with pytest.raises(ApiException):
        await secret_client.put_tag_for_secret(SECRET_KEY, tag_list)
    mock.assert_called_with(key=SECRET_KEY, tag=tag_list)


@pytest.mark.asyncio
async def test_get_tags_api_exception(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "get_tags")
    mock.side_effect = ApiException(status=404, body=ERROR_BODY)
    with pytest.raises(ApiException):
        await secret_client.get_tags(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)


@pytest.mark.asyncio
async def test_delete_tag_for_secret_api_exception(mocker, secret_client, tag_list):
    mock = mocker.patch.object(SecretResourceApiAdapter, "delete_tag_for_secret")
    mock.side_effect = ApiException(status=400, body="Bad request")
    with pytest.raises(ApiException):
        await secret_client.delete_tag_for_secret(SECRET_KEY, tag_list)
    mock.assert_called_with(key=SECRET_KEY, tag=tag_list)


@pytest.mark.asyncio
async def test_clear_local_cache_api_exception(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "clear_local_cache")
    mock.side_effect = ApiException(status=500, body="Internal error")
    with pytest.raises(ApiException):
        await secret_client.clear_local_cache()
    assert mock.called


@pytest.mark.asyncio
async def test_clear_redis_cache_api_exception(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "clear_redis_cache")
    mock.side_effect = ApiException(status=500, body="Internal error")
    with pytest.raises(ApiException):
        await secret_client.clear_redis_cache()
    assert mock.called


@pytest.mark.asyncio
async def test_put_secret_empty_value(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_secret")
    mock.return_value = {"status": "success"}
    result = await secret_client.put_secret(SECRET_KEY, "")
    mock.assert_called_with(SECRET_KEY, "")
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_get_secret_empty_list(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "list_all_secret_names")
    mock.return_value = []
    result = await secret_client.list_all_secret_names()
    assert mock.called
    assert result == []


@pytest.mark.asyncio
async def test_put_tag_for_secret_empty_tags(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_tag_for_secret")
    await secret_client.put_tag_for_secret(SECRET_KEY, [])
    mock.assert_called_with(key=SECRET_KEY, tag=[])


@pytest.mark.asyncio
async def test_list_all_secret_names_empty(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "list_all_secret_names")
    mock.return_value = []
    result = await secret_client.list_all_secret_names()
    assert mock.called
    assert result == []


@pytest.mark.asyncio
async def test_secret_exists_with_special_characters(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "secret_exists")
    mock.return_value = True
    special_key = "secret@#$%^&*()"
    result = await secret_client.secret_exists(special_key)
    mock.assert_called_with(special_key)
    assert result is True


@pytest.mark.asyncio
async def test_put_secret_with_large_value(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_secret")
    mock.return_value = {"status": "success"}
    large_value = "x" * 10000
    result = await secret_client.put_secret(SECRET_KEY, large_value)
    mock.assert_called_with(SECRET_KEY, large_value)
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_get_tags_with_multiple_tags(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "get_tags")
    multiple_tags = [
        TagAdapter(key="env", value="prod"),
        TagAdapter(key="service", value="api"),
        TagAdapter(key="version", value="1.0"),
    ]
    mock.return_value = multiple_tags
    result = await secret_client.get_tags(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert result == multiple_tags


@pytest.mark.asyncio
async def test_put_tag_for_secret_single_tag(mocker, secret_client, tag_adapter):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_tag_for_secret")
    await secret_client.put_tag_for_secret(SECRET_KEY, [tag_adapter])
    mock.assert_called_with(key=SECRET_KEY, tag=[tag_adapter])


@pytest.mark.asyncio
async def test_delete_tag_for_secret_single_tag(mocker, secret_client, tag_adapter):
    mock = mocker.patch.object(SecretResourceApiAdapter, "delete_tag_for_secret")
    await secret_client.delete_tag_for_secret(SECRET_KEY, [tag_adapter])
    mock.assert_called_with(key=SECRET_KEY, tag=[tag_adapter])


@pytest.mark.asyncio
async def test_list_secrets_that_user_can_grant_access_to_empty(mocker, secret_client):
    mock = mocker.patch.object(
        SecretResourceApiAdapter, "list_secrets_that_user_can_grant_access_to"
    )
    mock.return_value = []
    result = await secret_client.list_secrets_that_user_can_grant_access_to()
    assert mock.called
    assert result == []


@pytest.mark.asyncio
async def test_list_secrets_with_tags_that_user_can_grant_access_to_empty(
    mocker, secret_client
):
    mock = mocker.patch.object(
        SecretResourceApiAdapter, "list_secrets_with_tags_that_user_can_grant_access_to"
    )
    mock.return_value = []
    result = await secret_client.list_secrets_with_tags_that_user_can_grant_access_to()
    assert mock.called
    assert result == []


@pytest.mark.asyncio
async def test_put_secret_validated(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "put_secret")
    await secret_client.put_secret_validated(SECRET_KEY, SECRET_VALUE)
    mock.assert_called_with(key=SECRET_KEY, body=SECRET_VALUE)


@pytest.mark.asyncio
async def test_delete_secret_validated(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "delete_secret")
    await secret_client.delete_secret_validated(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)


@pytest.mark.asyncio
async def test_secret_exists_validated_true(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "secret_exists")
    mock.return_value = True
    result = await secret_client.secret_exists_validated(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert result is True


@pytest.mark.asyncio
async def test_secret_exists_validated_false(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "secret_exists")
    mock.return_value = False
    result = await secret_client.secret_exists_validated(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert result is False


@pytest.mark.asyncio
async def test_clear_local_cache_validated(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "clear_local_cache")
    await secret_client.clear_local_cache_validated()
    assert mock.called


@pytest.mark.asyncio
async def test_clear_redis_cache_validated(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApiAdapter, "clear_redis_cache")
    await secret_client.clear_redis_cache_validated()
    assert mock.called


@pytest.mark.asyncio
async def test_update_secret_validated(mocker, secret_client):
    mock = mocker.patch.object(secret_client, "put_secret_validated")
    await secret_client.update_secret_validated(SECRET_KEY, SECRET_VALUE)
    mock.assert_called_with(key=SECRET_KEY, secret=SECRET_VALUE)


@pytest.mark.asyncio
async def test_has_secret_validated_true(mocker, secret_client):
    mock = mocker.patch.object(secret_client, "secret_exists_validated")
    mock.return_value = True
    result = await secret_client.has_secret_validated(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert result is True


@pytest.mark.asyncio
async def test_has_secret_validated_false(mocker, secret_client):
    mock = mocker.patch.object(secret_client, "secret_exists_validated")
    mock.return_value = False
    result = await secret_client.has_secret_validated(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert result is False
