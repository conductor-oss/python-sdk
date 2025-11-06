
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.workflow_state_update_adapter import WorkflowStateUpdateAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("WorkflowStateUpdate")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_workflow_state_update_deserialization(raw_server_json, server_json):
    workflow_state_update_adapter = WorkflowStateUpdateAdapter.from_json(raw_server_json)
    assert workflow_state_update_adapter.to_dict() == server_json


def test_workflow_state_update_serialization(raw_server_json, server_json):
    assert sorted(WorkflowStateUpdateAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_workflow_state_update_invalid_data():
    with pytest.raises(ValidationError):
        WorkflowStateUpdateAdapter(task_result={"invalid_result"})
