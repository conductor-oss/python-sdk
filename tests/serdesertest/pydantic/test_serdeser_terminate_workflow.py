
import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.terminate_workflow_adapter import TerminateWorkflowAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("EventHandler.TerminateWorkflow")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_terminate_workflow_deserialization(raw_server_json, server_json):
    terminate_workflow_adapter = TerminateWorkflowAdapter.from_json(raw_server_json)
    assert terminate_workflow_adapter.to_dict() == server_json


def test_terminate_workflow_serialization(raw_server_json, server_json):
    assert sorted(TerminateWorkflowAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_terminate_workflow_invalid_data():
    with pytest.raises(ValidationError):
        TerminateWorkflowAdapter(workflow_id={"invalid_id"})
