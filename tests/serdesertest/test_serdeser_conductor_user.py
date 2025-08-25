import json

import pytest

from conductor.client.adapters.models.conductor_user_adapter import ConductorUserAdapter
from conductor.client.adapters.models.group_adapter import GroupAdapter
from conductor.client.adapters.models.role_adapter import RoleAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("ConductorUser"))


def test_conductor_user_serde(server_json):  #  noqa: PLR0915
    conductor_user = ConductorUserAdapter()
    conductor_user_dict = server_json
    if "id" in conductor_user_dict:
        conductor_user.id = conductor_user_dict["id"]
    if "name" in conductor_user_dict:
        conductor_user.name = conductor_user_dict["name"]
    if "roles" in conductor_user_dict:
        roles_list = []
        for _ in conductor_user_dict["roles"]:
            role = RoleAdapter()
            roles_list.append(role)
        conductor_user.roles = roles_list
    if "groups" in conductor_user_dict:
        groups_list = []
        for group_data in conductor_user_dict["groups"]:
            group = GroupAdapter()
            groups_list.append(group)
        conductor_user.groups = groups_list
    if "uuid" in conductor_user_dict:
        conductor_user.uuid = conductor_user_dict["uuid"]
    if "applicationUser" in conductor_user_dict:
        conductor_user.application_user = conductor_user_dict["applicationUser"]
    if "encryptedId" in conductor_user_dict:
        conductor_user.encrypted_id = conductor_user_dict["encryptedId"]
    if "encryptedIdDisplayValue" in conductor_user_dict:
        conductor_user.encrypted_id_display_value = conductor_user_dict[
            "encryptedIdDisplayValue"
        ]
    expected_id = server_json.get("id", None)
    assert conductor_user.id == expected_id
    expected_name = server_json.get("name", None)
    assert conductor_user.name == expected_name
    if "roles" in server_json:
        assert len(conductor_user.roles) == len(server_json["roles"])
    if "groups" in server_json:
        assert len(conductor_user.groups) == len(server_json["groups"])
    expected_uuid = server_json.get("uuid", None)
    assert conductor_user.uuid == expected_uuid
    expected_app_user = server_json.get("applicationUser", None)
    assert conductor_user.application_user == expected_app_user
    expected_encrypted_id = server_json.get("encryptedId", None)
    assert conductor_user.encrypted_id == expected_encrypted_id
    expected_encrypted_id_display = server_json.get("encryptedIdDisplayValue", None)
    assert conductor_user.encrypted_id_display_value == expected_encrypted_id_display
    serialized_json = conductor_user.to_dict()
    if "applicationUser" in server_json:
        assert serialized_json["application_user"] == server_json["applicationUser"]
    if "encryptedId" in server_json:
        assert serialized_json["encrypted_id"] == server_json["encryptedId"]
    if "encryptedIdDisplayValue" in server_json:
        assert (
            serialized_json["encrypted_id_display_value"]
            == server_json["encryptedIdDisplayValue"]
        )
    for field in ["id", "name", "uuid"]:
        if field in server_json:
            assert serialized_json[field] == server_json[field]
    if "roles" in server_json:
        assert len(serialized_json["roles"]) == len(server_json["roles"])
    if "groups" in server_json:
        assert len(serialized_json["groups"]) == len(server_json["groups"])
