import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("Group")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_group_deserialization(raw_server_json, server_json):
    action_adapter = GroupAdapter.from_json(raw_server_json)
    assert action_adapter.to_dict() == server_json


def test_group_serialization(raw_server_json, server_json):
    assert sorted(GroupAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_group_invalid_data():
    with pytest.raises(ValidationError):
        GroupAdapter(default_access="invalid_access")
