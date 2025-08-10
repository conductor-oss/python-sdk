import json

import pytest

from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.client.http.models.tag_object import TagObject, TypeEnum
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("Tag"))


def test_tag_object_ser_deser(server_json):
    tag_object = TagObject(
        key=server_json.get("key"),
        type=server_json.get("type"),
        value=server_json.get("value"),
    )
    assert tag_object.key == server_json.get(
        "key"
    ), "Key field not correctly deserialized"
    assert tag_object.type == server_json.get(
        "type"
    ), "Type field not correctly deserialized"
    assert tag_object.value == server_json.get(
        "value"
    ), "Value field not correctly deserialized"
    if tag_object.type:
        assert tag_object.type in [
            TypeEnum.METADATA.value,
            TypeEnum.RATE_LIMIT.value,
        ], "Type field not correctly mapped to enum"
    result_dict = tag_object.to_dict()
    assert result_dict.get("key") == server_json.get(
        "key"
    ), "Key field not correctly serialized"
    assert result_dict.get("type") == server_json.get(
        "type"
    ), "Type field not correctly serialized"
    assert result_dict.get("value") == server_json.get(
        "value"
    ), "Value field not correctly serialized"
    for key in server_json:
        assert key in result_dict, f"Field {key} missing from serialized output"
        assert (
            result_dict[key] == server_json[key]
        ), f"Field {key} has different value in serialized output"
