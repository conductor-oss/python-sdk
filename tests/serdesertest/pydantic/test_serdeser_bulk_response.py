import json

import pytest

from conductor.asyncio_client.adapters.models.bulk_response_adapter import BulkResponseAdapter
from conductor.client.http.models import BulkResponse
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json_dict():
    return json.loads(JsonTemplateResolver.get_json_string("BulkResponse"))


def test_bulk_response_serialization_deserialization(server_json_dict):
    bulk_response = BulkResponse(
        bulk_error_results=server_json_dict["bulkErrorResults"],
        bulk_successful_results=server_json_dict["bulkSuccessfulResults"],
        message=server_json_dict["message"],
    )
    assert isinstance(bulk_response, BulkResponse)
    assert isinstance(bulk_response.bulk_error_results, dict)
    assert isinstance(bulk_response.bulk_successful_results, list)
    for key, value in bulk_response.bulk_error_results.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
    for item in bulk_response.bulk_successful_results:
        if isinstance(item, dict) and "value" in item:
            assert isinstance(item["value"], str)
        elif isinstance(item, str):
            pass
        else:
            pytest.fail(
                f"Unexpected item type in bulk_successful_results: {type(item)}"
            )
    assert bulk_response.bulk_error_results == server_json_dict["bulkErrorResults"]
    assert (
        bulk_response.bulk_successful_results
        == server_json_dict["bulkSuccessfulResults"]
    )
    result_dict = bulk_response.to_dict()
    assert "bulk_error_results" in result_dict
    assert "bulk_successful_results" in result_dict
    assert result_dict["bulk_error_results"] == server_json_dict["bulkErrorResults"]
    assert (
        result_dict["bulk_successful_results"]
        == server_json_dict["bulkSuccessfulResults"]
    )
    json_compatible_dict = {
        "bulkErrorResults": result_dict["bulk_error_results"],
        "bulkSuccessfulResults": result_dict["bulk_successful_results"],
        "message": result_dict["message"],
    }
    normalized_original = json.loads(json.dumps(server_json_dict, sort_keys=True))
    normalized_result = json.loads(json.dumps(json_compatible_dict, sort_keys=True))
    assert normalized_original == normalized_result
    bulk_response_2 = BulkResponse(
        bulk_error_results=result_dict["bulk_error_results"],
        bulk_successful_results=result_dict["bulk_successful_results"],
        message=server_json_dict["message"],
    )
    assert bulk_response.bulk_error_results == bulk_response_2.bulk_error_results
    assert (
        bulk_response.bulk_successful_results == bulk_response_2.bulk_successful_results
    )
    bulk_response_errors_only = BulkResponse(bulk_error_results={"id1": "error1"})
    assert bulk_response_errors_only.bulk_error_results == {"id1": "error1"}
    assert bulk_response_errors_only.bulk_successful_results == []
    sample_successful_result = [{"value": "success1"}]
    bulk_response_success_only = BulkResponse(
        bulk_successful_results=sample_successful_result
    )
    assert bulk_response_success_only.bulk_error_results == {}
    assert (
        bulk_response_success_only.bulk_successful_results == sample_successful_result
    )
    bulk_response_empty = BulkResponse(
        bulk_error_results={}, bulk_successful_results=[]
    )
    assert bulk_response_empty.bulk_error_results == {}
    assert bulk_response_empty.bulk_successful_results == []
