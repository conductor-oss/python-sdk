
import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.task_details_adapter import TaskDetailsAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("EventHandler.TaskDetails")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_task_details_deserialization(raw_server_json, server_json):
    task_details_adapter = TaskDetailsAdapter.from_json(raw_server_json)
    assert task_details_adapter.to_dict() == server_json


def test_task_details_serialization(raw_server_json, server_json):
    assert sorted(TaskDetailsAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_task_details_invalid_data():
    with pytest.raises(ValidationError):
        TaskDetailsAdapter(output={"invalid_output"})
