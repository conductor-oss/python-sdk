import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.action_adapter import ActionAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("EventHandler.Action")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_action_deserialization(raw_server_json, server_json):
    action_adapter = ActionAdapter.from_json(raw_server_json)
    assert action_adapter.to_dict() == server_json


def test_action_serialization(raw_server_json, server_json):
    assert sorted(ActionAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_start_workflow_request_invalid_data():
    with pytest.raises(ValidationError):
        ActionAdapter(complete_task="invalid_task")
