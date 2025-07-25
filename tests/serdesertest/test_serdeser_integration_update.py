import unittest
import json
from conductor.client.http.models.integration_update import IntegrationUpdate
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestIntegrationUpdateSerDes(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("IntegrationUpdate")
        self.server_json = json.loads(self.server_json_str)

    def test_integration_update_serdes(self):
        # 1. Deserialize JSON into SDK model object
        integration_update = IntegrationUpdate(
            category=self.server_json.get("category"),
            configuration=self.server_json.get("configuration"),
            description=self.server_json.get("description"),
            enabled=self.server_json.get("enabled"),
            type=self.server_json.get("type")
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("category"), integration_update.category)
        self.assertEqual(self.server_json.get("configuration"), integration_update.configuration)
        self.assertEqual(self.server_json.get("description"), integration_update.description)
        self.assertEqual(self.server_json.get("enabled"), integration_update.enabled)
        self.assertEqual(self.server_json.get("type"), integration_update.type)

        # Specifically verify enum value for category is valid
        self.assertIn(integration_update.category, ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"])

        # 3. Serialize SDK model back to JSON
        model_dict = integration_update.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(self.server_json.get("category"), model_dict.get("category"))
        self.assertEqual(self.server_json.get("configuration"), model_dict.get("configuration"))
        self.assertEqual(self.server_json.get("description"), model_dict.get("description"))
        self.assertEqual(self.server_json.get("enabled"), model_dict.get("enabled"))
        self.assertEqual(self.server_json.get("type"), model_dict.get("type"))

        # Extra validation for complex fields
        if integration_update.configuration:
            # If configuration is a map, verify its structure is preserved
            self.assertEqual(
                self.server_json.get("configuration"),
                model_dict.get("configuration")
            )


if __name__ == "__main__":
    unittest.main()