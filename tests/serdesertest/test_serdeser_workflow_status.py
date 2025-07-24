import unittest
import json
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
from conductor.client.http.models.workflow_status import WorkflowStatus


class TestWorkflowStatusSerDes(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("WorkflowStatus")
        self.server_json = json.loads(self.server_json_str)

    def test_workflow_status_ser_des(self):
        # 1. Test deserialization from server JSON to SDK model
        workflow_status = WorkflowStatus(
            workflow_id=self.server_json.get("workflowId"),
            correlation_id=self.server_json.get("correlationId"),
            output=self.server_json.get("output"),
            variables=self.server_json.get("variables"),
            status=self.server_json.get("status")
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("workflowId"), workflow_status.workflow_id)
        self.assertEqual(self.server_json.get("correlationId"), workflow_status.correlation_id)
        self.assertEqual(self.server_json.get("output"), workflow_status.output)
        self.assertEqual(self.server_json.get("variables"), workflow_status.variables)
        self.assertEqual(self.server_json.get("status"), workflow_status.status)

        # Check status-based methods work correctly
        if workflow_status.status in ['COMPLETED', 'FAILED', 'TIMED_OUT', 'TERMINATED']:
            self.assertTrue(workflow_status.is_completed())
        else:
            self.assertFalse(workflow_status.is_completed())

        if workflow_status.status in ['PAUSED', 'COMPLETED']:
            self.assertTrue(workflow_status.is_successful())
        else:
            self.assertFalse(workflow_status.is_successful())

        if workflow_status.status in ['RUNNING', 'PAUSED']:
            self.assertTrue(workflow_status.is_running())
        else:
            self.assertFalse(workflow_status.is_running())

        # 3. Test serialization back to JSON
        serialized_json = workflow_status.to_dict()

        # 4. Verify the serialized JSON matches the original JSON
        self.assertEqual(self.server_json.get("workflowId"), serialized_json.get("workflow_id"))
        self.assertEqual(self.server_json.get("correlationId"), serialized_json.get("correlation_id"))
        self.assertEqual(self.server_json.get("output"), serialized_json.get("output"))
        self.assertEqual(self.server_json.get("variables"), serialized_json.get("variables"))
        self.assertEqual(self.server_json.get("status"), serialized_json.get("status"))

        # Additional test for special data structures if present in the template
        if isinstance(self.server_json.get("output"), dict):
            self.assertEqual(self.server_json.get("output"), workflow_status.output)

        if isinstance(self.server_json.get("variables"), dict):
            self.assertEqual(self.server_json.get("variables"), workflow_status.variables)


if __name__ == "__main__":
    unittest.main()