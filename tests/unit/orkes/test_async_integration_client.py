import logging

import pytest

from conductor.asyncio_client.adapters.api.integration_resource_api import (
    IntegrationResourceApiAdapter,
)
from conductor.asyncio_client.adapters.models.event_log_adapter import EventLogAdapter
from conductor.asyncio_client.adapters.models.integration_adapter import (
    IntegrationAdapter,
)
from conductor.asyncio_client.adapters.models.integration_api_adapter import (
    IntegrationApiAdapter,
)
from conductor.asyncio_client.adapters.models.integration_api_update_adapter import (
    IntegrationApiUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.integration_def_adapter import (
    IntegrationDefAdapter,
)
from conductor.asyncio_client.adapters.models.integration_update_adapter import (
    IntegrationUpdateAdapter,
)
from conductor.asyncio_client.adapters.models.message_template_adapter import (
    MessageTemplateAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_integration_client import (
    OrkesIntegrationClient,
)
from conductor.asyncio_client.adapters import ApiClient


INTEGRATION_NAME = "test_integration"
INTEGRATION_API_NAME = "test_api"
INTEGRATION_PROVIDER = "test_provider"
AI_PROMPT = "test_prompt"
CATEGORY = "API"
EVENT_TYPE = "SEND"


@pytest.fixture(scope="module")
def integration_client():
    configuration = Configuration("http://localhost:8080/api")
    api_client = ApiClient(configuration)
    return OrkesIntegrationClient(configuration, api_client=api_client)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def integration_def():
    return IntegrationDefAdapter(
        name=INTEGRATION_NAME,
        category=CATEGORY,
        enabled=True,
    )


@pytest.fixture
def integration_update():
    return IntegrationUpdateAdapter(
        category=CATEGORY,
        enabled=True,
    )


@pytest.fixture
def integration_api():
    return IntegrationApiAdapter(
        api=INTEGRATION_API_NAME,
        integration_name=INTEGRATION_NAME,
    )


@pytest.fixture
def integration_api_update():
    return IntegrationApiUpdateAdapter(
        description="Test API Update",
        enabled=True,
    )


@pytest.fixture
def integration():
    return IntegrationAdapter(
        name=INTEGRATION_NAME,
        category=CATEGORY,
        enabled=True,
    )


@pytest.fixture
def tag():
    return TagAdapter(key="test_key", value="test_value", type="METADATA")


@pytest.fixture
def event_log():
    return EventLogAdapter(
        event_type=EVENT_TYPE,
    )


@pytest.mark.asyncio
async def test_save_integration_provider(
    mocker, integration_client, integration_update
):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter, "save_integration_provider"
    )
    await integration_client.save_integration_provider(
        INTEGRATION_NAME, integration_update
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME, integration_update)


@pytest.mark.asyncio
async def test_get_integration_provider(mocker, integration_client, integration_def):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_provider",
        return_value=integration_def,
    )
    result = await integration_client.get_integration_provider(INTEGRATION_NAME)
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME)
    assert result == integration_def


@pytest.mark.asyncio
async def test_delete_integration_provider(mocker, integration_client):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter, "delete_integration_provider"
    )
    await integration_client.delete_integration_provider(INTEGRATION_NAME)
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME)


@pytest.mark.asyncio
async def test_get_integration_providers(mocker, integration_client, integration_def):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_providers",
        return_value=[integration_def],
    )
    result = await integration_client.get_integration_providers()
    assert mock.called
    mock.assert_called_with(category=None, active_only=None)
    assert result == [integration_def]


@pytest.mark.asyncio
async def test_get_integration_providers_with_filters(
    mocker, integration_client, integration_def
):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_providers",
        return_value=[integration_def],
    )
    result = await integration_client.get_integration_providers(
        category=CATEGORY, active_only=True
    )
    assert mock.called
    mock.assert_called_with(category=CATEGORY, active_only=True)
    assert result == [integration_def]


@pytest.mark.asyncio
async def test_get_integration_provider_defs(
    mocker, integration_client, integration_def
):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_provider_defs",
        return_value=[integration_def],
    )
    result = await integration_client.get_integration_provider_defs(INTEGRATION_NAME)
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME)
    assert result == [integration_def]


@pytest.mark.asyncio
async def test_save_integration_api(mocker, integration_client, integration_api_update):
    mock = mocker.patch.object(IntegrationResourceApiAdapter, "save_integration_api")
    await integration_client.save_integration_api(
        INTEGRATION_API_NAME, INTEGRATION_NAME, integration_api_update
    )
    assert mock.called
    mock.assert_called_with(
        INTEGRATION_API_NAME, INTEGRATION_NAME, integration_api_update
    )


@pytest.mark.asyncio
async def test_get_integration_api(mocker, integration_client, integration_api):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_api",
        return_value=integration_api,
    )
    result = await integration_client.get_integration_api(
        INTEGRATION_API_NAME, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_API_NAME, INTEGRATION_NAME)
    assert result == integration_api


@pytest.mark.asyncio
async def test_delete_integration_api(mocker, integration_client):
    mock = mocker.patch.object(IntegrationResourceApiAdapter, "delete_integration_api")
    await integration_client.delete_integration_api(
        INTEGRATION_API_NAME, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_API_NAME, INTEGRATION_NAME)


@pytest.mark.asyncio
async def test_get_integration_apis(mocker, integration_client, integration_api):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_apis",
        return_value=[integration_api],
    )
    result = await integration_client.get_integration_apis(INTEGRATION_NAME)
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME)
    assert result == [integration_api]


@pytest.mark.asyncio
async def test_get_integration_available_apis(
    mocker, integration_client, integration_api
):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_available_apis",
        return_value=[integration_api],
    )
    result = await integration_client.get_integration_available_apis(INTEGRATION_NAME)
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME)
    assert result == [integration_api]


@pytest.mark.asyncio
async def test_save_all_integrations(mocker, integration_client, integration_update):
    mock = mocker.patch.object(IntegrationResourceApiAdapter, "save_all_integrations")
    await integration_client.save_all_integrations([integration_update])
    assert mock.called
    mock.assert_called_with([integration_update])


@pytest.mark.asyncio
async def test_get_all_integrations(mocker, integration_client, integration):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_all_integrations",
        return_value=[integration],
    )
    result = await integration_client.get_all_integrations()
    assert mock.called
    mock.assert_called_with(category=None, active_only=None)
    assert result == [integration]


@pytest.mark.asyncio
async def test_get_all_integrations_with_filters(
    mocker, integration_client, integration
):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_all_integrations",
        return_value=[integration],
    )
    result = await integration_client.get_all_integrations(
        category=CATEGORY, active_only=True
    )
    assert mock.called
    mock.assert_called_with(category=CATEGORY, active_only=True)
    assert result == [integration]


@pytest.mark.asyncio
async def test_get_providers_and_integrations(mocker, integration_client):
    expected_result = {"providers": [], "integrations": []}
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_providers_and_integrations",
        return_value=expected_result,
    )
    result = await integration_client.get_providers_and_integrations()
    assert mock.called
    mock.assert_called_with(type=None, active_only=None)
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_providers_and_integrations_with_filters(mocker, integration_client):
    expected_result = {"providers": [], "integrations": []}
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_providers_and_integrations",
        return_value=expected_result,
    )
    result = await integration_client.get_providers_and_integrations(
        integration_type="test", active_only=True
    )
    assert mock.called
    mock.assert_called_with(type="test", active_only=True)
    assert result == expected_result


@pytest.mark.asyncio
async def test_put_tag_for_integration(mocker, integration_client, tag):
    mock = mocker.patch.object(IntegrationResourceApiAdapter, "put_tag_for_integration")
    await integration_client.put_tag_for_integration(
        [tag], INTEGRATION_API_NAME, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(
        name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME, tag=[tag]
    )


@pytest.mark.asyncio
async def test_get_tags_for_integration(mocker, integration_client, tag):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_tags_for_integration",
        return_value=[tag],
    )
    result = await integration_client.get_tags_for_integration(
        INTEGRATION_API_NAME, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(
        name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME
    )
    assert result == [tag]


@pytest.mark.asyncio
async def test_delete_tag_for_integration(mocker, integration_client, tag):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter, "delete_tag_for_integration"
    )
    await integration_client.delete_tag_for_integration(
        [tag], INTEGRATION_API_NAME, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(
        name=INTEGRATION_API_NAME, integration_name=INTEGRATION_NAME, tag=[tag]
    )


@pytest.mark.asyncio
async def test_put_tag_for_integration_provider(mocker, integration_client, tag):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter, "put_tag_for_integration_provider"
    )
    await integration_client.put_tag_for_integration_provider([tag], INTEGRATION_NAME)
    assert mock.called
    mock.assert_called_with([tag], INTEGRATION_NAME)


@pytest.mark.asyncio
async def test_get_tags_for_integration_provider(mocker, integration_client, tag):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_tags_for_integration_provider",
        return_value=[tag],
    )
    result = await integration_client.get_tags_for_integration_provider(
        INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME)
    assert result == [tag]


@pytest.mark.asyncio
async def test_delete_tag_for_integration_provider(mocker, integration_client, tag):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter, "delete_tag_for_integration_provider"
    )
    await integration_client.delete_tag_for_integration_provider(
        [tag], INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with([tag], INTEGRATION_NAME)


@pytest.mark.asyncio
async def test_get_token_usage_for_integration(mocker, integration_client):
    expected_usage = 100
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_token_usage_for_integration",
        return_value=expected_usage,
    )
    result = await integration_client.get_token_usage_for_integration(
        INTEGRATION_API_NAME, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_API_NAME, INTEGRATION_NAME)
    assert result == expected_usage


@pytest.mark.asyncio
async def test_get_token_usage_for_integration_provider(mocker, integration_client):
    expected_usage = {"total": "200", "used": "100"}
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_token_usage_for_integration_provider",
        return_value=expected_usage,
    )
    result = await integration_client.get_token_usage_for_integration_provider(
        INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_NAME)
    assert result == expected_usage


@pytest.mark.asyncio
async def test_register_token_usage(mocker, integration_client):
    tokens = 50
    mock = mocker.patch.object(IntegrationResourceApiAdapter, "register_token_usage")
    await integration_client.register_token_usage(
        INTEGRATION_API_NAME, INTEGRATION_NAME, tokens
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_API_NAME, INTEGRATION_NAME, tokens)


@pytest.mark.asyncio
async def test_associate_prompt_with_integration(mocker, integration_client):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter, "associate_prompt_with_integration"
    )
    await integration_client.associate_prompt_with_integration(
        AI_PROMPT, INTEGRATION_PROVIDER, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(AI_PROMPT, INTEGRATION_PROVIDER, INTEGRATION_NAME)


@pytest.mark.asyncio
async def test_get_prompts_with_integration(mocker, integration_client):
    expected_prompts = [
        MessageTemplateAdapter(name="prompt1"),
        MessageTemplateAdapter(name="prompt2"),
    ]
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_prompts_with_integration",
        return_value=expected_prompts,
    )
    result = await integration_client.get_prompts_with_integration(
        INTEGRATION_PROVIDER, INTEGRATION_NAME
    )
    assert mock.called
    mock.assert_called_with(INTEGRATION_PROVIDER, INTEGRATION_NAME)
    assert result == expected_prompts


@pytest.mark.asyncio
async def test_record_event_stats(mocker, integration_client, event_log):
    mock = mocker.patch.object(IntegrationResourceApiAdapter, "record_event_stats")
    await integration_client.record_event_stats(EVENT_TYPE, [event_log])
    assert mock.called
    mock.assert_called_with(type=EVENT_TYPE, event_log=[event_log])


@pytest.mark.asyncio
async def test_get_integration_by_category(mocker, integration_client, integration):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_all_integrations",
        return_value=[integration],
    )
    result = await integration_client.get_integration_by_category(CATEGORY, True)
    assert mock.called
    mock.assert_called_with(category=CATEGORY, active_only=True)
    assert result == [integration]


@pytest.mark.asyncio
async def test_get_active_integrations(mocker, integration_client, integration):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_all_integrations",
        return_value=[integration],
    )
    result = await integration_client.get_active_integrations()
    assert mock.called
    mock.assert_called_with(category=None, active_only=True)
    assert result == [integration]


@pytest.mark.asyncio
async def test_get_integration_provider_by_category(
    mocker, integration_client, integration_def
):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_providers",
        return_value=[integration_def],
    )
    result = await integration_client.get_integration_provider_by_category(
        CATEGORY, True
    )
    assert mock.called
    mock.assert_called_with(category=CATEGORY, active_only=True)
    assert result == [integration_def]


@pytest.mark.asyncio
async def test_get_active_integration_providers(
    mocker, integration_client, integration_def
):
    mock = mocker.patch.object(
        IntegrationResourceApiAdapter,
        "get_integration_providers",
        return_value=[integration_def],
    )
    result = await integration_client.get_active_integration_providers()
    assert mock.called
    mock.assert_called_with(category=None, active_only=True)
    assert result == [integration_def]
