import json

import pytest

from conductor.client.http.models.authorization_request import AuthorizationRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("AuthorizationRequest"))


def test_serialization_deserialization(server_json):
    auth_request = AuthorizationRequest(
        subject=server_json.get("subject"),
        target=server_json.get("target"),
        access=server_json.get("access"),
    )
    assert auth_request is not None, "Deserialized object should not be null"
    assert auth_request.access is not None, "Access list should not be null"
    assert all(
        access in ["CREATE", "READ", "UPDATE", "DELETE", "EXECUTE"]
        for access in auth_request.access
    )
    assert auth_request.subject is not None, "Subject should not be null"
    assert auth_request.target is not None, "Target should not be null"
    result_dict = auth_request.to_dict()
    assert set(server_json.keys()) == set(
        result_dict.keys()
    ), "Serialized JSON should have the same keys as the original"
    original_json_normalized = json.dumps(server_json, sort_keys=True)
    result_json_normalized = json.dumps(result_dict, sort_keys=True)
    assert (
        original_json_normalized == result_json_normalized
    ), "Serialized JSON should match the original SERVER_JSON"
