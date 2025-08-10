import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.skip_task_request_adapter import SkipTaskRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("SkipTaskRequest")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_skip_task_request_deserialization(raw_server_json, server_json):
    skip_task_request_adapter = SkipTaskRequestAdapter.from_json(raw_server_json)
    assert skip_task_request_adapter.to_dict() == server_json


def test_skip_task_request_serialization(raw_server_json, server_json):
    assert sorted(SkipTaskRequestAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_skip_task_request_invalid_data():
    with pytest.raises(ValidationError):
        SkipTaskRequestAdapter(task_input="invalid_input")
