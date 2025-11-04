import logging

import pytest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.secret_resource_api import SecretResourceApi
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_secret_client import OrkesSecretClient

SECRET_KEY = "ut_secret_key"
SECRET_VALUE = "ut_secret_value"
ERROR_BODY = '{"message":"No such secret found by key"}'


@pytest.fixture(scope="module")
def secret_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesSecretClient(configuration)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def test_init(secret_client):
    message = "secretResourceApi is not of type SecretResourceApi"
    assert isinstance(secret_client._secret_api, SecretResourceApi), message


def test_put_secret(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "put_secret")
    secret_client.put_secret(SECRET_KEY, SECRET_VALUE)
    mock.assert_called_with(body=SECRET_VALUE, key=SECRET_KEY)


def test_get_secret(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "get_secret")
    mock.return_value = SECRET_VALUE
    secret = secret_client.get_secret(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)
    assert secret == SECRET_VALUE


def test_list_all_secret_names(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "list_all_secret_names")
    secret_list = ["TEST_SECRET_1", "TEST_SECRET_2"]
    mock.return_value = secret_list
    secret_names = secret_client.list_all_secret_names()
    assert mock.called
    assert set(secret_names) == set(secret_list)


def test_list_secrets_that_user_can_grant_access_to(mocker, secret_client):
    mock = mocker.patch.object(
        SecretResourceApi, "list_secrets_that_user_can_grant_access_to"
    )
    secret_list = ["TEST_SECRET_1", "TEST_SECRET_2"]
    mock.return_value = secret_list
    secret_names = secret_client.list_secrets_that_user_can_grant_access_to()
    assert mock.called
    assert secret_names == secret_list


def test_delete_secret(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "delete_secret")
    secret_client.delete_secret(SECRET_KEY)
    mock.assert_called_with(key=SECRET_KEY)


def test_secret_exists(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "secret_exists")
    mock.return_value = True
    assert secret_client.secret_exists(SECRET_KEY) is True
    mock.assert_called_with(key=SECRET_KEY)


def test_set_secret_tags(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "put_tag_for_secret")
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    tags = [tag1, tag2]
    secret_client.set_secret_tags(tags, SECRET_KEY)
    mock.assert_called_with(tags, SECRET_KEY)


def test_get_secret_tags(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "get_tags")
    expected_tags_len = 2
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    mock.return_value = [tag1, tag2]
    tags = secret_client.get_secret_tags(SECRET_KEY)
    mock.assert_called_with(SECRET_KEY)
    assert len(tags) == expected_tags_len


def test_delete_secret_tags(mocker, secret_client):
    mock = mocker.patch.object(SecretResourceApi, "delete_tag_for_secret")
    tag1 = MetadataTag("tag1", "val1")
    tag2 = MetadataTag("tag2", "val2")
    tags = [tag1, tag2]
    secret_client.delete_secret_tags(tags, SECRET_KEY)
    mock.assert_called_with(tags, SECRET_KEY)
