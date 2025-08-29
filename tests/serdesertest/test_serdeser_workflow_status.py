import json

import pytest

from conductor.client.http.models.workflow_status import WorkflowStatusAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("WorkflowStatus")
    return json.loads(server_json_str)


def test_workflow_status_ser_des(server_json):
    # 1. Test deserialization from server JSON to SDK model
    workflow_status = WorkflowStatusAdapter(
        workflow_id=server_json.get("workflowId"),
        correlation_id=server_json.get("correlationId"),
        output=server_json.get("output"),
        variables=server_json.get("variables"),
        status=server_json.get("status"),
    )
    # 2. Verify all fields are properly populated
    assert server_json.get("workflowId") == workflow_status.workflow_id
    assert server_json.get("correlationId") == workflow_status.correlation_id
    assert server_json.get("output") == workflow_status.output
    assert server_json.get("variables") == workflow_status.variables
    assert server_json.get("status") == workflow_status.status
    # Check status-based methods work correctly
    if workflow_status.status in ["COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"]:
        assert workflow_status.is_completed()
    else:
        assert not workflow_status.is_completed()
    if workflow_status.status in ["PAUSED", "COMPLETED"]:
        assert workflow_status.is_successful()
    else:
        assert not workflow_status.is_successful()
    if workflow_status.status in ["RUNNING", "PAUSED"]:
        assert workflow_status.is_running()
    else:
        assert not workflow_status.is_running()
    # 3. Test serialization back to JSON
    serialized_json = workflow_status.to_dict()
    # 4. Verify the serialized JSON matches the original JSON
    assert server_json.get("workflowId") == serialized_json.get("workflow_id")
    assert server_json.get("correlationId") == serialized_json.get("correlation_id")
    assert server_json.get("output") == serialized_json.get("output")
    assert server_json.get("variables") == serialized_json.get("variables")
    assert server_json.get("status") == serialized_json.get("status")
    # Additional test for special data structures if present in the template
    if isinstance(server_json.get("output"), dict):
        assert server_json.get("output") == workflow_status.output
    if isinstance(server_json.get("variables"), dict):
        assert server_json.get("variables") == workflow_status.variables
