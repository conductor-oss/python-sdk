import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.task_result_adapter import TaskResultAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("TaskResult")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_task_result_deserialization(raw_server_json, server_json):
    task_result_adapter = TaskResultAdapter.from_json(raw_server_json)
    assert task_result_adapter.to_dict() == server_json


def test_task_result_serialization(raw_server_json, server_json):
    assert sorted(TaskResultAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_task_result_invalid_data():
    with pytest.raises(ValidationError):
        TaskResultAdapter(log={"invalid_log"})
