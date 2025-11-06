
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.update_workflow_variables_adapter import UpdateWorkflowVariablesAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("EventHandler.UpdateWorkflowVariables")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_update_workflow_variables_deserialization(raw_server_json, server_json):
    update_workflow_variables_adapter = UpdateWorkflowVariablesAdapter.from_json(raw_server_json)
    assert update_workflow_variables_adapter.to_dict() == server_json


def test_update_workflow_variables_serialization(raw_server_json, server_json):
    assert sorted(UpdateWorkflowVariablesAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_update_workflow_variables_invalid_data():
    with pytest.raises(ValidationError):
        UpdateWorkflowVariablesAdapter(workflow_id={"invalid_id"})
