import json

from conductor.client.http.models.workflow_task import WorkflowTask
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


def to_camel_case(snake_str):
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def workflow_task_to_json_dict(task):
    result = {}
    for snake_attr in task.swagger_types:
        value = getattr(task, snake_attr)
        if value is not None:
            if snake_attr in task.attribute_map:
                json_attr = task.attribute_map[snake_attr]
            else:
                json_attr = to_camel_case(snake_attr)
            if isinstance(value, list):
                result[json_attr] = [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in value
                ]
            elif hasattr(value, "to_dict"):
                result[json_attr] = value.to_dict()
            elif isinstance(value, dict):
                result[json_attr] = {
                    k: v.to_dict() if hasattr(v, "to_dict") else v
                    for k, v in value.items()
                }
            else:
                result[json_attr] = value
    return result


def test_workflow_task_serde():
    server_json_str = JsonTemplateResolver.get_json_string("WorkflowTask")
    server_json = json.loads(server_json_str)
    mapped_kwargs = {}
    for json_key, value in server_json.items():
        for py_attr, mapped_json in WorkflowTask.attribute_map.items():
            if mapped_json == json_key:
                mapped_kwargs[py_attr] = value
                break
    workflow_task = WorkflowTask(**mapped_kwargs)
    assert server_json.get("name") == workflow_task.name
    assert server_json.get("taskReferenceName") == workflow_task.task_reference_name
    if "joinOn" in server_json:
        assert server_json.get("joinOn") == workflow_task.join_on
    result_dict = workflow_task.to_dict()
    converted_dict = {}
    for key, value in result_dict.items():
        if value is not None:
            camel_key = key
            for py_attr, json_attr in WorkflowTask.attribute_map.items():
                if py_attr == key:
                    camel_key = json_attr
                    break
            converted_dict[camel_key] = value
    fixed_json_dict = workflow_task_to_json_dict(workflow_task)
    assert "name" in fixed_json_dict
    assert "taskReferenceName" in fixed_json_dict
    if workflow_task.join_on is not None:
        assert "joinOn" in fixed_json_dict
        assert workflow_task.join_on == fixed_json_dict["joinOn"]
    test_task = WorkflowTask(name="Test Task", task_reference_name="testRef")
    test_task.join_on = ["task1", "task2"]
    fixed_test_dict = workflow_task_to_json_dict(test_task)
    assert "joinOn" in fixed_test_dict
    assert test_task.join_on == fixed_test_dict["joinOn"]
