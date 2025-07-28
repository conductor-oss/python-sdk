import json

import pytest

from conductor.client.http.models.prompt_test_request import PromptTemplateTestRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("PromptTemplateTestRequest"))


def test_prompt_template_test_request_serde(server_json):
    model_obj = PromptTemplateTestRequest(
        llm_provider=server_json.get("llmProvider"),
        model=server_json.get("model"),
        prompt=server_json.get("prompt"),
        prompt_variables=server_json.get("promptVariables"),
        stop_words=server_json.get("stopWords"),
        temperature=server_json.get("temperature"),
        top_p=server_json.get("topP"),
    )
    assert server_json.get("llmProvider") == model_obj.llm_provider
    assert server_json.get("model") == model_obj.model
    assert server_json.get("prompt") == model_obj.prompt
    assert server_json.get("promptVariables") == model_obj.prompt_variables
    assert server_json.get("stopWords") == model_obj.stop_words
    assert server_json.get("temperature") == model_obj.temperature
    assert server_json.get("topP") == model_obj.top_p
    model_json = model_obj.to_dict()
    converted_model_json = {}
    for key, value in model_json.items():
        camel_key = model_obj.attribute_map.get(key, key)
        converted_model_json[camel_key] = value
    for key, value in server_json.items():
        assert key in converted_model_json
        assert value == converted_model_json[key]
