
import json

import pytest
from pydantic import ValidationError

from conductor.asyncio_client.adapters.models.task_summary_adapter import TaskSummaryAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("TaskSummary")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_task_summary_deserialization(raw_server_json, server_json):
    task_summary_adapter = TaskSummaryAdapter.from_json(raw_server_json)
    assert task_summary_adapter.to_dict() == server_json


def test_task_summary_serialization(raw_server_json, server_json):
    assert sorted(TaskSummaryAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_task_summary_invalid_data():
    with pytest.raises(ValidationError):
        TaskSummaryAdapter(input={"invalid_input"})
