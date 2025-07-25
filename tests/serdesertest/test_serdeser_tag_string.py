import unittest
import json
from conductor.client.http.models.tag_string import TagString, TypeEnum
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTagStringSerialization(unittest.TestCase):

    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("Tag")
        self.server_json = json.loads(self.server_json_str)

    def test_tag_string_serde(self):
        """Test serialization and deserialization of TagString model"""

        # 1. Deserialize JSON into model object
        tag_string = TagString(
            key=self.server_json.get('key'),
            type=self.server_json.get('type'),
            value=self.server_json.get('value')
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get('key'), tag_string.key)
        self.assertEqual(self.server_json.get('type'), tag_string.type)
        self.assertEqual(self.server_json.get('value'), tag_string.value)

        # Specific enum validation if 'type' is present
        if self.server_json.get('type'):
            self.assertIn(tag_string.type, [TypeEnum.METADATA.value, TypeEnum.RATE_LIMIT.value])

        # 3. Serialize model back to JSON
        model_dict = tag_string.to_dict()
        model_json = json.dumps(model_dict)
        model_dict_reloaded = json.loads(model_json)

        # 4. Verify JSON matches the original
        # Note: Only compare fields that were in the original JSON
        for key in self.server_json:
            self.assertEqual(self.server_json[key], model_dict_reloaded[key])

        # Create another instance using the dict and verify equality
        reconstructed_tag = TagString(
            key=model_dict_reloaded.get('key'),
            type=model_dict_reloaded.get('type'),
            value=model_dict_reloaded.get('value')
        )

        self.assertEqual(tag_string, reconstructed_tag)


if __name__ == '__main__':
    unittest.main()