import unittest
from conductor.client.http.models.sub_workflow_params import SubWorkflowParams
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestSubWorkflowParamsSerialization(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("SubWorkflowParams")
        self.server_json = json.loads(self.server_json_str)

    def test_serialization_deserialization(self):
        # 1. Deserialize JSON into model object
        model_obj = SubWorkflowParams(
            name=self.server_json["name"],
            version=self.server_json.get("version"),
            task_to_domain=self.server_json.get("taskToDomain"),
            workflow_definition=self.server_json.get("workflowDefinition"),
            idempotency_key=self.server_json.get("idempotencyKey"),
            idempotency_strategy=self.server_json.get("idempotencyStrategy"),
            priority=self.server_json.get("priority")
        )

        # 2. Verify all fields are correctly populated
        self.assertEqual(model_obj.name, self.server_json["name"])

        if "version" in self.server_json:
            self.assertEqual(model_obj.version, self.server_json["version"])

        if "taskToDomain" in self.server_json:
            # Verify map structure
            self.assertEqual(model_obj.task_to_domain, self.server_json["taskToDomain"])
            # Check a specific entry if available
            if self.server_json["taskToDomain"] and len(self.server_json["taskToDomain"]) > 0:
                first_key = next(iter(self.server_json["taskToDomain"].keys()))
                self.assertEqual(model_obj.task_to_domain[first_key], self.server_json["taskToDomain"][first_key])

        if "workflowDefinition" in self.server_json:
            # This would be a complex object that may need special handling
            self.assertEqual(model_obj.workflow_definition, self.server_json["workflowDefinition"])

        if "idempotencyKey" in self.server_json:
            self.assertEqual(model_obj.idempotency_key, self.server_json["idempotencyKey"])

        if "idempotencyStrategy" in self.server_json:
            # This is likely an enum that may need special handling
            self.assertEqual(model_obj.idempotency_strategy, self.server_json["idempotencyStrategy"])

        if "priority" in self.server_json:
            self.assertEqual(model_obj.priority, self.server_json["priority"])

        # 3. Serialize model back to dictionary
        model_dict = model_obj.to_dict()

        # 4. Verify the serialized dict matches original JSON structure
        # Check each field after transformation from snake_case back to camelCase
        if "name" in self.server_json:
            self.assertEqual(model_dict["name"], self.server_json["name"])

        if "version" in self.server_json:
            self.assertEqual(model_dict["version"], self.server_json["version"])

        if "taskToDomain" in self.server_json:
            self.assertEqual(model_dict["task_to_domain"], self.server_json["taskToDomain"])

        if "workflowDefinition" in self.server_json:
            self.assertEqual(model_dict["workflow_definition"], self.server_json["workflowDefinition"])

        if "idempotencyKey" in self.server_json:
            self.assertEqual(model_dict["idempotency_key"], self.server_json["idempotencyKey"])

        if "idempotencyStrategy" in self.server_json:
            self.assertEqual(model_dict["idempotency_strategy"], self.server_json["idempotencyStrategy"])

        if "priority" in self.server_json:
            self.assertEqual(model_dict["priority"], self.server_json["priority"])


if __name__ == "__main__":
    unittest.main()