import json

import pytest

from conductor.client.adapters.models.search_result_workflow_summary_adapter import (
    SearchResultWorkflowSummaryAdapter,
)
from conductor.client.adapters.models.workflow_summary_adapter import WorkflowSummaryAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("SearchResult"))


def test_serialization_deserialization(server_json):
    workflow_summary = WorkflowSummaryAdapter()
    model = SearchResultWorkflowSummaryAdapter(
        total_hits=server_json.get("totalHits"),
        results=[workflow_summary] if server_json.get("results") else None,
    )
    assert model.total_hits == server_json.get("totalHits")
    if model.results:
        assert len(model.results) == len(server_json.get("results", []))
    serialized_dict = model.to_dict()
    assert serialized_dict["total_hits"] == server_json.get("totalHits")
    if serialized_dict.get("results"):
        assert len(serialized_dict["results"]) == len(server_json.get("results", []))
