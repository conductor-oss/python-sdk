import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.bulk_response_adapter import BulkResponseAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("BulkResponse")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_bulk_response_deserialization(raw_server_json, server_json):
    bulk_response = BulkResponseAdapter.from_json(raw_server_json)
    assert bulk_response.to_dict() == server_json


def test_bulk_response_serialization(raw_server_json, server_json):
    assert sorted(BulkResponseAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_bulk_response_validation_error():
    with pytest.raises(ValidationError):
        BulkResponseAdapter(message=1)
