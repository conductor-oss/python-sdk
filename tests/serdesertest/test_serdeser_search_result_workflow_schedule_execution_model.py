import json

import pytest

from conductor.client.adapters.models.search_result_workflow_schedule_execution_model_adapter import (
    SearchResultWorkflowScheduleExecutionModelAdapter,
)
from conductor.client.adapters.models.workflow_schedule_execution_model_adapter import (
    WorkflowScheduleExecutionModelAdapter,
)
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("SearchResult"))


def test_search_result_workflow_schedule_execution_model_serde(server_json):
    work_flow_schedule_execution_model = WorkflowScheduleExecutionModelAdapter()
    model = SearchResultWorkflowScheduleExecutionModelAdapter(
        total_hits=server_json["totalHits"],
        results=(
            [work_flow_schedule_execution_model] if server_json.get("results") else None
        ),
    )
    assert model.total_hits == server_json["totalHits"]
    assert len(model.results) == len(server_json["results"])
    if model.results and len(model.results) > 0:
        sample_result = model.results[0]
        assert isinstance(sample_result, WorkflowScheduleExecutionModelAdapter)
    model_dict = model.to_dict()
    assert model_dict["total_hits"] == server_json["totalHits"]
    assert len(model_dict["results"]) == len(server_json["results"])
    assert "total_hits" in model_dict
    assert "results" in model_dict
