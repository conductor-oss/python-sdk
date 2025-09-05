import json

import pytest

from conductor.client.http.models.terminate_workflow import TerminateWorkflowAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string(
        "EventHandler.TerminateWorkflow"
    )
    return json.loads(server_json_str)


def test_terminate_workflow_ser_des(server_json):
    """Test serialization and deserialization of TerminateWorkflow model."""
    # 1. Verify server JSON can be correctly deserialized
    model_obj = TerminateWorkflowAdapter(
        workflow_id=server_json["workflowId"],
        termination_reason=server_json["terminationReason"],
    )
    # 2. Verify all fields are properly populated during deserialization
    assert server_json["workflowId"] == model_obj.workflow_id
    assert server_json["terminationReason"] == model_obj.termination_reason
    # 3. Verify SDK model can be serialized back to JSON
    result_json = model_obj.to_dict()
    # 4. Verify resulting JSON matches original
    assert server_json["workflowId"] == result_json["workflow_id"]
    assert server_json["terminationReason"] == result_json["termination_reason"]
    # Verify no extra keys were added
    assert len(server_json) == len(result_json)
    # Check string representation
    assert model_obj.workflow_id in repr(model_obj)
    assert model_obj.termination_reason in repr(model_obj)
