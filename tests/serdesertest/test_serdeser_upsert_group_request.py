import json

import pytest

from conductor.client.http.models.upsert_group_request import UpsertGroupRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("UpsertGroupRequest")
    return json.loads(server_json_str)


def test_serde_upsert_group_request(server_json):
    # 1. Deserialize JSON into model object
    model_obj = UpsertGroupRequestAdapter(
        description=server_json.get("description"),
        roles=server_json.get("roles"),
        default_access=server_json.get("defaultAccess"),
    )
    # 2. Verify all fields are properly populated
    assert model_obj.description == server_json.get("description")
    # Check roles list is populated correctly
    assert model_obj.roles is not None
    assert len(model_obj.roles) == len(server_json.get("roles", []))
    for role in model_obj.roles:
        assert role in [
            "ADMIN",
            "USER",
            "WORKER",
            "METADATA_MANAGER",
            "WORKFLOW_MANAGER",
        ]
    # Check default_access map is populated correctly
    assert model_obj.default_access is not None
    assert len(model_obj.default_access) == len(server_json.get("defaultAccess", {}))
    # Verify all keys in default_access are valid
    for key in model_obj.default_access:
        assert key in ["WORKFLOW_DEF", "TASK_DEF"]
    # 3. Serialize the model back to dict/JSON
    model_dict = model_obj.to_dict()
    # 4. Verify the serialized JSON matches the original
    # Check that snake_case in Python is properly converted to camelCase in JSON
    assert model_dict["default_access"] == server_json.get("defaultAccess")
    assert model_dict["description"] == server_json.get("description")
    assert model_dict["roles"] == server_json.get("roles")
    # Additional validation for complex nested structures
    if "defaultAccess" in server_json:
        for target_type, access_list in server_json["defaultAccess"].items():
            assert target_type in model_dict["default_access"]
            assert access_list == model_dict["default_access"][target_type]
