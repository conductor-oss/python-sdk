import json

import pytest

from conductor.asyncio_client.adapters.models.state_change_event_adapter import StateChangeEventAdapter
from conductor.client.http.models.state_change_event import (
    StateChangeConfig,
    StateChangeEvent,
    StateChangeEventType,
)
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def state_change_event_json():
    return json.loads(JsonTemplateResolver.get_json_string("StateChangeEvent"))


def test_state_change_event_serde(state_change_event_json):
    event = StateChangeEvent(
        type=state_change_event_json["type"], payload=state_change_event_json["payload"]
    )
    assert event.type == state_change_event_json["type"]
    assert event.payload == state_change_event_json["payload"]
    serialized_json = event.to_dict()
    assert serialized_json["type"] == state_change_event_json["type"]
    assert serialized_json["payload"] == state_change_event_json["payload"]


def test_state_change_config_multiple_event_types():
    event_types = [StateChangeEventType.onStart, StateChangeEventType.onSuccess]
    events = [StateChangeEvent(type="sample_type", payload={"key": "value"})]
    config = StateChangeConfig(event_type=event_types, events=events)
    assert config.type == "onStart,onSuccess"
    serialized_json = config.to_dict()
    assert serialized_json["type"] == "onStart,onSuccess"
    assert len(serialized_json["events"]) == 1
    assert serialized_json["events"][0]["type"] == "sample_type"
    assert serialized_json["events"][0]["payload"] == {"key": "value"}
