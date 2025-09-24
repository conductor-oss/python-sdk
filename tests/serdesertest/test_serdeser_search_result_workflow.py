import json

import pytest

from conductor.client.http.models.search_result_workflow import SearchResultWorkflowAdapter
from conductor.client.http.models.workflow import WorkflowAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("SearchResult"))


def test_search_result_workflow_serde(server_json):
    model = SearchResultWorkflowAdapter()
    if "totalHits" in server_json:
        model.total_hits = server_json["totalHits"]
    if server_json.get("results"):
        workflow_list = []
        for workflow_json in server_json["results"]:
            workflow = WorkflowAdapter()
            workflow_list.append(workflow)
        model.results = workflow_list
    assert model.total_hits is not None
    assert model.results is not None
    if model.results:
        assert isinstance(model.results[0], WorkflowAdapter)
    model_dict = model.to_dict()
    model_json = json.dumps(model_dict)
    deserialized_json = json.loads(model_json)
    assert server_json.get("totalHits") == deserialized_json.get("total_hits")
    assert len(server_json.get("results", [])) == len(
        deserialized_json.get("results", [])
    )
