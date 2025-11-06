
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.workflow_status_adapter import WorkflowStatusAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("WorkflowStatus")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_workflow_status_deserialization(raw_server_json, server_json):
    workflow_status_adapter = WorkflowStatusAdapter.from_json(raw_server_json)
    assert workflow_status_adapter.to_dict() == server_json


def test_workflow_status_serialization(raw_server_json, server_json):
    assert sorted(WorkflowStatusAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_workflow_status_invalid_data():
    with pytest.raises(ValidationError):
        WorkflowStatusAdapter(workflow_id={"invalid_id"})
