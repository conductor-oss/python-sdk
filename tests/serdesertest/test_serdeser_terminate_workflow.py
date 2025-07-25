import unittest
import json
from conductor.client.http.models.terminate_workflow import TerminateWorkflow
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTerminateWorkflowSerDes(unittest.TestCase):
    """Test serialization and deserialization of TerminateWorkflow model."""

    def setUp(self):
        """Set up test environment."""
        self.server_json_str = JsonTemplateResolver.get_json_string("EventHandler.TerminateWorkflow")
        self.server_json = json.loads(self.server_json_str)

    def test_terminate_workflow_ser_des(self):
        """Test serialization and deserialization of TerminateWorkflow model."""
        # 1. Verify server JSON can be correctly deserialized
        model_obj = TerminateWorkflow(
            workflow_id=self.server_json["workflowId"],
            termination_reason=self.server_json["terminationReason"]
        )

        # 2. Verify all fields are properly populated during deserialization
        self.assertEqual(self.server_json["workflowId"], model_obj.workflow_id)
        self.assertEqual(self.server_json["terminationReason"], model_obj.termination_reason)

        # 3. Verify SDK model can be serialized back to JSON
        result_json = model_obj.to_dict()

        # 4. Verify resulting JSON matches original
        self.assertEqual(self.server_json["workflowId"], result_json["workflowId"])
        self.assertEqual(self.server_json["terminationReason"], result_json["terminationReason"])

        # Verify no data loss by checking all keys exist
        for key in self.server_json:
            self.assertIn(key, result_json)

        # Verify no extra keys were added
        self.assertEqual(len(self.server_json), len(result_json))

        # Check string representation
        self.assertIn(model_obj.workflow_id, repr(model_obj))
        self.assertIn(model_obj.termination_reason, repr(model_obj))


if __name__ == "__main__":
    unittest.main()