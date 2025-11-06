import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.authorization_request_adapter import AuthorizationRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("AuthorizationRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_authorization_request_deserialization(raw_server_json, server_json):
    authorization_request = AuthorizationRequestAdapter.from_json(raw_server_json)
    assert authorization_request.to_dict() == server_json


def test_authorization_request_serialization(raw_server_json, server_json):
    assert sorted(AuthorizationRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_authorization_request_invalid_access():
    with pytest.raises(ValidationError):
        AuthorizationRequestAdapter(access="INVALID_PERMISSION")
