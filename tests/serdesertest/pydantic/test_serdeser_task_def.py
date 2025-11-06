
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.task_def_adapter import TaskDefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("TaskDef")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_task_def_deserialization(raw_server_json, server_json):
    task_def_adapter = TaskDefAdapter.from_json(raw_server_json)
    assert task_def_adapter.to_dict() == server_json


def test_task_def_serialization(raw_server_json, server_json):
    assert sorted(TaskDefAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_task_def_invalid_data():
    with pytest.raises(ValidationError):
        TaskDefAdapter(name={"invalid_name"})
