import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.correlation_ids_search_request_adapter import CorrelationIdsSearchRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("CorrelationIdsSearchRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_correlation_ids_search_request_deserialization(raw_server_json, server_json):
    correlation_ids_search_request_adapter = CorrelationIdsSearchRequestAdapter.from_json(raw_server_json)
    assert correlation_ids_search_request_adapter.to_dict() == server_json


def test_correlation_ids_search_request_serialization(raw_server_json, server_json):
    assert sorted(CorrelationIdsSearchRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_correlation_ids_search_request_validation_error():
    with pytest.raises(ValidationError):
        CorrelationIdsSearchRequestAdapter(correlation_ids="invalid ids")
