import json

import pytest

from conductor.client.http.models.group import Group
from conductor.client.http.models.role import Role
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("Group"))


def test_group_serde(server_json):
    group = Group(
        id=server_json.get("id"),
        description=server_json.get("description"),
        roles=[Role(**role) for role in server_json.get("roles", [])],
        default_access=server_json.get("defaultAccess"),
    )
    assert server_json.get("id") == group.id
    assert server_json.get("description") == group.description
    if server_json.get("roles"):
        assert group.roles is not None
        assert len(server_json.get("roles")) == len(group.roles)
        for i, role in enumerate(group.roles):
            assert isinstance(role, Role)
            assert server_json.get("roles")[i].get("name") == role.name
    if server_json.get("defaultAccess"):
        assert group.default_access is not None
        for key in server_json.get("defaultAccess").keys():
            assert key in group.default_access
            assert server_json.get("defaultAccess")[key] == group.default_access[key]
    result_dict = group.to_dict()
    camel_case_dict = {}
    for key, value in result_dict.items():
        json_key = Group.attribute_map.get(key, key)
        camel_case_dict[json_key] = value
    for key in server_json.keys():
        if key == "roles":
            if server_json.get("roles"):
                assert len(server_json.get("roles")) == len(
                    camel_case_dict.get("roles", [])
                )
                for i, role_dict in enumerate(camel_case_dict.get("roles", [])):
                    for role_key in server_json.get("roles")[i].keys():
                        assert server_json.get("roles")[i].get(
                            role_key
                        ) == role_dict.get(
                            Role.attribute_map.get(
                                role_key.replace("camelCase", "snake_case"), role_key
                            )
                        )
        elif key == "defaultAccess":
            if server_json.get("defaultAccess"):
                for map_key, map_value in server_json.get("defaultAccess").items():
                    assert map_key in camel_case_dict.get("defaultAccess", {})
                    assert map_value == camel_case_dict.get("defaultAccess", {}).get(
                        map_key
                    )
        else:
            assert server_json.get(key) == camel_case_dict.get(key)
