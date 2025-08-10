import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.event_handler_adapter import EventHandlerAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("EventHandler")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_event_handler_deserialization(raw_server_json, server_json):
    event_handler_adapter = EventHandlerAdapter.from_json(raw_server_json)
    assert event_handler_adapter.to_dict() == server_json


def test_event_handler_serialization(raw_server_json, server_json):
    assert sorted(EventHandlerAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_event_handler_validation_error():
    with pytest.raises(ValidationError):
        EventHandlerAdapter(name=1)
