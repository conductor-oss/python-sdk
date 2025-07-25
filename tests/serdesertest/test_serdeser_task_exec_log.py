import unittest
import json
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
from conductor.client.http.models.task_exec_log import TaskExecLog


class TaskExecLogSerdeserTest(unittest.TestCase):
    """
    Test class for validating serialization/deserialization of TaskExecLog model
    """

    def setUp(self):
        """
        Set up test fixtures
        """
        self.server_json_str = JsonTemplateResolver.get_json_string("TaskExecLog")
        self.server_json = json.loads(self.server_json_str)

    def test_task_exec_log_serdeser(self):
        """
        Test serialization and deserialization of TaskExecLog
        """
        # 1. Deserialize JSON into SDK model object
        task_exec_log = TaskExecLog(
            log=self.server_json.get("log"),
            task_id=self.server_json.get("taskId"),
            created_time=self.server_json.get("createdTime")
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("log"), task_exec_log.log)
        self.assertEqual(self.server_json.get("taskId"), task_exec_log.task_id)
        self.assertEqual(self.server_json.get("createdTime"), task_exec_log.created_time)

        # 3. Serialize SDK model back to dictionary
        task_exec_log_dict = task_exec_log.to_dict()

        # 4. Verify serialized dictionary matches original JSON
        # Check the original JSON attributes are in the serialized dictionary
        self.assertEqual(self.server_json.get("log"), task_exec_log_dict.get("log"))
        # Handle camelCase to snake_case transformations
        self.assertEqual(self.server_json.get("taskId"), task_exec_log_dict.get("task_id"))
        self.assertEqual(self.server_json.get("createdTime"), task_exec_log_dict.get("created_time"))

        # Verify no data is lost (all keys from original JSON exist in serialized output)
        for key in self.server_json:
            if key == "taskId":
                self.assertIn("task_id", task_exec_log_dict)
            elif key == "createdTime":
                self.assertIn("created_time", task_exec_log_dict)
            else:
                self.assertIn(key, task_exec_log_dict)

if __name__ == '__main__':
    unittest.main()