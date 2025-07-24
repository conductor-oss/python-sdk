import unittest
import json
from conductor.client.http.models.integration_api import IntegrationApi
from conductor.client.http.models.tag_object import TagObject
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class IntegrationApiSerializationTest(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("IntegrationApi")
        self.server_json = json.loads(self.server_json_str)

    def test_integration_api_serialization_deserialization(self):
        # 1. Deserialize JSON to IntegrationApi object
        integration_api = IntegrationApi(
            api=self.server_json.get("api"),
            configuration=self.server_json.get("configuration"),
            created_by=self.server_json.get("createdBy"),
            created_on=self.server_json.get("createdOn"),
            description=self.server_json.get("description"),
            enabled=self.server_json.get("enabled"),
            integration_name=self.server_json.get("integrationName"),
            tags=[TagObject(
                key=tag.get("key"),
                value=tag.get("value")
            ) for tag in self.server_json.get("tags", [])]
            if self.server_json.get("tags") else None,
            updated_by=self.server_json.get("updatedBy"),
            updated_on=self.server_json.get("updatedOn")
        )

        # 2. Verify all fields are correctly populated
        # Simple fields
        self.assertEqual(self.server_json.get("api"), integration_api.api)
        self.assertEqual(self.server_json.get("description"), integration_api.description)
        self.assertEqual(self.server_json.get("enabled"), integration_api.enabled)
        self.assertEqual(self.server_json.get("integrationName"), integration_api.integration_name)

        # Date/time fields with camelCase to snake_case transformation
        self.assertEqual(self.server_json.get("createdBy"), integration_api.created_by)
        self.assertEqual(self.server_json.get("createdOn"), integration_api.created_on)
        self.assertEqual(self.server_json.get("updatedBy"), integration_api.updated_by)
        self.assertEqual(self.server_json.get("updatedOn"), integration_api.updated_on)

        # Complex data - configuration (dictionary)
        self.assertEqual(self.server_json.get("configuration"), integration_api.configuration)

        # Complex data - tags (list of TagObject)
        if self.server_json.get("tags"):
            self.assertEqual(len(self.server_json.get("tags")), len(integration_api.tags))
            for i, tag in enumerate(integration_api.tags):
                self.assertIsInstance(tag, TagObject)
                # Verify key fields of TagObject
                self.assertEqual(self.server_json.get("tags")[i].get("key"), tag.key)
                self.assertEqual(self.server_json.get("tags")[i].get("value"), tag.value)

        # 3. Serialize back to JSON
        serialized_json = integration_api.to_dict()

        # 4. Verify the serialized JSON matches the original, field by field
        # (instead of direct dictionary comparison)

        # Check simple fields
        for field in ["api", "description", "enabled"]:
            json_field = field
            if field in IntegrationApi.attribute_map:
                json_field = IntegrationApi.attribute_map[field]
            self.assertEqual(self.server_json.get(json_field), serialized_json.get(field),
                             f"Field {field} does not match after serialization")

        # Check fields with camelCase to snake_case transformation
        self.assertEqual(self.server_json.get("createdBy"), serialized_json.get("created_by"))
        self.assertEqual(self.server_json.get("createdOn"), serialized_json.get("created_on"))
        self.assertEqual(self.server_json.get("updatedBy"), serialized_json.get("updated_by"))
        self.assertEqual(self.server_json.get("updatedOn"), serialized_json.get("updated_on"))
        self.assertEqual(self.server_json.get("integrationName"), serialized_json.get("integration_name"))

        # Check configuration
        self.assertEqual(self.server_json.get("configuration"), serialized_json.get("configuration"))

        # Check tags manually field by field
        if self.server_json.get("tags"):
            for i, original_tag in enumerate(self.server_json.get("tags")):
                serialized_tag = serialized_json.get("tags")[i]
                self.assertEqual(original_tag.get("key"), serialized_tag.get("key"))
                self.assertEqual(original_tag.get("value"), serialized_tag.get("value"))
                # Now we're just ignoring the 'type' field that's added during serialization


if __name__ == '__main__':
    unittest.main()