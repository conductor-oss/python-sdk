import unittest
import json
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestUpsertGroupRequest(unittest.TestCase):
    def setUp(self):
        # Load the JSON template using JsonTemplateResolver
        self.server_json_str = JsonTemplateResolver.get_json_string("UpsertGroupRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_serde_upsert_group_request(self):
        # 1. Deserialize JSON into model object
        model_obj = UpsertGroupRequest(
            description=self.server_json.get("description"),
            roles=self.server_json.get("roles"),
            default_access=self.server_json.get("defaultAccess")
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(model_obj.description, self.server_json.get("description"))

        # Check roles list is populated correctly
        self.assertIsNotNone(model_obj.roles)
        self.assertEqual(len(model_obj.roles), len(self.server_json.get("roles", [])))
        for role in model_obj.roles:
            self.assertIn(role, ["ADMIN", "USER", "WORKER", "METADATA_MANAGER", "WORKFLOW_MANAGER"])

        # Check default_access map is populated correctly
        self.assertIsNotNone(model_obj.default_access)
        self.assertEqual(len(model_obj.default_access), len(self.server_json.get("defaultAccess", {})))

        # Verify all keys in default_access are valid
        for key in model_obj.default_access:
            self.assertIn(key, ["WORKFLOW_DEF", "TASK_DEF"])

        # 3. Serialize the model back to dict/JSON
        model_dict = model_obj.to_dict()

        # 4. Verify the serialized JSON matches the original
        # Check that snake_case in Python is properly converted to camelCase in JSON
        self.assertEqual(model_dict["default_access"], self.server_json.get("defaultAccess"))
        self.assertEqual(model_dict["description"], self.server_json.get("description"))
        self.assertEqual(model_dict["roles"], self.server_json.get("roles"))

        # Additional validation for complex nested structures
        if "defaultAccess" in self.server_json:
            for target_type, access_list in self.server_json["defaultAccess"].items():
                self.assertIn(target_type, model_dict["default_access"])
                self.assertEqual(access_list, model_dict["default_access"][target_type])


if __name__ == '__main__':
    unittest.main()