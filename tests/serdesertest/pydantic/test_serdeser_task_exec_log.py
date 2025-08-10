import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.task_exec_log_adapter import TaskExecLogAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("TaskExecLog")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_task_exec_log_deserialization(raw_server_json, server_json):
    task_exec_log_adapter = TaskExecLogAdapter.from_json(raw_server_json)
    assert task_exec_log_adapter.to_dict() == server_json


def test_task_exec_log_serialization(raw_server_json, server_json):
    assert sorted(TaskExecLogAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_task_exec_log_invalid_data():
    with pytest.raises(ValidationError):
        TaskExecLogAdapter(log={"invalid_log"})
