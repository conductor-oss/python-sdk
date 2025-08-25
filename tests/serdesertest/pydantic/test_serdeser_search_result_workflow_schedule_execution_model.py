import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.search_result_workflow_schedule_execution_model_adapter import SearchResultWorkflowScheduleExecutionModelAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("SearchResult")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_action_deserialization(raw_server_json, server_json):
    action_adapter = SearchResultWorkflowScheduleExecutionModelAdapter.from_json(raw_server_json)
    assert action_adapter.to_dict() is not None


def test_start_workflow_request_invalid_data():
    with pytest.raises(ValidationError):
        SearchResultWorkflowScheduleExecutionModelAdapter(results="invalid_results")
