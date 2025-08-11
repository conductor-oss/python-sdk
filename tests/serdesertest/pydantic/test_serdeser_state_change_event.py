import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.state_change_event_adapter import StateChangeEventAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("StateChangeEvent")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_state_change_event_deserialization(raw_server_json, server_json):
    state_change_event_adapter = StateChangeEventAdapter.from_json(raw_server_json)
    assert state_change_event_adapter.to_dict() == server_json


def test_state_change_event_serialization(raw_server_json, server_json):
    assert sorted(StateChangeEventAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_state_change_event_invalid_data():
    with pytest.raises(ValidationError):
        StateChangeEventAdapter(payload="invalid_type")
