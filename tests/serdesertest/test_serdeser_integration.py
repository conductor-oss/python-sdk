import json
import unittest
from conductor.client.http.models.integration import Integration
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class IntegrationSerdeserTest(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("Integration")
        self.server_json = json.loads(self.server_json_str)

    def test_integration_serdeser(self):
        # 1. Deserialize JSON into model object
        integration = Integration(
            category=self.server_json.get("category"),
            configuration=self.server_json.get("configuration"),
            created_by=self.server_json.get("createdBy"),
            created_on=self.server_json.get("createdOn"),
            description=self.server_json.get("description"),
            enabled=self.server_json.get("enabled"),
            models_count=self.server_json.get("modelsCount"),
            name=self.server_json.get("name"),
            tags=self.server_json.get("tags"),
            type=self.server_json.get("type"),
            updated_by=self.server_json.get("updatedBy"),
            updated_on=self.server_json.get("updatedOn"),
            apis=self.server_json.get("apis")
        )

        # 2. Verify all fields are correctly populated
        self.assertEqual(self.server_json.get("category"), integration.category)
        self.assertEqual(self.server_json.get("configuration"), integration.configuration)
        self.assertEqual(self.server_json.get("createdBy"), integration.created_by)
        self.assertEqual(self.server_json.get("createdOn"), integration.created_on)
        self.assertEqual(self.server_json.get("description"), integration.description)
        self.assertEqual(self.server_json.get("enabled"), integration.enabled)
        self.assertEqual(self.server_json.get("modelsCount"), integration.models_count)
        self.assertEqual(self.server_json.get("name"), integration.name)
        self.assertEqual(self.server_json.get("tags"), integration.tags)
        self.assertEqual(self.server_json.get("type"), integration.type)
        self.assertEqual(self.server_json.get("updatedBy"), integration.updated_by)
        self.assertEqual(self.server_json.get("updatedOn"), integration.updated_on)
        self.assertEqual(self.server_json.get("apis"), integration.apis)

        # Special check for enum values
        if integration.category is not None:
            self.assertIn(integration.category, ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"])

        # 3. Serialize model back to dict
        serialized_dict = integration.to_dict()

        # 4. Transform Python's snake_case back to camelCase for comparison
        transformed_dict = {}
        for snake_key, value in serialized_dict.items():
            camel_key = integration.attribute_map.get(snake_key, snake_key)
            transformed_dict[camel_key] = value

        # Compare original JSON with serialized and transformed dict
        for key, value in self.server_json.items():
            self.assertEqual(value, transformed_dict.get(key),
                             f"Value mismatch for key {key}: Original={value}, Serialized={transformed_dict.get(key)}")


if __name__ == '__main__':
    unittest.main()