import json

import pytest

from conductor.client.adapters.models.rerun_workflow_request_adapter import RerunWorkflowRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def request_json():
    return json.loads(JsonTemplateResolver.get_json_string("RerunWorkflowRequest"))


@pytest.fixture
def request_obj(request_json):
    obj = RerunWorkflowRequestAdapter()
    obj.re_run_from_workflow_id = request_json["reRunFromWorkflowId"]
    obj.workflow_input = request_json["workflowInput"]
    obj.re_run_from_task_id = request_json["reRunFromTaskId"]
    obj.task_input = request_json["taskInput"]
    obj.correlation_id = request_json["correlationId"]
    return obj


def test_serialization_deserialization_cycle(request_json, request_obj):
    result_dict = request_obj.to_dict()
    transformed_dict = {
        "reRunFromWorkflowId": result_dict["re_run_from_workflow_id"],
        "workflowInput": result_dict["workflow_input"],
        "reRunFromTaskId": result_dict["re_run_from_task_id"],
        "taskInput": result_dict["task_input"],
        "correlationId": result_dict["correlation_id"],
    }
    # 1. Test deserialization: Assert that fields are correctly populated
    assert request_obj.re_run_from_workflow_id == "sample_reRunFromWorkflowId"
    assert request_obj.re_run_from_task_id == "sample_reRunFromTaskId"
    assert request_obj.correlation_id == "sample_correlationId"
    assert isinstance(request_obj.workflow_input, dict)
    assert request_obj.workflow_input["sample_key"] == "sample_value"
    assert isinstance(request_obj.task_input, dict)
    assert request_obj.task_input["sample_key"] == "sample_value"
    # 2. Test serialization: Compare individual fields
    assert (
        transformed_dict["reRunFromWorkflowId"] == request_json["reRunFromWorkflowId"]
    )
    assert transformed_dict["reRunFromTaskId"] == request_json["reRunFromTaskId"]
    assert transformed_dict["correlationId"] == request_json["correlationId"]
    assert transformed_dict["workflowInput"] == request_json["workflowInput"]
    assert transformed_dict["taskInput"] == request_json["taskInput"]
    # 3. Ensure no fields are missing
    assert set(transformed_dict.keys()) == set(request_json.keys())
    # 4. Test full cycle with deep equality
    assert transformed_dict == request_json
