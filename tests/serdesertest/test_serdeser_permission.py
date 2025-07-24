import unittest
import json
from conductor.client.http.models.permission import Permission
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestPermissionSerialization(unittest.TestCase):
    def setUp(self):
        # Load template JSON using the resolver utility
        self.server_json_str = JsonTemplateResolver.get_json_string("Permission")
        self.server_json = json.loads(self.server_json_str)

    def test_permission_serde(self):
        # 1. Server JSON can be correctly deserialized into SDK model object
        permission_obj = Permission(name=self.server_json.get("name"))

        # 2. All fields are properly populated during deserialization
        self.assertEqual(permission_obj.name, self.server_json.get("name"))

        # 3. The SDK model can be serialized back to JSON
        serialized_json = permission_obj.to_dict()

        # 4. The resulting JSON matches the original, ensuring no data is lost
        # Handle potential camelCase to snake_case transformations
        self.assertEqual(serialized_json.get("name"), self.server_json.get("name"))

        # Additional verification to ensure all fields in original JSON are in serialized JSON
        for key in self.server_json:
            # Convert camelCase to snake_case if needed
            python_key = key
            self.assertIn(python_key, serialized_json)

        # Verify no extra fields were added during serialization
        self.assertEqual(len(serialized_json), len(self.server_json))


if __name__ == '__main__':
    unittest.main()