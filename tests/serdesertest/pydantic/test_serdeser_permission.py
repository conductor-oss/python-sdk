import json

import pytest

from conductor.asyncio_client.adapters.models.permission_adapter import PermissionAdapter
from conductor.client.http.models.permission import Permission
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("Permission"))


def test_permission_serde(server_json):
    permission_obj = Permission(name=server_json.get("name"))
    assert permission_obj.name == server_json.get("name")
    serialized_json = permission_obj.to_dict()
    assert serialized_json.get("name") == server_json.get("name")
    for key in server_json:
        python_key = key
        assert python_key in serialized_json
    assert len(serialized_json) == len(server_json)
