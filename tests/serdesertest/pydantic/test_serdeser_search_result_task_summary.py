import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.search_result_task_summary_adapter import SearchResultTaskSummaryAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("SearchResult")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_search_result_task_summary_deserialization(raw_server_json, server_json):
    search_result_task_summary_adapter = SearchResultTaskSummaryAdapter.from_json(raw_server_json)
    assert search_result_task_summary_adapter.to_dict() is not None


def test_search_result_task_summary_invalid_data():
    with pytest.raises(ValidationError):
        SearchResultTaskSummaryAdapter(results="invalid_results")
