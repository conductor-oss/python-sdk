import json

import pytest

from conductor.client.http.models.target_ref import TargetRef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("TargetRef"))


def test_target_ref_serdes(server_json):
    target_ref = TargetRef(type=server_json.get("type"), id=server_json.get("id"))
    assert target_ref.type is not None
    assert target_ref.id is not None
    valid_types = [
        "WORKFLOW_DEF",
        "TASK_DEF",
        "APPLICATION",
        "USER",
        "SECRET_NAME",
        "TAG",
        "DOMAIN",
    ]
    assert target_ref.type in valid_types
    sdk_json = target_ref.to_dict()
    assert server_json.get("type") == sdk_json.get("type")
    assert server_json.get("id") == sdk_json.get("id")
    serialized_json = json.dumps(sdk_json)
    deserialized_json = json.loads(serialized_json)
    round_trip_obj = TargetRef(
        type=deserialized_json.get("type"), id=deserialized_json.get("id")
    )
    assert target_ref.type == round_trip_obj.type
    assert target_ref.id == round_trip_obj.id
    assert target_ref == round_trip_obj
