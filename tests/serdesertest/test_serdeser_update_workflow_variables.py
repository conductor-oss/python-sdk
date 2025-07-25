import json
import unittest
from dataclasses import asdict
from conductor.client.http.models.update_workflow_variables import UpdateWorkflowVariables
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestUpdateWorkflowVariables(unittest.TestCase):
    """Test serialization and deserialization of UpdateWorkflowVariables model."""

    def setUp(self):
        """Set up test fixtures."""
        self.server_json_str = JsonTemplateResolver.get_json_string("EventHandler.UpdateWorkflowVariables")
        self.server_json = json.loads(self.server_json_str)

    def test_update_workflow_variables_serde(self):
        """Test serialization and deserialization of UpdateWorkflowVariables.

        Verifies:
        1. Server JSON can be correctly deserialized into SDK model object
        2. All fields are properly populated during deserialization
        3. The SDK model can be serialized back to JSON
        4. The resulting JSON matches the original
        """
        # 1. Deserialize JSON into model object
        model = UpdateWorkflowVariables(
            workflow_id=self.server_json.get("workflowId"),
            variables=self.server_json.get("variables"),
            append_array=self.server_json.get("appendArray")
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(model.workflow_id, self.server_json.get("workflowId"))
        self.assertEqual(model.variables, self.server_json.get("variables"))
        self.assertEqual(model.append_array, self.server_json.get("appendArray"))

        # Verify complex data structures (if present)
        if model.variables:
            self.assertIsInstance(model.variables, dict)
            # Additional verification for specific variable types could be added here

        # 3. Serialize model back to JSON
        model_json = model.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(model_json.get("workflowId"), self.server_json.get("workflowId"))
        self.assertEqual(model_json.get("variables"), self.server_json.get("variables"))
        self.assertEqual(model_json.get("appendArray"), self.server_json.get("appendArray"))


if __name__ == '__main__':
    unittest.main()