import json

import pytest
from conductor.client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.shared.http.enums import IdempotencyStrategy
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("StartWorkflowRequest"))


def test_deserialize_serialize_start_workflow_request(server_json):
    workflow_request = StartWorkflowRequestAdapter(
        name=server_json.get("name"),
        version=server_json.get("version"),
        correlation_id=server_json.get("correlationId"),
        input=server_json.get("input"),
        task_to_domain=server_json.get("taskToDomain"),
        workflow_def=server_json.get("workflowDef"),
        external_input_payload_storage_path=server_json.get(
            "externalInputPayloadStoragePath"
        ),
        priority=server_json.get("priority"),
        created_by=server_json.get("createdBy"),
        idempotency_key=server_json.get("idempotencyKey"),
        idempotency_strategy=IdempotencyStrategy(
            server_json.get("idempotencyStrategy", "FAIL")
        ),
    )
    assert server_json.get("name") == workflow_request.name
    assert server_json.get("version") == workflow_request.version
    assert server_json.get("correlationId") == workflow_request.correlation_id
    assert server_json.get("input") == workflow_request.input
    assert server_json.get("taskToDomain") == workflow_request.task_to_domain
    assert server_json.get("workflowDef") == workflow_request.workflow_def
    assert (
        server_json.get("externalInputPayloadStoragePath")
        == workflow_request.external_input_payload_storage_path
    )
    assert server_json.get("priority") == workflow_request.priority
    assert server_json.get("createdBy") == workflow_request.created_by
    assert server_json.get("idempotencyKey") == workflow_request.idempotency_key
    expected_strategy = IdempotencyStrategy(
        server_json.get("idempotencyStrategy", "FAIL")
    )
    assert expected_strategy == workflow_request.idempotency_strategy
    result_dict = workflow_request.to_dict()
    assert server_json.get("name") == result_dict.get("name")
    assert server_json.get("version") == result_dict.get("version")
    assert server_json.get("correlationId") == result_dict.get("correlation_id")
    assert server_json.get("input") == result_dict.get("input")
    assert server_json.get("taskToDomain") == result_dict.get("task_to_domain")
    assert server_json.get("workflowDef") == result_dict.get("workflow_def")
    assert server_json.get("externalInputPayloadStoragePath") == result_dict.get(
        "external_input_payload_storage_path"
    )
    assert server_json.get("priority") == result_dict.get("priority")
    assert server_json.get("createdBy") == result_dict.get("created_by")
    assert server_json.get("idempotencyKey") == result_dict.get("idempotency_key")
    expected_strategy_str = server_json.get("idempotencyStrategy", "FAIL")
    if isinstance(expected_strategy_str, tuple):
        expected_strategy_str = expected_strategy_str[0]
    assert expected_strategy_str == str(result_dict.get("idempotency_strategy"))
