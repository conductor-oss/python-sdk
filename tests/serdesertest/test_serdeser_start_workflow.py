import unittest
import json
from conductor.client.http.models.start_workflow import StartWorkflow
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestStartWorkflowSerDes(unittest.TestCase):
    def setUp(self):
        # Load JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("EventHandler.StartWorkflow")
        self.server_json = json.loads(self.server_json_str)

    def test_serdes_start_workflow(self):
        # 1. Test deserialization of JSON to model
        model = StartWorkflow(
            name=self.server_json.get("name"),
            version=self.server_json.get("version"),
            correlation_id=self.server_json.get("correlationId"),
            input=self.server_json.get("input"),
            task_to_domain=self.server_json.get("taskToDomain")
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("name"), model.name)
        self.assertEqual(self.server_json.get("version"), model.version)
        self.assertEqual(self.server_json.get("correlationId"), model.correlation_id)

        # Verify maps are properly populated
        if "input" in self.server_json:
            self.assertIsNotNone(model.input)
            self.assertEqual(self.server_json.get("input"), model.input)
            # Check sample values based on template expectations
            if isinstance(model.input, dict) and len(model.input) > 0:
                # Verify the structure matches what we expect
                first_key = next(iter(model.input))
                self.assertIsNotNone(first_key)

        if "taskToDomain" in self.server_json:
            self.assertIsNotNone(model.task_to_domain)
            self.assertEqual(self.server_json.get("taskToDomain"), model.task_to_domain)
            # Check sample values for task_to_domain
            if isinstance(model.task_to_domain, dict) and len(model.task_to_domain) > 0:
                first_key = next(iter(model.task_to_domain))
                self.assertIsNotNone(first_key)
                self.assertIsInstance(model.task_to_domain[first_key], str)

        # 3. Test serialization of model back to JSON
        model_dict = model.to_dict()

        # 4. Verify the resulting JSON matches the original with field name transformations
        # Checking camelCase (JSON) to snake_case (Python) transformations
        self.assertEqual(self.server_json.get("name"), model_dict.get("name"))
        self.assertEqual(self.server_json.get("version"), model_dict.get("version"))
        self.assertEqual(self.server_json.get("correlationId"), model_dict.get("correlation_id"))
        self.assertEqual(self.server_json.get("input"), model_dict.get("input"))
        self.assertEqual(self.server_json.get("taskToDomain"), model_dict.get("task_to_domain"))


if __name__ == '__main__':
    unittest.main()