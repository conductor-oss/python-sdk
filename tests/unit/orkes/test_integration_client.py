import logging
import pytest

from conductor.client.codegen.rest import ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.integration_resource_api import IntegrationResourceApi
from conductor.client.http.models.integration import Integration
from conductor.client.http.models.integration_api import IntegrationApi
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.http.models.integration_def import IntegrationDef
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.message_template import MessageTemplate
from conductor.client.http.models.tag import Tag
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient

INTEGRATION_NAME = "test_integration"
INTEGRATION_API_NAME = "test_api"
AI_PROMPT = "test_prompt"
MODEL_NAME = "test_model"
AI_INTEGRATION = "test_ai_integration"


@pytest.fixture(scope="module")
def integration_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesIntegrationClient(configuration)


@pytest.fixture(scope="module")
def integration():
    return Integration()


@pytest.fixture(scope="module")
def integration_update():
    return IntegrationUpdate()


@pytest.fixture(scope="module")
def integration_api():
    return IntegrationApi()


@pytest.fixture(scope="module")
def integration_api_update():
    return IntegrationApiUpdate()


@pytest.fixture(scope="module")
def integration_def():
    return IntegrationDef()


@pytest.fixture(scope="module")
def tag_list():
    return [Tag(key="env", value="prod"), Tag(key="team", value="platform")]


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def test_init(integration_client):
    message = "integration_api is not of type IntegrationResourceApi"
    assert isinstance(integration_client._integration_api, IntegrationResourceApi), message


def test_save_integration_provider(mocker, integration_client, integration_update):
    mock = mocker.patch.object(IntegrationResourceApi, "save_integration_provider")
    integration_client.save_integration_provider(INTEGRATION_NAME, integration_update)
    mock.assert_called_with(body=integration_update, name=INTEGRATION_NAME)


def test_save_integration(mocker, integration_client, integration_update):
    mock = mocker.patch.object(IntegrationResourceApi, "save_integration_provider")
    integration_client.save_integration(INTEGRATION_NAME, integration_update)
    mock.assert_called_with(body=integration_update, name=INTEGRATION_NAME)


def test_get_integration_provider(mocker, integration_client, integration):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_provider")
    mock.return_value = integration
    result = integration_client.get_integration_provider(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result == integration


def test_get_integration_provider_not_found(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_provider")
    api_exception = ApiException(status=404)
    mock.side_effect = api_exception
    result = integration_client.get_integration_provider(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result is None


def test_get_integration(mocker, integration_client, integration):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_provider")
    mock.return_value = integration
    result = integration_client.get_integration(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result == integration


def test_get_integration_not_found(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_provider")
    api_exception = ApiException(status=404)
    mock.side_effect = api_exception
    result = integration_client.get_integration(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result is None


def test_get_integration_providers(mocker, integration_client, integration):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_providers")
    mock.return_value = [integration]
    result = integration_client.get_integration_providers()
    assert mock.called
    assert result == [integration]


def test_get_integration_providers_with_filters(mocker, integration_client, integration):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_providers")
    mock.return_value = [integration]
    result = integration_client.get_integration_providers(category="API", active_only=True)
    mock.assert_called_with(category="API", active_only=True)
    assert result == [integration]


def test_get_integration_provider_defs(mocker, integration_client, integration_def):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_provider_defs")
    mock.return_value = [integration_def]
    result = integration_client.get_integration_provider_defs()
    assert mock.called
    assert result == [integration_def]


def test_delete_integration(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "delete_integration_provider")
    integration_client.delete_integration(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)


def test_save_integration_api(mocker, integration_client, integration_api_update):
    mock = mocker.patch.object(IntegrationResourceApi, "save_integration_api")
    integration_client.save_integration_api(INTEGRATION_NAME, INTEGRATION_API_NAME, integration_api_update)
    mock.assert_called_with(body=integration_api_update, name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)


def test_get_integration_api(mocker, integration_client, integration_api):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_api")
    mock.return_value = integration_api
    result = integration_client.get_integration_api(INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)
    assert result == integration_api


def test_get_integration_api_not_found(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_api")
    api_exception = ApiException(status=404)
    mock.side_effect = api_exception
    result = integration_client.get_integration_api(INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)
    assert result is None


def test_delete_integration_api(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "delete_integration_api")
    integration_client.delete_integration_api(INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)


def test_get_integration_apis(mocker, integration_client, integration_api):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_apis")
    mock.return_value = [integration_api]
    result = integration_client.get_integration_apis(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result == [integration_api]


def test_get_integrations(mocker, integration_client, integration):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_providers")
    mock.return_value = [integration]
    result = integration_client.get_integrations()
    assert mock.called
    assert result == [integration]


def test_associate_prompt_with_integration(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "associate_prompt_with_integration")
    integration_client.associate_prompt_with_integration(AI_INTEGRATION, MODEL_NAME, AI_PROMPT)
    mock.assert_called_with(integration_provider=AI_INTEGRATION, integration_name=MODEL_NAME, prompt_name=AI_PROMPT)


def test_get_prompts_with_integration(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_prompts_with_integration")
    message_template = MessageTemplate()
    mock.return_value = [message_template]
    result = integration_client.get_prompts_with_integration(AI_INTEGRATION, MODEL_NAME)
    mock.assert_called_with(integration_provider=AI_INTEGRATION, integration_name=MODEL_NAME)
    assert result == [message_template]


def test_get_token_usage_for_integration(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_token_usage_for_integration")
    mock.return_value = 1000
    result = integration_client.get_token_usage_for_integration(INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)
    assert result == 1000


def test_get_token_usage_for_integration_provider(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_token_usage_for_integration_provider")
    expected_usage = {"total": "5000", "monthly": "1000"}
    mock.return_value = expected_usage
    result = integration_client.get_token_usage_for_integration_provider(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result == expected_usage


def test_register_token_usage(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "register_token_usage")
    integration_client.register_token_usage(500, INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(body=500, name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)


def test_delete_tag_for_integration(mocker, integration_client, tag_list):
    mock = mocker.patch.object(IntegrationResourceApi, "delete_tag_for_integration")
    integration_client.delete_tag_for_integration(tag_list, INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(body=tag_list, name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)


def test_delete_tag_for_integration_provider(mocker, integration_client, tag_list):
    mock = mocker.patch.object(IntegrationResourceApi, "delete_tag_for_integration_provider")
    integration_client.delete_tag_for_integration_provider(tag_list, INTEGRATION_NAME)
    mock.assert_called_with(body=tag_list, name=INTEGRATION_NAME)


def test_get_tags_for_integration(mocker, integration_client, tag_list):
    mock = mocker.patch.object(IntegrationResourceApi, "get_tags_for_integration")
    mock.return_value = tag_list
    result = integration_client.get_tags_for_integration(INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)
    assert result == tag_list


def test_get_tags_for_integration_provider(mocker, integration_client, tag_list):
    mock = mocker.patch.object(IntegrationResourceApi, "get_tags_for_integration_provider")
    mock.return_value = tag_list
    result = integration_client.get_tags_for_integration_provider(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result == tag_list


def test_put_tag_for_integration(mocker, integration_client, tag_list):
    mock = mocker.patch.object(IntegrationResourceApi, "put_tag_for_integration")
    integration_client.put_tag_for_integration(tag_list, INTEGRATION_API_NAME, INTEGRATION_NAME)
    mock.assert_called_with(body=tag_list, name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME)


def test_put_tag_for_integration_provider(mocker, integration_client, tag_list):
    mock = mocker.patch.object(IntegrationResourceApi, "put_tag_for_integration_provider")
    integration_client.put_tag_for_integration_provider(tag_list, INTEGRATION_NAME)
    mock.assert_called_with(body=tag_list, name=INTEGRATION_NAME)


def test_get_integration_providers_empty(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_providers")
    mock.return_value = []
    result = integration_client.get_integration_providers()
    assert mock.called
    assert result == []


def test_get_integration_apis_empty(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApi, "get_integration_apis")
    mock.return_value = []
    result = integration_client.get_integration_apis(INTEGRATION_NAME)
    mock.assert_called_with(name=INTEGRATION_NAME)
    assert result == []
