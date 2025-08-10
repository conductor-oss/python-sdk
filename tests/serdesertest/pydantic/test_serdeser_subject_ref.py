import json

import pytest

from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter
from conductor.client.http.models.subject_ref import SubjectRef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("SubjectRef")
    return json.loads(server_json_str)


def test_subject_ref_serdes(server_json):
    # 1. Deserialize server JSON into SDK model object
    subject_ref = SubjectRef(type=server_json.get("type"), id=server_json.get("id"))
    # 2. Verify all fields are properly populated during deserialization
    assert subject_ref.type == server_json.get("type")
    assert subject_ref.id == server_json.get("id")
    # Check type is a valid enum value
    assert subject_ref.type in ["USER", "ROLE", "GROUP"]
    # 3. Serialize the SDK model back to JSON
    serialized_json = subject_ref.to_dict()
    # 4. Verify the resulting JSON matches the original
    assert serialized_json["type"] == server_json.get("type")
    assert serialized_json["id"] == server_json.get("id")
    # Convert both to strings to compare the complete structure
    original_json_str = json.dumps(server_json, sort_keys=True)
    serialized_json_str = json.dumps(serialized_json, sort_keys=True)
    assert serialized_json_str == original_json_str
