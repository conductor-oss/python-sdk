import unittest
import json
from conductor.client.http.models.task_details import TaskDetails
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTaskDetailsSerialization(unittest.TestCase):
    """Test case to validate serialization and deserialization of TaskDetails model."""

    def setUp(self):
        """Set up test fixtures."""
        self.server_json_str = JsonTemplateResolver.get_json_string("EventHandler.TaskDetails")
        self.server_json = json.loads(self.server_json_str)

    def test_task_details_serde(self):
        """
        Test serialization and deserialization of TaskDetails model.

        This test verifies:
        1. Server JSON can be correctly deserialized into TaskDetails object
        2. All fields are properly populated during deserialization
        3. The TaskDetails object can be serialized back to JSON
        4. The resulting JSON matches the original, ensuring no data is lost
        """
        # 1. Deserialize JSON into TaskDetails object
        task_details = TaskDetails(
            workflow_id=self.server_json.get('workflowId'),
            task_ref_name=self.server_json.get('taskRefName'),
            output=self.server_json.get('output'),
            task_id=self.server_json.get('taskId')
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get('workflowId'), task_details.workflow_id)
        self.assertEqual(self.server_json.get('taskRefName'), task_details.task_ref_name)
        self.assertEqual(self.server_json.get('output'), task_details.output)
        self.assertEqual(self.server_json.get('taskId'), task_details.task_id)

        # Test the put_output_item method
        if task_details.output is None:
            task_details.put_output_item("test_key", "test_value")
            self.assertEqual({"test_key": "test_value"}, task_details.output)
        else:
            original_size = len(task_details.output)
            task_details.put_output_item("test_key", "test_value")
            self.assertEqual(original_size + 1, len(task_details.output))
            self.assertEqual("test_value", task_details.output.get("test_key"))

        # 3. Serialize TaskDetails object back to dictionary
        task_details_dict = task_details.to_dict()

        # 4. Compare the serialized dictionary with the original JSON
        # Note: We need to handle the test_key we added separately
        expected_dict = {
            'workflow_id': self.server_json.get('workflowId'),
            'task_ref_name': self.server_json.get('taskRefName'),
            'output': self.server_json.get('output'),
            'task_id': self.server_json.get('taskId')
        }

        # If output was None in the original, it would now be {"test_key": "test_value"}
        if expected_dict['output'] is None:
            expected_dict['output'] = {"test_key": "test_value"}
        else:
            expected_dict['output'] = {**expected_dict['output'], "test_key": "test_value"}

        for key, value in expected_dict.items():
            if key == 'output':
                for output_key, output_value in value.items():
                    self.assertEqual(output_value, task_details_dict[key].get(output_key))
            else:
                self.assertEqual(value, task_details_dict[key])


if __name__ == '__main__':
    unittest.main()