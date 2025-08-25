import json

import pytest

from conductor.client.adapters.models.search_result_task_adapter import SearchResultTaskAdapter
from conductor.client.adapters.models.task_adapter import TaskAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("SearchResult"))


def test_search_result_task_ser_des(server_json):
    task = TaskAdapter()
    search_result = SearchResultTaskAdapter(
        total_hits=server_json.get("totalHits"),
        results=[task] if server_json.get("results") else None,
    )
    assert search_result.total_hits == server_json.get("totalHits")
    if server_json.get("results"):
        assert search_result.results is not None
        assert len(search_result.results) == len(server_json.get("results"))
    else:
        if "results" in server_json and server_json["results"] is None:
            assert search_result.results is None
    serialized_dict = search_result.to_dict()
    if "totalHits" in server_json:
        assert serialized_dict.get("total_hits") == server_json.get("totalHits")
    if "results" in server_json and server_json["results"] is not None:
        assert serialized_dict.get("results") is not None
        assert len(serialized_dict.get("results")) == len(server_json.get("results"))
    elif "results" in server_json and server_json["results"] is None:
        assert serialized_dict.get("results") is None
