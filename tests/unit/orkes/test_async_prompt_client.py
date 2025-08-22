import logging

import pytest

from conductor.asyncio_client.adapters.api.prompt_resource_api import (
    PromptResourceApiAdapter,
)
from conductor.asyncio_client.adapters.models.message_template_adapter import (
    MessageTemplateAdapter,
)
from conductor.asyncio_client.adapters.models.prompt_template_test_request_adapter import (
    PromptTemplateTestRequestAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.asyncio_client.adapters import ApiClient

TEMPLATE_NAME = "test_template"
TEMPLATE_DESCRIPTION = "Test template description"
TEMPLATE_BODY = "Hello {{name}}, welcome to {{platform}}!"
MODEL_NAME = "gpt-4"
TAG_KEY = "category"
TAG_VALUE = "greeting"
TEST_INPUT = {"name": "John", "platform": "Conductor"}


@pytest.fixture(scope="module")
def prompt_client():
    configuration = Configuration("http://localhost:8080/api")
    api_client = ApiClient(configuration)
    return OrkesPromptClient(configuration, api_client=api_client)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def message_template():
    return MessageTemplateAdapter(
        name=TEMPLATE_NAME,
        description=TEMPLATE_DESCRIPTION,
        template=TEMPLATE_BODY,
    )


@pytest.fixture
def prompt_template_test_request():
    return PromptTemplateTestRequestAdapter()


@pytest.fixture
def tag():
    return TagAdapter(key=TAG_KEY, value=TAG_VALUE, type="METADATA")


def test_init(prompt_client):
    message = "prompt_api is not of type PromptResourceApiAdapter"
    assert isinstance(prompt_client.prompt_api, PromptResourceApiAdapter), message


@pytest.mark.asyncio
async def test_save_message_template(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApiAdapter, "save_message_template")
    await prompt_client.save_message_template(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY, [MODEL_NAME]
    )
    assert mock.called
    mock.assert_called_with(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY, models=[MODEL_NAME]
    )


@pytest.mark.asyncio
async def test_save_message_template_without_models(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApiAdapter, "save_message_template")
    await prompt_client.save_message_template(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY
    )
    assert mock.called
    mock.assert_called_with(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY, models=None
    )


@pytest.mark.asyncio
async def test_get_message_template(mocker, prompt_client, message_template):
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_template",
        return_value=message_template,
    )
    result = await prompt_client.get_message_template(TEMPLATE_NAME)
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME)
    assert result == message_template


@pytest.mark.asyncio
async def test_get_message_templates(mocker, prompt_client, message_template):
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=[message_template],
    )
    result = await prompt_client.get_message_templates()
    assert mock.called
    mock.assert_called_with()
    assert result == [message_template]


@pytest.mark.asyncio
async def test_delete_message_template(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApiAdapter, "delete_message_template")
    await prompt_client.delete_message_template(TEMPLATE_NAME)
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME)


@pytest.mark.asyncio
async def test_create_message_templates(mocker, prompt_client, message_template):
    mock = mocker.patch.object(PromptResourceApiAdapter, "create_message_templates")
    await prompt_client.create_message_templates([message_template])
    assert mock.called
    mock.assert_called_with([message_template])


@pytest.mark.asyncio
async def test_test_message_template(
    mocker, prompt_client, prompt_template_test_request
):
    expected_result = "Hello John, welcome to Conductor!"
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "test_message_template",
        return_value=expected_result,
    )
    result = await prompt_client.test_message_template(prompt_template_test_request)
    assert mock.called
    mock.assert_called_with(prompt_template_test_request)
    assert result == expected_result


@pytest.mark.asyncio
async def test_put_tag_for_prompt_template(mocker, prompt_client, tag):
    mock = mocker.patch.object(PromptResourceApiAdapter, "put_tag_for_prompt_template")
    await prompt_client.put_tag_for_prompt_template(TEMPLATE_NAME, [tag])
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME, [tag])


@pytest.mark.asyncio
async def test_get_tags_for_prompt_template(mocker, prompt_client, tag):
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_tags_for_prompt_template",
        return_value=[tag],
    )
    result = await prompt_client.get_tags_for_prompt_template(TEMPLATE_NAME)
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME)
    assert result == [tag]


@pytest.mark.asyncio
async def test_delete_tag_for_prompt_template(mocker, prompt_client, tag):
    mock = mocker.patch.object(
        PromptResourceApiAdapter, "delete_tag_for_prompt_template"
    )
    await prompt_client.delete_tag_for_prompt_template(TEMPLATE_NAME, [tag])
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME, [tag])


@pytest.mark.asyncio
async def test_create_simple_template(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApiAdapter, "save_message_template")
    await prompt_client.create_simple_template(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY
    )
    assert mock.called
    mock.assert_called_with(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY, models=None
    )


@pytest.mark.asyncio
async def test_update_template(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApiAdapter, "save_message_template")
    await prompt_client.update_template(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY, [MODEL_NAME]
    )
    assert mock.called
    mock.assert_called_with(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY, models=[MODEL_NAME]
    )


@pytest.mark.asyncio
async def test_template_exists_true(mocker, prompt_client, message_template):
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_template",
        return_value=message_template,
    )
    result = await prompt_client.template_exists(TEMPLATE_NAME)
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME)
    assert result is True


@pytest.mark.asyncio
async def test_template_exists_false(mocker, prompt_client):
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_template",
        side_effect=ApiException(status=404),
    )
    result = await prompt_client.template_exists(TEMPLATE_NAME)
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME)
    assert result is False


@pytest.mark.asyncio
async def test_get_templates_by_tag(mocker, prompt_client, message_template, tag):
    mock_get_templates = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=[message_template],
    )
    mock_get_tags = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_tags_for_prompt_template",
        return_value=[tag],
    )
    result = await prompt_client.get_templates_by_tag(TAG_KEY, TAG_VALUE)
    assert mock_get_templates.called
    assert mock_get_tags.called
    assert result == [message_template]


@pytest.mark.asyncio
async def test_get_templates_by_tag_no_match(mocker, prompt_client, message_template):
    mock_get_templates = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=[message_template],
    )
    mock_get_tags = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_tags_for_prompt_template",
        return_value=[],
    )
    result = await prompt_client.get_templates_by_tag(TAG_KEY, TAG_VALUE)
    assert mock_get_templates.called
    assert mock_get_tags.called
    assert result == []


@pytest.mark.asyncio
async def test_clone_template(mocker, prompt_client, message_template):
    mock_get_template = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_template",
        return_value=message_template,
    )
    mock_save_template = mocker.patch.object(
        PromptResourceApiAdapter, "save_message_template"
    )

    target_name = "cloned_template"
    await prompt_client.clone_template(TEMPLATE_NAME, target_name)

    assert mock_get_template.called
    mock_get_template.assert_called_with(TEMPLATE_NAME)
    assert mock_save_template.called
    mock_save_template.assert_called_with(
        target_name,
        f"Clone of {TEMPLATE_DESCRIPTION}",
        TEMPLATE_BODY,
        models=None,
    )


@pytest.mark.asyncio
async def test_clone_template_with_description(mocker, prompt_client, message_template):
    mock_get_template = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_template",
        return_value=message_template,
    )
    mock_save_template = mocker.patch.object(
        PromptResourceApiAdapter, "save_message_template"
    )

    target_name = "cloned_template"
    new_description = "Custom description"
    await prompt_client.clone_template(TEMPLATE_NAME, target_name, new_description)

    assert mock_get_template.called
    mock_get_template.assert_called_with(TEMPLATE_NAME)
    assert mock_save_template.called
    mock_save_template.assert_called_with(
        target_name,
        new_description,
        TEMPLATE_BODY,
        models=None,
    )


@pytest.mark.asyncio
async def test_bulk_delete_templates(mocker, prompt_client):
    template_names = ["template1", "template2", "template3"]
    mock_delete = mocker.patch.object(
        PromptResourceApiAdapter, "delete_message_template"
    )

    await prompt_client.bulk_delete_templates(template_names)

    assert mock_delete.call_count == 3
    expected_calls = [mocker.call(name) for name in template_names]
    mock_delete.assert_has_calls(expected_calls)


@pytest.mark.asyncio
async def test_bulk_delete_templates_with_exception(mocker, prompt_client):
    template_names = ["template1", "template2", "template3"]
    mock_delete = mocker.patch.object(
        PromptResourceApiAdapter,
        "delete_message_template",
        side_effect=[None, ApiException(status=404), None],
    )

    await prompt_client.bulk_delete_templates(template_names)

    assert mock_delete.call_count == 3


@pytest.mark.asyncio
async def test_save_prompt(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApiAdapter, "save_message_template")
    await prompt_client.save_prompt(TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY)
    assert mock.called
    mock.assert_called_with(
        TEMPLATE_NAME, TEMPLATE_DESCRIPTION, TEMPLATE_BODY, models=None
    )


@pytest.mark.asyncio
async def test_get_prompt(mocker, prompt_client, message_template):
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_template",
        return_value=message_template,
    )
    result = await prompt_client.get_prompt(TEMPLATE_NAME)
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME)
    assert result == message_template


@pytest.mark.asyncio
async def test_delete_prompt(mocker, prompt_client):
    mock = mocker.patch.object(PromptResourceApiAdapter, "delete_message_template")
    await prompt_client.delete_prompt(TEMPLATE_NAME)
    assert mock.called
    mock.assert_called_with(TEMPLATE_NAME)


@pytest.mark.asyncio
async def test_list_prompts(mocker, prompt_client, message_template):
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=[message_template],
    )
    result = await prompt_client.list_prompts()
    assert mock.called
    mock.assert_called_with()
    assert result == [message_template]


@pytest.mark.asyncio
async def test_get_template_count(mocker, prompt_client):
    templates = [
        MessageTemplateAdapter(name="template1"),
        MessageTemplateAdapter(name="template2"),
        MessageTemplateAdapter(name="template3"),
    ]
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=templates,
    )
    result = await prompt_client.get_template_count()
    assert mock.called
    mock.assert_called_with()
    assert result == 3


@pytest.mark.asyncio
async def test_search_templates_by_name(mocker, prompt_client):
    templates = [
        MessageTemplateAdapter(name="greeting_template"),
        MessageTemplateAdapter(name="farewell_template"),
        MessageTemplateAdapter(name="welcome_template"),
    ]
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=templates,
    )
    result = await prompt_client.search_templates_by_name("greeting")
    assert mock.called
    mock.assert_called_with()
    assert len(result) == 1
    assert result[0].name == "greeting_template"


@pytest.mark.asyncio
async def test_search_templates_by_name_case_insensitive(mocker, prompt_client):
    templates = [
        MessageTemplateAdapter(name="GREETING_TEMPLATE"),
        MessageTemplateAdapter(name="farewell_template"),
    ]
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=templates,
    )
    result = await prompt_client.search_templates_by_name("greeting")
    assert mock.called
    mock.assert_called_with()
    assert len(result) == 1
    assert result[0].name == "GREETING_TEMPLATE"


@pytest.mark.asyncio
async def test_get_templates_with_model(mocker, prompt_client):
    templates = [
        MessageTemplateAdapter(name="template1"),
        MessageTemplateAdapter(name="template2"),
        MessageTemplateAdapter(name="template3"),
    ]
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=templates,
    )
    result = await prompt_client.get_templates_with_model("gpt-4")
    assert mock.called
    mock.assert_called_with()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_templates_with_model_no_match(mocker, prompt_client):
    templates = [
        MessageTemplateAdapter(name="template1"),
        MessageTemplateAdapter(name="template2"),
    ]
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=templates,
    )
    result = await prompt_client.get_templates_with_model("gpt-4")
    assert mock.called
    mock.assert_called_with()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_templates_with_model_no_models_attribute(mocker, prompt_client):
    templates = [
        MessageTemplateAdapter(name="template1"),
        MessageTemplateAdapter(name="template2"),
    ]
    mock = mocker.patch.object(
        PromptResourceApiAdapter,
        "get_message_templates",
        return_value=templates,
    )
    result = await prompt_client.get_templates_with_model("gpt-4")
    assert mock.called
    mock.assert_called_with()
    assert len(result) == 0
