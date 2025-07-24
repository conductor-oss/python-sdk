import unittest
import json
from conductor.client.http.models.skip_task_request import SkipTaskRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestSkipTaskRequestSerDes(unittest.TestCase):
    def setUp(self):
        # Load JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("SkipTaskRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_skip_task_request_serde(self):
        # 1. Deserialize server JSON to model using constructor
        model = SkipTaskRequest(
            task_input=self.server_json.get('taskInput'),
            task_output=self.server_json.get('taskOutput')
        )

        # 2. Verify all fields populated correctly
        self.assertEqual(self.server_json.get('taskInput'), model.task_input)
        self.assertEqual(self.server_json.get('taskOutput'), model.task_output)

        # Verify nested structures if they exist
        if isinstance(model.task_input, dict):
            for key, value in self.server_json.get('taskInput').items():
                self.assertEqual(value, model.task_input.get(key))

        if isinstance(model.task_output, dict):
            for key, value in self.server_json.get('taskOutput').items():
                self.assertEqual(value, model.task_output.get(key))

        # 3. Create a dict manually matching the server format
        json_from_model = {
            'taskInput': model.task_input,
            'taskOutput': model.task_output
        }

        # Remove None values
        json_from_model = {k: v for k, v in json_from_model.items() if v is not None}

        # 4. Compare with original JSON
        self.assertEqual(self.server_json, json_from_model)


if __name__ == '__main__':
    unittest.main()