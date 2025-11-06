import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.integration_update_adapter import IntegrationUpdateAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("IntegrationUpdate")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_integration_update_deserialization(raw_server_json, server_json):
    integration_update_adapter = IntegrationUpdateAdapter.from_json(raw_server_json)
    assert integration_update_adapter.to_dict() == server_json


def test_integration_update_serialization(raw_server_json, server_json):
    assert sorted(IntegrationUpdateAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_integration_update_invalid_data():
    with pytest.raises(ValidationError):
        IntegrationUpdateAdapter(configuration="invalid_configuration")
