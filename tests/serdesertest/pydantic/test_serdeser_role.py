import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.role_adapter import RoleAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("Role")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_role_deserialization(raw_server_json, server_json):
    role_adapter = RoleAdapter.from_json(raw_server_json)
    assert role_adapter.to_dict() == server_json


def test_role_serialization(raw_server_json, server_json):
    assert sorted(RoleAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_role_invalid_data():
    with pytest.raises(ValidationError):
        RoleAdapter(name={"invalid_name"})
