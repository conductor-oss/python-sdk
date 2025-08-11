
import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.workflow_summary_adapter import WorkflowSummaryAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("WorkflowSummary")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_workflow_summary_deserialization(raw_server_json, server_json):
    workflow_summary_adapter = WorkflowSummaryAdapter.from_json(raw_server_json)
    assert workflow_summary_adapter.to_dict() == server_json


def test_workflow_summary_serialization(raw_server_json, server_json):
    assert sorted(WorkflowSummaryAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_workflow_summary_invalid_data():
    with pytest.raises(ValidationError):
        WorkflowSummaryAdapter(workflow_id={"invalid_id"})
