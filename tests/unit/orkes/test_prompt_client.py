import logging
import pytest

from conductor.client.codegen.rest import ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.prompt_resource_api import PromptResourceApi
from conductor.client.http.models.message_template import MessageTemplate
from conductor.client.http.models.prompt_template_test_request import PromptTemplateTestRequest
from conductor.client.http.models.tag import Tag
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient

PROMPT_NAME = "test_prompt"
PROMPT_DESCRIPTION = "Test prompt description"
PROMPT_TEMPLATE = "Hello {{name}}, welcome to {{place}}"
AI_INTEGRATION = "openai"
MODEL_NAME = "gpt-4"


@pytest.fixture(scope="module")
def prompt_client():
    configuration = Configuration("http://localhost:8080/api")
    return OrkesPromptClient(configuration)


@pytest.fixture(scope="module")
def message_template():
    template = MessageTemplate()
    template.name = PROMPT_NAME
    template.description = PROMPT_DESCRIPTION
    template.template = PROMPT_TEMPLATE
    return template


@pytest.fixture(scope="module")
def tag_list():
    return [Tag(key="env", value="prod"), Tag(key="team", value="platform")]


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def test_init(prompt_client):
    message = "prompt_api is not of type PromptResourceApi"
    assert isinstance(prompt_client._prompt_api, PromptResourceApi), message


def test_save_prompt(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "save_message_template")
    prompt_client.save_prompt(PROMPT_NAME, PROMPT_DESCRIPTION, PROMPT_TEMPLATE)
    mock.assert_called_with(body=PROMPT_TEMPLATE, description=PROMPT_DESCRIPTION, name=PROMPT_NAME)


def test_get_prompt(mocker, prompt_client, message_template):
    mock = mocker.patch.object(PromptResourceApi, "get_message_template")
    mock.return_value = message_template
    result = prompt_client.get_prompt(PROMPT_NAME)
    mock.assert_called_with(name=PROMPT_NAME)
    assert result == message_template


def test_get_prompt_not_found(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "get_message_template")
    api_exception = ApiException(status=404)
    mock.side_effect = api_exception
    result = prompt_client.get_prompt(PROMPT_NAME)
    mock.assert_called_with(name=PROMPT_NAME)
    assert result is None


def test_get_prompts(mocker, prompt_client, message_template):
    mock = mocker.patch.object(PromptResourceApi, "get_message_templates")
    mock.return_value = [message_template]
    result = prompt_client.get_prompts()
    assert mock.called
    assert result == [message_template]


def test_delete_prompt(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "delete_message_template")
    prompt_client.delete_prompt(PROMPT_NAME)
    mock.assert_called_with(name=PROMPT_NAME)


def test_get_tags_for_prompt_template(mocker, prompt_client, tag_list):
    mock = mocker.patch.object(PromptResourceApi, "get_tags_for_prompt_template")
    mock.return_value = tag_list
    result = prompt_client.get_tags_for_prompt_template(PROMPT_NAME)
    mock.assert_called_with(name=PROMPT_NAME)
    assert result == tag_list


def test_update_tag_for_prompt_template(mocker, prompt_client, tag_list):
    mock = mocker.patch.object(PromptResourceApi, "put_tag_for_prompt_template")
    prompt_client.update_tag_for_prompt_template(PROMPT_NAME, tag_list)
    mock.assert_called_with(body=tag_list, name=PROMPT_NAME)


def test_delete_tag_for_prompt_template(mocker, prompt_client, tag_list):
    mock = mocker.patch.object(PromptResourceApi, "delete_tag_for_prompt_template")
    prompt_client.delete_tag_for_prompt_template(PROMPT_NAME, tag_list)
    mock.assert_called_with(body=tag_list, name=PROMPT_NAME)


def test_test_prompt(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "test_message_template")
    mock.return_value = "Hello John, welcome to Paris"
    variables = {"name": "John", "place": "Paris"}
    result = prompt_client.test_prompt(
        PROMPT_TEMPLATE,
        variables,
        AI_INTEGRATION,
        MODEL_NAME,
        temperature=0.5,
        top_p=0.8
    )
    assert mock.called
    call_args = mock.call_args[0][0]
    assert isinstance(call_args, PromptTemplateTestRequest)
    assert call_args.prompt == PROMPT_TEMPLATE
    assert call_args.llm_provider == AI_INTEGRATION
    assert call_args.model == MODEL_NAME
    assert call_args.prompt_variables == variables
    assert call_args.temperature == 0.5
    assert call_args.top_p == 0.8
    assert result == "Hello John, welcome to Paris"


def test_test_prompt_with_stop_words(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "test_message_template")
    mock.return_value = "Hello John"
    variables = {"name": "John"}
    stop_words = [".", "!"]
    result = prompt_client.test_prompt(
        "Hello {{name}}",
        variables,
        AI_INTEGRATION,
        MODEL_NAME,
        stop_words=stop_words
    )
    assert mock.called
    call_args = mock.call_args[0][0]
    assert call_args.stop_words == stop_words
    assert result == "Hello John"


def test_create_message_templates(mocker, prompt_client, message_template):
    mock = mocker.patch.object(PromptResourceApi, "create_message_templates")
    templates = [message_template]
    prompt_client.create_message_templates(templates)
    mock.assert_called_with(body=templates)


def test_get_prompts_empty(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "get_message_templates")
    mock.return_value = []
    result = prompt_client.get_prompts()
    assert mock.called
    assert result == []


def test_get_tags_for_prompt_template_empty(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "get_tags_for_prompt_template")
    mock.return_value = []
    result = prompt_client.get_tags_for_prompt_template(PROMPT_NAME)
    mock.assert_called_with(name=PROMPT_NAME)
    assert result == []


def test_update_tag_for_prompt_template_empty(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "put_tag_for_prompt_template")
    prompt_client.update_tag_for_prompt_template(PROMPT_NAME, [])
    mock.assert_called_with(body=[], name=PROMPT_NAME)


def test_delete_tag_for_prompt_template_empty(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "delete_tag_for_prompt_template")
    prompt_client.delete_tag_for_prompt_template(PROMPT_NAME, [])
    mock.assert_called_with(body=[], name=PROMPT_NAME)


def test_test_prompt_default_params(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "test_message_template")
    mock.return_value = "Test output"
    variables = {"key": "value"}
    result = prompt_client.test_prompt(
        "Test {{key}}",
        variables,
        AI_INTEGRATION,
        MODEL_NAME
    )
    assert mock.called
    call_args = mock.call_args[0][0]
    assert call_args.temperature == 0.1
    assert call_args.top_p == 0.9
    assert result == "Test output"


def test_create_message_templates_multiple(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApi, "create_message_templates")
    templates = [
        MessageTemplate(name="template1"),
        MessageTemplate(name="template2"),
    ]
    prompt_client.create_message_templates(templates)
    mock.assert_called_with(body=templates)
