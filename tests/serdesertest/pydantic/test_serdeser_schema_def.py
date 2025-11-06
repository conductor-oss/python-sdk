import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.schema_def_adapter import SchemaDefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("SchemaDef")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_schema_def_deserialization(raw_server_json, server_json):
    schema_def_adapter = SchemaDefAdapter.from_json(raw_server_json)
    assert schema_def_adapter.to_dict() == server_json


def test_schema_def_serialization(raw_server_json, server_json):
    assert sorted(SchemaDefAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_schema_def_invalid_data():
    with pytest.raises(ValidationError):
        SchemaDefAdapter(owner_app={"invalid_name"})
