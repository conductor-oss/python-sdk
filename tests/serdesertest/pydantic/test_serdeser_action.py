import json
import re

import pytest

from conductor.asyncio_client.adapters.models.action_adapter import ActionAdapter
from conductor.client.http.models.action import Action
from conductor.client.http.models.start_workflow import StartWorkflow
from conductor.client.http.models.task_details import TaskDetails
from conductor.client.http.models.terminate_workflow import TerminateWorkflow
from conductor.client.http.models.update_workflow_variables import (
    UpdateWorkflowVariables,
)
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


def camel_to_snake(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def create_model_object(model_class, json_data):
    if not json_data:
        return None
    obj = model_class()
    for key, value in json_data.items():
        snake_key = camel_to_snake(key)
        if hasattr(obj, snake_key):
            setattr(obj, snake_key, value)
    return obj


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("EventHandler.Action"))


def test_action_serdes(server_json):
    action_obj = Action(
        action=server_json.get("action"),
        start_workflow=create_model_object(
            StartWorkflow, server_json.get("start_workflow")
        ),
        complete_task=create_model_object(
            TaskDetails, server_json.get("complete_task")
        ),
        fail_task=create_model_object(TaskDetails, server_json.get("fail_task")),
        expand_inline_json=server_json.get("expandInlineJSON"),
        terminate_workflow=create_model_object(
            TerminateWorkflow, server_json.get("terminate_workflow")
        ),
        update_workflow_variables=create_model_object(
            UpdateWorkflowVariables, server_json.get("update_workflow_variables")
        ),
    )
    assert server_json.get("action") == action_obj.action
    if "start_workflow" in server_json:
        assert action_obj.start_workflow is not None
    if "complete_task" in server_json:
        assert action_obj.complete_task is not None
    if "fail_task" in server_json:
        assert action_obj.fail_task is not None
    if "expandInlineJSON" in server_json:
        assert server_json.get("expandInlineJSON") == action_obj.expand_inline_json
    if "terminate_workflow" in server_json:
        assert action_obj.terminate_workflow is not None
    if "update_workflow_variables" in server_json:
        assert action_obj.update_workflow_variables is not None
    allowed_values = [
        "start_workflow",
        "complete_task",
        "fail_task",
        "terminate_workflow",
        "update_workflow_variables",
    ]
    assert action_obj.action in allowed_values
    result_json = action_obj.to_dict()
    for key in server_json:
        if key == "expandInlineJSON":
            assert server_json[key] == result_json["expand_inline_json"]
        elif key in [
            "terminate_workflow",
            "start_workflow",
            "complete_task",
            "fail_task",
            "update_workflow_variables",
        ]:
            if server_json[key] is not None:
                assert result_json[key] is not None
                if key == "terminate_workflow" and key in result_json:
                    term_json = server_json[key]
                    result_term = result_json[key]
                    if "workflowId" in term_json and "workflowId" in result_term:
                        assert term_json["workflowId"] == result_term["workflowId"]
                    if (
                        "terminationReason" in term_json
                        and "terminationReason" in result_term
                    ):
                        assert (
                            term_json["terminationReason"]
                            == result_term["terminationReason"]
                        )
                if key == "update_workflow_variables" and key in result_json:
                    update_json = server_json[key]
                    result_update = result_json[key]
                    if "workflowId" in update_json and "workflowId" in result_update:
                        assert update_json["workflowId"] == result_update["workflowId"]
                    if "variables" in update_json and "variables" in result_update:
                        assert update_json["variables"] == result_update["variables"]
                    if "appendArray" in update_json and "appendArray" in result_update:
                        assert (
                            update_json["appendArray"] == result_update["appendArray"]
                        )
        elif key in result_json:
            assert server_json[key] == result_json[key]
