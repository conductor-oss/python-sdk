
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.upsert_group_request_adapter import UpsertGroupRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("UpsertGroupRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_upsert_group_request_deserialization(raw_server_json, server_json):
    upsert_group_request_adapter = UpsertGroupRequestAdapter.from_json(raw_server_json)
    assert upsert_group_request_adapter.to_dict() == server_json


def test_upsert_group_request_serialization(raw_server_json, server_json):
    assert sorted(UpsertGroupRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_upsert_group_request_invalid_data():
    with pytest.raises(ValidationError):
        UpsertGroupRequestAdapter(group_id={"invalid_id"})
