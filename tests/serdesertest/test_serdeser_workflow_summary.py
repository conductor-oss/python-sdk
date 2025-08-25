import json

import pytest

from conductor.client.adapters.models.workflow_summary_adapter import WorkflowSummaryAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("WorkflowSummary")
    return json.loads(server_json_str)


def test_workflow_summary_serde(server_json):
    # Test deserialization from JSON to SDK model
    model = WorkflowSummaryAdapter(
        workflow_type=server_json.get("workflowType"),
        version=server_json.get("version"),
        workflow_id=server_json.get("workflowId"),
        correlation_id=server_json.get("correlationId"),
        start_time=server_json.get("startTime"),
        update_time=server_json.get("updateTime"),
        end_time=server_json.get("endTime"),
        status=server_json.get("status"),
        input=server_json.get("input"),
        output=server_json.get("output"),
        reason_for_incompletion=server_json.get("reasonForIncompletion"),
        execution_time=server_json.get("executionTime"),
        event=server_json.get("event"),
        failed_reference_task_names=server_json.get("failedReferenceTaskNames"),
        external_input_payload_storage_path=server_json.get(
            "externalInputPayloadStoragePath"
        ),
        external_output_payload_storage_path=server_json.get(
            "externalOutputPayloadStoragePath"
        ),
        priority=server_json.get("priority"),
        created_by=server_json.get("createdBy"),
        output_size=server_json.get("outputSize"),
        input_size=server_json.get("inputSize"),
        failed_task_names=set(server_json.get("failedTaskNames", [])),
    )
    _verify_fields(model, server_json)
    # Serialize the model back to a dict
    serialized_dict = model.to_dict()
    # Transform Python snake_case keys to JSON camelCase
    json_dict = _transform_to_json_format(serialized_dict)
    # Verify the serialized JSON matches the original (with expected transformations)
    _verify_json_matches(json_dict, server_json)


def _verify_fields(model: WorkflowSummaryAdapter, server_json):
    """Verify all fields in the model are correctly populated."""
    assert model.workflow_type == server_json.get("workflowType")
    assert model.version == server_json.get("version")
    assert model.workflow_id == server_json.get("workflowId")
    assert model.correlation_id == server_json.get("correlationId")
    assert model.start_time == server_json.get("startTime")
    assert model.update_time == server_json.get("updateTime")
    assert model.end_time == server_json.get("endTime")
    assert model.status == server_json.get("status")
    assert model.input == server_json.get("input")
    assert model.output == server_json.get("output")
    assert model.reason_for_incompletion == server_json.get("reasonForIncompletion")
    assert model.execution_time == server_json.get("executionTime")
    assert model.event == server_json.get("event")
    assert model.failed_reference_task_names == server_json.get(
        "failedReferenceTaskNames"
    )
    assert model.external_input_payload_storage_path == server_json.get(
        "externalInputPayloadStoragePath"
    )
    assert model.external_output_payload_storage_path == server_json.get(
        "externalOutputPayloadStoragePath"
    )
    assert model.priority == server_json.get("priority")
    assert model.created_by == server_json.get("createdBy")
    # Special handling for Set type
    if "failedTaskNames" in server_json:
        assert isinstance(model.failed_task_names, set)
        assert model.failed_task_names == set(server_json.get("failedTaskNames"))


def _transform_to_json_format(python_dict):
    """Transform Python dict keys from snake_case to camelCase for JSON comparison."""
    attribute_map = WorkflowSummaryAdapter.attribute_map
    result = {}
    for py_key, value in python_dict.items():
        # Get the corresponding JSON key from attribute_map
        if py_key in attribute_map:
            json_key = attribute_map[py_key]
            # Handle special types (lists, dicts, etc.)
            if isinstance(value, set):
                result[json_key] = list(value)
            elif isinstance(value, dict):
                # Handle nested dictionaries if needed
                result[json_key] = value
            else:
                result[json_key] = value
    return result


def _verify_json_matches(transformed_dict, original_json):
    """Verify that the serialized and transformed dict matches the original JSON."""
    # Check that all fields in the original JSON are present in the transformed dict
    for key in original_json:
        # Handle special case for failedTaskNames (set in Python, list in JSON)
        if key == "failedTaskNames":
            assert key in transformed_dict
            assert isinstance(transformed_dict[key], list)
            assert set(transformed_dict[key]) == set(original_json[key])
        else:
            assert key in transformed_dict
            assert transformed_dict[key] == original_json[key]
