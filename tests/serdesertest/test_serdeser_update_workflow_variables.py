import json

import pytest

from conductor.client.adapters.models.update_workflow_variables_adapter import (
    UpdateWorkflowVariablesAdapter,
)
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string(
        "EventHandler.UpdateWorkflowVariables"
    )
    return json.loads(server_json_str)


def test_update_workflow_variables_serde(server_json):
    """Test serialization and deserialization of UpdateWorkflowVariables.
    Verifies:
    1. Server JSON can be correctly deserialized into SDK model object
    2. All fields are properly populated during deserialization
    3. The SDK model can be serialized back to JSON
    4. The resulting JSON matches the original
    """
    # 1. Deserialize JSON into model object
    model = UpdateWorkflowVariablesAdapter(
        workflow_id=server_json.get("workflowId"),
        variables=server_json.get("variables"),
        append_array=server_json.get("appendArray"),
    )
    # 2. Verify all fields are properly populated
    assert model.workflow_id == server_json.get("workflowId")
    assert model.variables == server_json.get("variables")
    assert model.append_array == server_json.get("appendArray")
    # Verify complex data structures (if present)
    if model.variables:
        assert isinstance(model.variables, dict)
        # Additional verification for specific variable types could be added here
    # 3. Serialize model back to JSON
    model_json = model.to_dict()
    # 4. Verify the resulting JSON matches the original
    assert model_json.get("workflow_id") == server_json.get("workflowId")
    assert model_json.get("variables") == server_json.get("variables")
    assert model_json.get("append_array") == server_json.get("appendArray")
