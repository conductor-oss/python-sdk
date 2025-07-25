import unittest
from conductor.client.http.models.integration_def import IntegrationDef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestIntegrationDefSerialization(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("IntegrationDef")
        self.server_json = json.loads(self.server_json_str)

    def test_serialization_deserialization(self):
        # 1. Test deserialization from server JSON to SDK model
        integration_def = IntegrationDef(
            category=self.server_json['category'],
            category_label=self.server_json['categoryLabel'],
            configuration=self.server_json['configuration'],
            description=self.server_json['description'],
            enabled=self.server_json['enabled'],
            icon_name=self.server_json['iconName'],
            name=self.server_json['name'],
            tags=self.server_json['tags'],
            type=self.server_json['type']
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(integration_def.category, self.server_json['category'])
        self.assertEqual(integration_def.category_label, self.server_json['categoryLabel'])
        self.assertEqual(integration_def.configuration, self.server_json['configuration'])
        self.assertEqual(integration_def.description, self.server_json['description'])
        self.assertEqual(integration_def.enabled, self.server_json['enabled'])
        self.assertEqual(integration_def.icon_name, self.server_json['iconName'])
        self.assertEqual(integration_def.name, self.server_json['name'])
        self.assertEqual(integration_def.tags, self.server_json['tags'])
        self.assertEqual(integration_def.type, self.server_json['type'])

        # Check that enum values are valid for category
        self.assertIn(integration_def.category, ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"])

        # Check that complex structures are properly populated
        if integration_def.tags:
            self.assertIsInstance(integration_def.tags, list)

        if integration_def.configuration:
            self.assertIsInstance(integration_def.configuration, list)

        # 3. Test serialization back to JSON
        serialized_json = integration_def.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(serialized_json['category'], self.server_json['category'])
        self.assertEqual(serialized_json['category_label'], self.server_json['categoryLabel'])
        self.assertEqual(serialized_json['configuration'], self.server_json['configuration'])
        self.assertEqual(serialized_json['description'], self.server_json['description'])
        self.assertEqual(serialized_json['enabled'], self.server_json['enabled'])
        self.assertEqual(serialized_json['icon_name'], self.server_json['iconName'])
        self.assertEqual(serialized_json['name'], self.server_json['name'])
        self.assertEqual(serialized_json['tags'], self.server_json['tags'])
        self.assertEqual(serialized_json['type'], self.server_json['type'])


if __name__ == '__main__':
    unittest.main()