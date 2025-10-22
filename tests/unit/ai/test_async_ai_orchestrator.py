import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conductor.asyncio_client.ai.orchestrator import AsyncAIOrchestrator
from conductor.asyncio_client.adapters import ApiClient

from conductor.asyncio_client.adapters.models.message_template_adapter import (
    MessageTemplateAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.exceptions import NotFoundException
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.asyncio_client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.asyncio_client.workflow.executor.workflow_executor import AsyncWorkflowExecutor
from conductor.shared.ai.configuration.interfaces.integration_config import IntegrationConfig
from conductor.shared.ai.enums import LLMProvider, VectorDB


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)

@pytest.fixture
def mock_configuration():
    return Configuration("http://localhost:8080/api")

@pytest.fixture
def mock_api_client():
    return MagicMock(spec=ApiClient)

@pytest.fixture
def mock_orkes_clients():
    return MagicMock(spec=OrkesClients)

@pytest.fixture
def mock_integration_client():
    return AsyncMock(spec=OrkesIntegrationClient)

@pytest.fixture
def mock_prompt_client():
    return AsyncMock(spec=OrkesPromptClient)

@pytest.fixture
def mock_workflow_executor():
    return AsyncMock(spec=AsyncWorkflowExecutor)

@pytest.fixture
def mock_integration_config():
    config = MagicMock(spec=IntegrationConfig)
    config.to_dict.return_value = {"api_key": "test_key", "base_url": "https://api.test.com"}
    return config

@pytest.fixture
def orchestrator(mock_configuration, mock_api_client, mock_orkes_clients,
                    mock_integration_client, mock_prompt_client, mock_workflow_executor):
    with patch('conductor.asyncio_client.ai.orchestrator.OrkesClients', return_value=mock_orkes_clients):
        mock_orkes_clients.get_integration_client.return_value = mock_integration_client
        mock_orkes_clients.get_prompt_client.return_value = mock_prompt_client
        mock_orkes_clients.get_workflow_executor.return_value = mock_workflow_executor

        orchestrator = AsyncAIOrchestrator(api_configuration=mock_configuration, api_client=mock_api_client)
        orchestrator.integration_client = mock_integration_client
        orchestrator.prompt_client = mock_prompt_client
        orchestrator.workflow_executor = mock_workflow_executor

        return orchestrator

def test_init_with_default_prompt_test_workflow_name(mock_configuration, mock_api_client, mock_orkes_clients,
                                                    mock_integration_client, mock_prompt_client,
                                                    mock_workflow_executor):
    with patch('conductor.asyncio_client.ai.orchestrator.OrkesClients', return_value=mock_orkes_clients):
        mock_orkes_clients.get_integration_client.return_value = mock_integration_client
        mock_orkes_clients.get_prompt_client.return_value = mock_prompt_client
        mock_orkes_clients.get_workflow_executor.return_value = mock_workflow_executor

        orchestrator = AsyncAIOrchestrator(api_configuration=mock_configuration, api_client=mock_api_client)

        assert orchestrator.integration_client == mock_integration_client
        assert orchestrator.prompt_client == mock_prompt_client
        assert orchestrator.workflow_executor == mock_workflow_executor
        assert orchestrator.prompt_test_workflow_name.startswith("prompt_test_")

def test_init_with_custom_prompt_test_workflow_name(mock_configuration, mock_api_client, mock_orkes_clients,
                                                    mock_integration_client, mock_prompt_client,
                                                    mock_workflow_executor):
    custom_name = "custom_test_workflow"

    with patch('conductor.asyncio_client.ai.orchestrator.OrkesClients', return_value=mock_orkes_clients):
        mock_orkes_clients.get_integration_client.return_value = mock_integration_client
        mock_orkes_clients.get_prompt_client.return_value = mock_prompt_client
        mock_orkes_clients.get_workflow_executor.return_value = mock_workflow_executor

        orchestrator = AsyncAIOrchestrator(api_configuration=mock_configuration, api_client=mock_api_client, prompt_test_workflow_name=custom_name)

        assert orchestrator.prompt_test_workflow_name == custom_name

@pytest.mark.asyncio
async def test_add_prompt_template_success(orchestrator, mock_prompt_client):
    name = "test_prompt"
    template = "Hello ${name}, how are you?"
    description = "A test prompt template"

    result = await orchestrator.add_prompt_template(name, template, description)

    mock_prompt_client.save_prompt.assert_called_once_with(name, description, template)
    assert result == orchestrator

@pytest.mark.asyncio
async def test_get_prompt_template_success(orchestrator, mock_prompt_client):
    template_name = "test_prompt"
    expected_template = MessageTemplateAdapter(name=template_name, description="Test")
    mock_prompt_client.get_prompt.return_value = expected_template

    result = await orchestrator.get_prompt_template(template_name)

    mock_prompt_client.get_prompt.assert_called_once_with(template_name)
    assert result == expected_template

@pytest.mark.asyncio
async def test_get_prompt_template_not_found(orchestrator, mock_prompt_client):
    template_name = "non_existent_prompt"
    mock_prompt_client.get_prompt.side_effect = NotFoundException("Not found")

    result = await orchestrator.get_prompt_template(template_name)

    mock_prompt_client.get_prompt.assert_called_once_with(template_name)
    assert result is None

@pytest.mark.asyncio
async def test_associate_prompt_template_success(orchestrator, mock_integration_client):
    name = "test_prompt"
    ai_integration = "openai_integration"
    ai_models = ["gpt-4", "gpt-3.5-turbo"]

    await orchestrator.associate_prompt_template(name, ai_integration, ai_models)

    assert mock_integration_client.associate_prompt_with_integration.call_count == 2
    mock_integration_client.associate_prompt_with_integration.assert_any_call(
        ai_integration, "gpt-4", name
    )
    mock_integration_client.associate_prompt_with_integration.assert_any_call(
        ai_integration, "gpt-3.5-turbo", name
    )

@pytest.mark.asyncio
async def test_test_prompt_template_success(orchestrator, mock_prompt_client):
    text = "Hello ${name}, how are you?"
    variables = {"name": "John"}
    ai_integration = "openai_integration"
    text_complete_model = "gpt-4"
    stop_words = ["stop", "end"]
    max_tokens = 150
    temperature = 0.7
    top_p = 0.9

    expected_result = "Hello John, how are you? I'm doing well, thank you!"
    mock_prompt_client.test_prompt.return_value = expected_result

    result = await orchestrator.test_prompt_template(
        text, variables, ai_integration, text_complete_model,
        stop_words, max_tokens, temperature, top_p
    )

    mock_prompt_client.test_prompt.assert_called_once_with(
        text, variables, ai_integration, text_complete_model,
        temperature, top_p, stop_words
    )
    assert result == expected_result

@pytest.mark.asyncio
async def test_test_prompt_template_with_default_stop_words(orchestrator, mock_prompt_client):
    text = "Hello ${name}, how are you?"
    variables = {"name": "John"}
    ai_integration = "openai_integration"
    text_complete_model = "gpt-4"

    expected_result = "Hello John, how are you? I'm doing well, thank you!"
    mock_prompt_client.test_prompt.return_value = expected_result

    result = await orchestrator.test_prompt_template(
        text, variables, ai_integration, text_complete_model
    )

    mock_prompt_client.test_prompt.assert_called_once_with(
        text, variables, ai_integration, text_complete_model,
        0, 1, []
    )
    assert result == expected_result

@pytest.mark.asyncio
async def test_add_ai_integration_new_integration(orchestrator, mock_integration_client,
                                                    mock_integration_config):
    ai_integration_name = "test_openai"
    provider = LLMProvider.OPEN_AI
    models = ["gpt-4", "gpt-3.5-turbo"]
    description = "Test OpenAI integration"
    overwrite = False

    mock_integration_client.get_integration_provider.return_value = None
    mock_integration_client.get_integration_api.return_value = None

    await orchestrator.add_ai_integration(
        ai_integration_name, provider, models, description, mock_integration_config, overwrite
    )

    mock_integration_client.save_integration_provider.assert_called_once()
    call_args = mock_integration_client.save_integration_provider.call_args
    assert call_args[0][0] == ai_integration_name

    assert mock_integration_client.save_integration_api.call_count == 2

@pytest.mark.asyncio
async def test_add_ai_integration_existing_integration_with_overwrite(orchestrator,
                                                                        mock_integration_client,
                                                                        mock_integration_config):
    ai_integration_name = "test_openai"
    provider = LLMProvider.OPEN_AI
    models = ["gpt-4"]
    description = "Test OpenAI integration"
    overwrite = True

    existing_integration = MagicMock()
    mock_integration_client.get_integration_provider.return_value = existing_integration
    mock_integration_client.get_integration_api.return_value = None

    await orchestrator.add_ai_integration(
        ai_integration_name, provider, models, description, mock_integration_config, overwrite
    )

    mock_integration_client.save_integration_provider.assert_called_once()
    mock_integration_client.save_integration_api.assert_called_once()

@pytest.mark.asyncio
async def test_add_ai_integration_existing_integration_without_overwrite(orchestrator,
                                                                        mock_integration_client,
                                                                        mock_integration_config):
    ai_integration_name = "test_openai"
    provider = LLMProvider.OPEN_AI
    models = ["gpt-4"]
    description = "Test OpenAI integration"
    overwrite = False

    existing_integration = MagicMock()
    mock_integration_client.get_integration_provider.return_value = existing_integration
    mock_integration_client.get_integration_api.return_value = None

    await orchestrator.add_ai_integration(
        ai_integration_name, provider, models, description, mock_integration_config, overwrite
    )

    mock_integration_client.save_integration_provider.assert_not_called()
    mock_integration_client.save_integration_api.assert_called_once()

@pytest.mark.asyncio
async def test_add_vector_store_new_integration(orchestrator, mock_integration_client,
                                                mock_integration_config):
    db_integration_name = "test_pinecone"
    provider = VectorDB.PINECONE_DB
    indices = ["index1", "index2"]
    description = "Test Pinecone integration"
    overwrite = False

    # Mock that integration doesn't exist
    mock_integration_client.get_integration.return_value = None
    mock_integration_client.get_integration_api.return_value = None

    await orchestrator.add_vector_store(
        db_integration_name, provider, indices, mock_integration_config, description, overwrite
    )

    mock_integration_client.save_integration.assert_called_once()
    call_args = mock_integration_client.save_integration.call_args
    assert call_args[0][0] == db_integration_name

    assert mock_integration_client.save_integration_api.call_count == 2

@pytest.mark.asyncio
async def test_add_vector_store_with_default_description(orchestrator, mock_integration_client,
                                                        mock_integration_config):
    db_integration_name = "test_pinecone"
    provider = VectorDB.PINECONE_DB
    indices = ["index1"]
    overwrite = False

    mock_integration_client.get_integration.return_value = None
    mock_integration_client.get_integration_api.return_value = None

    await orchestrator.add_vector_store(
        db_integration_name, provider, indices, mock_integration_config, overwrite=overwrite
    )

    mock_integration_client.save_integration.assert_called_once()
    call_args = mock_integration_client.save_integration.call_args
    assert call_args[0][0] == db_integration_name

@pytest.mark.asyncio
async def test_get_token_used_success(orchestrator, mock_integration_client):
    ai_integration = "test_openai"
    expected_tokens = 1500
    mock_integration_client.get_token_usage_for_integration_provider.return_value = expected_tokens

    result = await orchestrator.get_token_used(ai_integration)

    mock_integration_client.get_token_usage_for_integration_provider.assert_called_once_with(ai_integration)
    assert result == expected_tokens

@pytest.mark.asyncio
async def test_get_token_used_by_model_success(orchestrator, mock_integration_client):
    ai_integration = "test_openai"
    model = "gpt-4"
    expected_tokens = 750
    mock_integration_client.get_token_usage_for_integration.return_value = expected_tokens

    result = await orchestrator.get_token_used_by_model(ai_integration, model)

    mock_integration_client.get_token_usage_for_integration.assert_called_once_with(ai_integration, model)
    assert result == expected_tokens

@pytest.mark.asyncio
async def test_add_prompt_template_error_handling(orchestrator, mock_prompt_client):
    name = "test_prompt"
    template = "Hello ${name}"
    description = "Test prompt"

    mock_prompt_client.save_prompt.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        await orchestrator.add_prompt_template(name, template, description)

@pytest.mark.asyncio
async def test_associate_prompt_template_error_handling(orchestrator, mock_integration_client):
    name = "test_prompt"
    ai_integration = "test_openai"
    ai_models = ["gpt-4"]

    mock_integration_client.associate_prompt_with_integration.side_effect = Exception("Association failed")

    with pytest.raises(Exception, match="Association failed"):
        await orchestrator.associate_prompt_template(name, ai_integration, ai_models)

@pytest.mark.asyncio
async def test_test_prompt_template_error_handling(orchestrator, mock_prompt_client):
    text = "Hello ${name}"
    variables = {"name": "John"}
    ai_integration = "test_openai"
    text_complete_model = "gpt-4"

    mock_prompt_client.test_prompt.side_effect = Exception("Test failed")

    with pytest.raises(Exception, match="Test failed"):
        await orchestrator.test_prompt_template(text, variables, ai_integration, text_complete_model)

def test_prompt_test_workflow_name_generation(mock_configuration, mock_orkes_clients,
                                            mock_integration_client, mock_prompt_client,
                                            mock_workflow_executor):
    with patch('conductor.asyncio_client.ai.orchestrator.OrkesClients', return_value=mock_orkes_clients):
        mock_orkes_clients.get_integration_client.return_value = mock_integration_client
        mock_orkes_clients.get_prompt_client.return_value = mock_prompt_client
        mock_orkes_clients.get_workflow_executor.return_value = mock_workflow_executor

        orchestrator = AsyncAIOrchestrator(api_configuration=mock_configuration, api_client=mock_api_client)

        assert orchestrator.prompt_test_workflow_name.startswith("prompt_test_")
        uuid_part = orchestrator.prompt_test_workflow_name[len("prompt_test_"):]
        assert len(uuid_part) == 36

@pytest.mark.asyncio
async def test_add_ai_integration_with_empty_models_list(orchestrator, mock_integration_client,
                                                        mock_integration_config):
    ai_integration_name = "test_openai"
    provider = LLMProvider.OPEN_AI
    models = []
    description = "Test OpenAI integration"
    overwrite = False

    mock_integration_client.get_integration_provider.return_value = None

    await orchestrator.add_ai_integration(
        ai_integration_name, provider, models, description, mock_integration_config, overwrite
    )

    mock_integration_client.save_integration_provider.assert_called_once()
    mock_integration_client.save_integration_api.assert_not_called()

@pytest.mark.asyncio
async def test_add_vector_store_with_empty_indices_list(orchestrator, mock_integration_client,
                                                        mock_integration_config):
    db_integration_name = "test_pinecone"
    provider = VectorDB.PINECONE_DB
    indices = []
    description = "Test Pinecone integration"
    overwrite = False

    mock_integration_client.get_integration.return_value = None

    await orchestrator.add_vector_store(
        db_integration_name, provider, indices, mock_integration_config, description, overwrite
    )

    mock_integration_client.save_integration.assert_called_once()
    mock_integration_client.save_integration_api.assert_not_called()
