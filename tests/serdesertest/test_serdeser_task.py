import json

import pytest

from conductor.client.http.models.task import TaskAdapter
from conductor.shared.http.enums import TaskResultStatus
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


def convert_to_snake_case(json_obj):
    if isinstance(json_obj, dict):
        python_obj = {}
        for key, value in json_obj.items():
            snake_key = None
            for python_key, json_key in TaskAdapter.attribute_map.items():
                if json_key == key:
                    snake_key = python_key
                    break
            if snake_key is None:
                snake_key = key
            if isinstance(value, dict) or isinstance(value, list):
                python_obj[snake_key] = convert_to_snake_case(value)
            else:
                python_obj[snake_key] = value
        return python_obj
    elif isinstance(json_obj, list):
        return [
            convert_to_snake_case(item) if isinstance(item, (dict, list)) else item
            for item in json_obj
        ]
    else:
        return json_obj


def validate_functional_equivalence(task1, task2):
    assert task1.task_id == task2.task_id
    assert task1.status == task2.status
    assert task1.task_type == task2.task_type
    assert task1.reference_task_name == task2.reference_task_name
    task1_dict = task1.to_dict()
    task2_dict = task2.to_dict()
    for field in ["taskId", "status", "taskType", "referenceTaskName"]:
        if field in task1_dict and field in task2_dict:
            assert task1_dict[field] == task2_dict[field]


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("Task"))


def test_task_serialization_deserialization(server_json):
    python_json = convert_to_snake_case(server_json)
    task = TaskAdapter(**python_json)
    assert isinstance(task, TaskAdapter)
    if "task_id" in python_json:
        assert task.task_id == python_json["task_id"]
    if "status" in python_json:
        assert task.status == python_json["status"]
    serialized_json = task.to_dict()
    task2 = TaskAdapter(**convert_to_snake_case(serialized_json))
    assert isinstance(task2, TaskAdapter)
    task_result = task.to_task_result(TaskResultStatus.COMPLETED)
    assert task_result.task_id == task.task_id
    assert task_result.workflow_instance_id == task.workflow_instance_id
    assert task_result.worker_id == task.worker_id
    assert task_result.status == TaskResultStatus.COMPLETED
    validate_functional_equivalence(task, task2)
