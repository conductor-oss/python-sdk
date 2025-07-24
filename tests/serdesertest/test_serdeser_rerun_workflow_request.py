import unittest
import json
from copy import deepcopy

from conductor.client.http.models import RerunWorkflowRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestRerunWorkflowRequestSerialization(unittest.TestCase):
    """Test serialization and deserialization of RerunWorkflowRequest."""

    def setUp(self):
        """Set up test data."""
        # Get the JSON template for RerunWorkflowRequest
        self.server_json_str = JsonTemplateResolver.get_json_string("RerunWorkflowRequest")
        self.request_json = json.loads(self.server_json_str)

        # Create the SDK object for reuse in multiple tests
        self.request_obj = RerunWorkflowRequest()
        self.request_obj.re_run_from_workflow_id = self.request_json["reRunFromWorkflowId"]
        self.request_obj.workflow_input = self.request_json["workflowInput"]
        self.request_obj.re_run_from_task_id = self.request_json["reRunFromTaskId"]
        self.request_obj.task_input = self.request_json["taskInput"]
        self.request_obj.correlation_id = self.request_json["correlationId"]

        # Transform SDK object dict to match server format (for reuse in tests)
        result_dict = self.request_obj.to_dict()
        self.transformed_dict = {
            "reRunFromWorkflowId": result_dict["re_run_from_workflow_id"],
            "workflowInput": result_dict["workflow_input"],
            "reRunFromTaskId": result_dict["re_run_from_task_id"],
            "taskInput": result_dict["task_input"],
            "correlationId": result_dict["correlation_id"]
        }

    def test_serialization_deserialization_cycle(self):
        """Test the complete serialization/deserialization cycle."""
        # 1. Test deserialization: Assert that fields are correctly populated
        self.assertEqual(self.request_obj.re_run_from_workflow_id, "sample_reRunFromWorkflowId")
        self.assertEqual(self.request_obj.re_run_from_task_id, "sample_reRunFromTaskId")
        self.assertEqual(self.request_obj.correlation_id, "sample_correlationId")

        # Check dictionary fields (maps)
        self.assertIsInstance(self.request_obj.workflow_input, dict)
        self.assertEqual(self.request_obj.workflow_input["sample_key"], "sample_value")

        self.assertIsInstance(self.request_obj.task_input, dict)
        self.assertEqual(self.request_obj.task_input["sample_key"], "sample_value")

        # 2. Test serialization: Compare individual fields
        self.assertEqual(self.transformed_dict["reRunFromWorkflowId"], self.request_json["reRunFromWorkflowId"])
        self.assertEqual(self.transformed_dict["reRunFromTaskId"], self.request_json["reRunFromTaskId"])
        self.assertEqual(self.transformed_dict["correlationId"], self.request_json["correlationId"])

        # Compare dictionary fields
        self.assertEqual(self.transformed_dict["workflowInput"], self.request_json["workflowInput"])
        self.assertEqual(self.transformed_dict["taskInput"], self.request_json["taskInput"])

        # 3. Ensure no fields are missing
        self.assertEqual(set(self.transformed_dict.keys()), set(self.request_json.keys()))

        # 4. Test full cycle with deep equality
        self.assertEqual(self.transformed_dict, self.request_json)


if __name__ == "__main__":
    unittest.main()