import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import UpsertUserRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("UpsertUserRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_upsert_user_request_deserialization(raw_server_json, server_json):
    upsert_user_request_adapter = UpsertUserRequestAdapter.from_json(raw_server_json)
    assert upsert_user_request_adapter.to_dict() == server_json


def test_upsert_user_request_serialization(raw_server_json, server_json):
    assert sorted(UpsertUserRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_upsert_user_request_invalid_data():
    with pytest.raises(ValidationError):
        UpsertUserRequestAdapter(user_id={"invalid_id"})
