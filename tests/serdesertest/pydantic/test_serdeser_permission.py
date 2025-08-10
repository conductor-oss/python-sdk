
import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.permission_adapter import PermissionAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("Permission")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_permission_deserialization(raw_server_json, server_json):
    permission_adapter = PermissionAdapter.from_json(raw_server_json)
    assert permission_adapter.to_dict() == server_json


def test_permission_serialization(raw_server_json, server_json):
    assert sorted(PermissionAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_permission_invalid_data():
    with pytest.raises(ValidationError):
        PermissionAdapter(name={"invalid_name"})
