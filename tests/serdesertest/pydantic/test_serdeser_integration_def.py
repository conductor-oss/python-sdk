import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.integration_def_adapter import IntegrationDefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("IntegrationDef")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_integration_def_deserialization(raw_server_json, server_json):
    integration_def_adapter = IntegrationDefAdapter.from_json(raw_server_json)
    assert integration_def_adapter.to_dict() == server_json


def test_integration_def_serialization(raw_server_json, server_json):
    assert sorted(IntegrationDefAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_integration_def_invalid_data():
    with pytest.raises(ValidationError):
        IntegrationDefAdapter(configuration="invalid_configuration")
