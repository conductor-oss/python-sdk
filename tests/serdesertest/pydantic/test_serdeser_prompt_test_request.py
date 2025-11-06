
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.prompt_template_test_request_adapter import PromptTemplateTestRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("PromptTemplateTestRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_prompt_test_request_deserialization(raw_server_json, server_json):
    prompt_test_request_adapter = PromptTemplateTestRequestAdapter.from_json(raw_server_json)
    assert prompt_test_request_adapter.to_dict() == server_json


def test_prompt_test_request_serialization(raw_server_json, server_json):
    assert sorted(PromptTemplateTestRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_prompt_test_request_invalid_data():
    with pytest.raises(ValidationError):
        PromptTemplateTestRequestAdapter(llm_provider={"invalid_provider"})
