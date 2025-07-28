import json

import pytest

from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_test_request import (
    TaskMock,
    WorkflowTestRequest,
)
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("WorkflowTestRequest")
    return json.loads(server_json_str)


def snake_to_camel(snake_case):
    """Convert snake_case to camelCase"""
    components = snake_case.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def test_workflow_test_request_serdes(server_json):  # noqa: PLR0915
    """Test serialization and deserialization of WorkflowTestRequest"""
    # 1. Deserialize JSON into SDK model object
    workflow_test_request = WorkflowTestRequest(
        correlation_id=server_json.get("correlationId"),
        created_by=server_json.get("createdBy"),
        external_input_payload_storage_path=server_json.get(
            "externalInputPayloadStoragePath"
        ),
        input=server_json.get("input"),
        name=server_json.get("name"),
        priority=server_json.get("priority"),
        version=server_json.get("version"),
    )
    # Handle complex nested structures
    if "taskToDomain" in server_json:
        workflow_test_request.task_to_domain = server_json.get("taskToDomain")
    # Handle workflowDef object if present
    if "workflowDef" in server_json and server_json["workflowDef"] is not None:
        workflow_def = WorkflowDef()
        # Assuming there are fields in WorkflowDef that need to be populated
        workflow_test_request.workflow_def = workflow_def
    # Handle subWorkflowTestRequest if present
    if server_json.get("subWorkflowTestRequest"):
        sub_workflow_dict = {}
        for key, value in server_json["subWorkflowTestRequest"].items():
            # Create a sub-request for each entry
            sub_request = WorkflowTestRequest(name=value.get("name"))
            sub_workflow_dict[key] = sub_request
        workflow_test_request.sub_workflow_test_request = sub_workflow_dict
    # Handle taskRefToMockOutput if present
    if server_json.get("taskRefToMockOutput"):
        task_mock_dict = {}
        for task_ref, mock_list in server_json["taskRefToMockOutput"].items():
            task_mocks = []
            for mock_data in mock_list:
                task_mock = TaskMock(
                    status=mock_data.get("status", "COMPLETED"),
                    output=mock_data.get("output"),
                    execution_time=mock_data.get("executionTime", 0),
                    queue_wait_time=mock_data.get("queueWaitTime", 0),
                )
                task_mocks.append(task_mock)
            task_mock_dict[task_ref] = task_mocks
        workflow_test_request.task_ref_to_mock_output = task_mock_dict
    # 2. Verify all fields are properly populated
    assert server_json.get("correlationId") == workflow_test_request.correlation_id

    assert server_json.get("createdBy") == workflow_test_request.created_by
    assert server_json.get("name") == workflow_test_request.name
    assert server_json.get("priority") == workflow_test_request.priority
    assert server_json.get("version") == workflow_test_request.version
    # Verify complex nested structures if present
    if "taskToDomain" in server_json:
        assert server_json.get("taskToDomain") == workflow_test_request.task_to_domain
    if server_json.get("subWorkflowTestRequest"):
        assert workflow_test_request.sub_workflow_test_request is not None
        for key in server_json["subWorkflowTestRequest"]:
            assert key in workflow_test_request.sub_workflow_test_request
            assert (
                server_json["subWorkflowTestRequest"][key].get("name")
                == workflow_test_request.sub_workflow_test_request[key].name
            )
    if server_json.get("taskRefToMockOutput"):
        assert workflow_test_request.task_ref_to_mock_output is not None
        for task_ref in server_json["taskRefToMockOutput"]:
            assert task_ref in workflow_test_request.task_ref_to_mock_output
            for i, mock_data in enumerate(server_json["taskRefToMockOutput"][task_ref]):
                assert (
                    mock_data.get("status", "COMPLETED")
                    == workflow_test_request.task_ref_to_mock_output[task_ref][i].status
                )
                assert (
                    mock_data.get("output")
                    == workflow_test_request.task_ref_to_mock_output[task_ref][i].output
                )
    # 3. Serialize model back to JSON
    model_dict = workflow_test_request.to_dict()
    # Convert snake_case keys to camelCase for comparison with original JSON
    serialized_json = {}
    for key, value in model_dict.items():
        camel_key = snake_to_camel(key)
        serialized_json[camel_key] = value
    # 4. Verify the serialized JSON matches the original
    # Check basic fields match (allowing for null/None differences)
    if "correlationId" in server_json:
        assert server_json["correlationId"] == serialized_json["correlationId"]
    if "createdBy" in server_json:
        assert server_json["createdBy"] == serialized_json["createdBy"]
    if "name" in server_json:
        assert server_json["name"] == serialized_json["name"]
    if "priority" in server_json:
        assert server_json["priority"] == serialized_json["priority"]
    if "version" in server_json:
        assert server_json["version"] == serialized_json["version"]
    # Check maps and complex structures
    if "taskToDomain" in server_json:
        assert server_json["taskToDomain"] == serialized_json["taskToDomain"]
    # Verify that sub-workflow structure is preserved correctly
    if server_json.get("subWorkflowTestRequest"):
        assert "subWorkflowTestRequest" in serialized_json
        for key in server_json["subWorkflowTestRequest"]:
            assert key in serialized_json["subWorkflowTestRequest"]
            orig_name = server_json["subWorkflowTestRequest"][key].get("name")
            serial_obj = serialized_json["subWorkflowTestRequest"][key]
            # Handle the case where to_dict() might return a dictionary or an object
            if isinstance(serial_obj, dict):
                serial_name = serial_obj.get("name")
            else:
                # Assuming it's an object with attribute access
                serial_name = getattr(serial_obj, "name", None)
            assert orig_name == serial_name
    # Verify task mock outputs
    if server_json.get("taskRefToMockOutput"):
        assert "taskRefToMockOutput" in serialized_json
        for task_ref in server_json["taskRefToMockOutput"]:
            assert task_ref in serialized_json["taskRefToMockOutput"]
            for i, mock_data in enumerate(server_json["taskRefToMockOutput"][task_ref]):
                orig_status = mock_data.get("status", "COMPLETED")
                orig_output = mock_data.get("output")
                serial_mock = serialized_json["taskRefToMockOutput"][task_ref][i]
                # Handle the case where to_dict() might return a dictionary or an object
                if isinstance(serial_mock, dict):
                    serial_status = serial_mock.get("status")
                    serial_output = serial_mock.get("output")
                else:
                    # Assuming it's an object with attribute access
                    serial_status = getattr(serial_mock, "status", None)
                    serial_output = getattr(serial_mock, "output", None)
                assert orig_status == serial_status
                assert orig_output == serial_output
