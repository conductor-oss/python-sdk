import unittest
import json
from typing import Set
from conductor.client.http.models.workflow_summary import WorkflowSummary
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestWorkflowSummarySerialization(unittest.TestCase):
    def setUp(self):
        # Load JSON template using JsonTemplateResolver
        self.server_json_str = JsonTemplateResolver.get_json_string("WorkflowSummary")
        self.server_json = json.loads(self.server_json_str)

    def test_workflow_summary_serde(self):
        # Test deserialization from JSON to SDK model
        model = WorkflowSummary(
            workflow_type=self.server_json.get("workflowType"),
            version=self.server_json.get("version"),
            workflow_id=self.server_json.get("workflowId"),
            correlation_id=self.server_json.get("correlationId"),
            start_time=self.server_json.get("startTime"),
            update_time=self.server_json.get("updateTime"),
            end_time=self.server_json.get("endTime"),
            status=self.server_json.get("status"),
            input=self.server_json.get("input"),
            output=self.server_json.get("output"),
            reason_for_incompletion=self.server_json.get("reasonForIncompletion"),
            execution_time=self.server_json.get("executionTime"),
            event=self.server_json.get("event"),
            failed_reference_task_names=self.server_json.get("failedReferenceTaskNames"),
            external_input_payload_storage_path=self.server_json.get("externalInputPayloadStoragePath"),
            external_output_payload_storage_path=self.server_json.get("externalOutputPayloadStoragePath"),
            priority=self.server_json.get("priority"),
            created_by=self.server_json.get("createdBy"),
            output_size=self.server_json.get("outputSize"),
            input_size=self.server_json.get("inputSize"),
            failed_task_names=set(self.server_json.get("failedTaskNames", []))
        )

        # Verify all fields are properly populated
        self._verify_fields(model)

        # Serialize the model back to a dict
        serialized_dict = model.to_dict()

        # Transform Python snake_case keys to JSON camelCase
        json_dict = self._transform_to_json_format(serialized_dict)

        # Verify the serialized JSON matches the original (with expected transformations)
        self._verify_json_matches(json_dict, self.server_json)

    def _verify_fields(self, model: WorkflowSummary):
        """Verify all fields in the model are correctly populated."""
        self.assertEqual(model.workflow_type, self.server_json.get("workflowType"))
        self.assertEqual(model.version, self.server_json.get("version"))
        self.assertEqual(model.workflow_id, self.server_json.get("workflowId"))
        self.assertEqual(model.correlation_id, self.server_json.get("correlationId"))
        self.assertEqual(model.start_time, self.server_json.get("startTime"))
        self.assertEqual(model.update_time, self.server_json.get("updateTime"))
        self.assertEqual(model.end_time, self.server_json.get("endTime"))
        self.assertEqual(model.status, self.server_json.get("status"))
        self.assertEqual(model.input, self.server_json.get("input"))
        self.assertEqual(model.output, self.server_json.get("output"))
        self.assertEqual(model.reason_for_incompletion, self.server_json.get("reasonForIncompletion"))
        self.assertEqual(model.execution_time, self.server_json.get("executionTime"))
        self.assertEqual(model.event, self.server_json.get("event"))
        self.assertEqual(model.failed_reference_task_names, self.server_json.get("failedReferenceTaskNames"))
        self.assertEqual(model.external_input_payload_storage_path,
                         self.server_json.get("externalInputPayloadStoragePath"))
        self.assertEqual(model.external_output_payload_storage_path,
                         self.server_json.get("externalOutputPayloadStoragePath"))
        self.assertEqual(model.priority, self.server_json.get("priority"))
        self.assertEqual(model.created_by, self.server_json.get("createdBy"))

        # Special handling for Set type
        if "failedTaskNames" in self.server_json:
            self.assertIsInstance(model.failed_task_names, set)
            self.assertEqual(model.failed_task_names, set(self.server_json.get("failedTaskNames")))


    def _transform_to_json_format(self, python_dict):
        """Transform Python dict keys from snake_case to camelCase for JSON comparison."""
        attribute_map = WorkflowSummary.attribute_map
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

    def _verify_json_matches(self, transformed_dict, original_json):
        """Verify that the serialized and transformed dict matches the original JSON."""
        # Check that all fields in the original JSON are present in the transformed dict
        for key in original_json:
            # Handle special case for failedTaskNames (set in Python, list in JSON)
            if key == "failedTaskNames":
                self.assertIn(key, transformed_dict)
                self.assertIsInstance(transformed_dict[key], list)
                self.assertEqual(set(transformed_dict[key]), set(original_json[key]))
            else:
                self.assertIn(key, transformed_dict)
                self.assertEqual(transformed_dict[key], original_json[key])


if __name__ == '__main__':
    unittest.main()