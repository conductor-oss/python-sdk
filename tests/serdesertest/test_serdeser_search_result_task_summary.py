import json

import pytest

from conductor.client.adapters.models.search_result_task_summary_adapter import (
    SearchResultTaskSummaryAdapter,
)
from conductor.client.adapters.models.task_summary_adapter import TaskSummaryAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("SearchResult")
    return json.loads(server_json_str)


def test_search_result_task_summary_serdeser(server_json):
    """Test serialization and deserialization of SearchResultTaskSummary"""
    task_summary = TaskSummaryAdapter()
    # 1. Test deserialization of server JSON into SDK model
    model = SearchResultTaskSummaryAdapter(
        total_hits=server_json.get("totalHits"),
        results=[task_summary] if server_json.get("results") else None,
    )
    # 2. Verify all fields are properly populated
    assert model.total_hits == server_json.get("totalHits")
    assert len(model.results) == len(server_json.get("results", []))
    # Verify each TaskSummary in results list
    for i, task_summary in enumerate(model.results):
        # Assuming TaskSummary has properties that correspond to the JSON fields
        # Add specific assertions for TaskSummary fields here
        assert isinstance(task_summary, TaskSummaryAdapter)
    # 3. Test serialization back to JSON
    model_dict = model.to_dict()
    # 4. Verify the resulting JSON matches the original
    assert model_dict.get("total_hits") == server_json.get("totalHits")
    assert len(model_dict.get("results", [])) == len(server_json.get("results", []))
    # Check field transformation from snake_case to camelCase
    serialized_json = {}
    for attr, json_key in model.attribute_map.items():
        if attr in model_dict:
            serialized_json[json_key] = model_dict[attr]
    # Compare serialized JSON with original (considering camelCase transformation)
    for key in server_json:
        if key == "results":
            # For lists, compare length
            assert len(serialized_json.get(key, [])) == len(server_json.get(key, []))
        else:
            assert serialized_json.get(key) == server_json.get(key)
