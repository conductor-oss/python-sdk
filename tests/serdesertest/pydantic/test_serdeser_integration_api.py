import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.integration_api_adapter import IntegrationApiAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("IntegrationApi")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_integration_api_deserialization(raw_server_json, server_json):
    action_adapter = IntegrationApiAdapter.from_json(raw_server_json)
    assert action_adapter.to_dict() == server_json


def test_integration_api_serialization(raw_server_json, server_json):
    assert sorted(IntegrationApiAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_integration_api_invalid_data():
    with pytest.raises(ValidationError):
        IntegrationApiAdapter(configuration="invalid_configuration")
