import json

import pytest

from conductor.client.http.models.permission import Permission
from conductor.client.http.models.role import Role
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("Role")
    return json.loads(server_json_str)


def test_role_serialization_deserialization(server_json):
    """Test that Role objects can be properly serialized and deserialized."""
    # 1. Test deserialization from server JSON to SDK model
    role_obj = Role(
        name=server_json.get("name"),
        permissions=[
            Permission(**perm) if isinstance(perm, dict) else perm
            for perm in server_json.get("permissions", [])
        ],
    )
    # 2. Verify all fields are properly populated
    assert server_json.get("name") == role_obj.name
    # Verify permissions list if present
    if "permissions" in server_json:
        assert role_obj.permissions is not None
        assert len(server_json["permissions"]) == len(role_obj.permissions)
        # Check first permission in list if available
        if server_json["permissions"] and role_obj.permissions:
            # This would need to be adapted based on the Permission class structure
            if hasattr(role_obj.permissions[0], "to_dict"):
                permission_dict = role_obj.permissions[0].to_dict()
                for key, value in server_json["permissions"][0].items():
                    # Convert JSON camelCase to Python snake_case if needed
                    snake_key = "".join(
                        ["_" + c.lower() if c.isupper() else c for c in key]
                    ).lstrip("_")
                    if snake_key in permission_dict:
                        assert value == permission_dict[snake_key]
    # 3. Test serialization back to JSON
    serialized_json = role_obj.to_dict()
    # 4. Verify the resulting JSON matches the original
    assert server_json.get("name") == serialized_json.get("name")
    # Compare permissions lists if present
    if "permissions" in server_json and "permissions" in serialized_json:
        assert len(server_json["permissions"]) == len(serialized_json["permissions"])
        # Deeper comparison would depend on Permission class structure
        if server_json["permissions"] and serialized_json["permissions"]:
            # This assumes Permission has a similar structure and serialization logic
            for i, (orig_perm, serial_perm) in enumerate(
                zip(server_json["permissions"], serialized_json["permissions"])
            ):
                if isinstance(orig_perm, dict) and isinstance(serial_perm, dict):
                    for key in orig_perm:
                        snake_key = "".join(
                            ["_" + c.lower() if c.isupper() else c for c in key]
                        ).lstrip("_")
                        camel_key = "".join(
                            [
                                word.capitalize() if i > 0 else word
                                for i, word in enumerate(snake_key.split("_"))
                            ]
                        )
                        assert (
                            key in serial_perm or camel_key in serial_perm
                        ), f"Key {key} or {camel_key} missing from serialized permission"
