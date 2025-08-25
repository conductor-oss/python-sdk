import json

import pytest

from conductor.client.adapters.models.upsert_user_request_adapter import (
    RolesEnum,
    UpsertUserRequestAdapter,
)
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("UpsertUserRequest")
    return json.loads(server_json_str)


def test_upsert_user_request_serdeser(server_json):
    # 1. Deserialize JSON into model object
    model_obj = UpsertUserRequestAdapter(
        name=server_json.get("name"),
        roles=server_json.get("roles"),
        groups=server_json.get("groups"),
    )
    # 2. Verify all fields are properly populated
    # Verify name field
    assert server_json.get("name") == model_obj.name
    # Verify roles list and enum values
    roles = server_json.get("roles")
    if roles:
        assert len(roles) == len(model_obj.roles)
        for role in model_obj.roles:
            assert role in [e.value for e in RolesEnum]
            assert role in roles
    # Verify groups list
    groups = server_json.get("groups")
    if groups:
        assert len(groups) == len(model_obj.groups)
        for i, group in enumerate(groups):
            assert group == model_obj.groups[i]
    # 3. Serialize model back to JSON
    model_dict = model_obj.to_dict()
    model_json = json.dumps(model_dict)
    # 4. Verify the resulting JSON matches the original
    # Convert both JSONs to dictionaries for comparison
    deserialized_json = json.loads(model_json)
    # Compare key by key to handle any field name transformations
    for key in server_json:
        assert key in deserialized_json
        if isinstance(server_json[key], list):
            assert len(server_json[key]) == len(deserialized_json[key])
            for i, item in enumerate(server_json[key]):
                assert item == deserialized_json[key][i]
        else:
            assert server_json[key] == deserialized_json[key]
