
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.integration_adapter import IntegrationAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("Integration")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_integration_deserialization(raw_server_json, server_json):
    integration_adapter = IntegrationAdapter.from_json(raw_server_json)
    assert integration_adapter.to_dict() == server_json


def test_integration_serialization(raw_server_json, server_json):
    assert sorted(IntegrationAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_integration_invalid_data():
    with pytest.raises(ValidationError):
        IntegrationAdapter(configuration="invalid_configuration")
