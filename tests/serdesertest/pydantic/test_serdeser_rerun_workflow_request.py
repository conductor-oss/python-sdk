import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import RerunWorkflowRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("RerunWorkflowRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_rerun_workflow_request_deserialization(raw_server_json, server_json):
    rerun_workflow_request_adapter = RerunWorkflowRequestAdapter.from_json(raw_server_json)
    assert rerun_workflow_request_adapter.to_dict() == server_json


def test_rerun_workflow_request_serialization(raw_server_json, server_json):
    assert sorted(RerunWorkflowRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_rerun_workflow_request_invalid_data():
    with pytest.raises(ValidationError):
        RerunWorkflowRequestAdapter(correlation_id={"invalid_id"})
