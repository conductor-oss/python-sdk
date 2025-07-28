import json

import pytest

from conductor.client.http.models.sub_workflow_params import SubWorkflowParams
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("SubWorkflowParams"))


def test_serialization_deserialization(server_json):
    model_obj = SubWorkflowParams(
        name=server_json["name"],
        version=server_json.get("version"),
        task_to_domain=server_json.get("taskToDomain"),
        workflow_definition=server_json.get("workflowDefinition"),
        idempotency_key=server_json.get("idempotencyKey"),
        idempotency_strategy=server_json.get("idempotencyStrategy"),
        priority=server_json.get("priority"),
    )
    assert model_obj.name == server_json["name"]
    if "version" in server_json:
        assert model_obj.version == server_json["version"]
    if "taskToDomain" in server_json:
        assert model_obj.task_to_domain == server_json["taskToDomain"]
        if server_json["taskToDomain"] and len(server_json["taskToDomain"]) > 0:
            first_key = next(iter(server_json["taskToDomain"].keys()))
            assert (
                model_obj.task_to_domain[first_key]
                == server_json["taskToDomain"][first_key]
            )
    if "workflowDefinition" in server_json:
        assert model_obj.workflow_definition == server_json["workflowDefinition"]
    if "idempotencyKey" in server_json:
        assert model_obj.idempotency_key == server_json["idempotencyKey"]
    if "idempotencyStrategy" in server_json:
        assert model_obj.idempotency_strategy == server_json["idempotencyStrategy"]
    if "priority" in server_json:
        assert model_obj.priority == server_json["priority"]
    model_dict = model_obj.to_dict()
    if "name" in server_json:
        assert model_dict["name"] == server_json["name"]
    if "version" in server_json:
        assert model_dict["version"] == server_json["version"]
    if "taskToDomain" in server_json:
        assert model_dict["task_to_domain"] == server_json["taskToDomain"]
    if "workflowDefinition" in server_json:
        assert model_dict["workflow_definition"] == server_json["workflowDefinition"]
    if "idempotencyKey" in server_json:
        assert model_dict["idempotency_key"] == server_json["idempotencyKey"]
    if "idempotencyStrategy" in server_json:
        assert model_dict["idempotency_strategy"] == server_json["idempotencyStrategy"]
    if "priority" in server_json:
        assert model_dict["priority"] == server_json["priority"]
