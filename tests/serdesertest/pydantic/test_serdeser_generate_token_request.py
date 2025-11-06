import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.generate_token_request_adapter import GenerateTokenRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("GenerateTokenRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_generate_token_request_deserialization(raw_server_json, server_json):
    action_adapter = GenerateTokenRequestAdapter.from_json(raw_server_json)
    assert action_adapter.to_dict() == server_json


def test_generate_token_request_serialization(raw_server_json, server_json):
    assert sorted(GenerateTokenRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_generate_token_request_invalid_data():
    with pytest.raises(ValidationError):
        GenerateTokenRequestAdapter(key_id="invalid_id")
