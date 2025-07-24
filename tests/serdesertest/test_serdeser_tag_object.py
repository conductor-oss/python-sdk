import unittest
import json
from conductor.client.http.models.tag_object import TagObject, TypeEnum
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTagObjectSerDeser(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("Tag")
        self.server_json = json.loads(self.server_json_str)

    def test_tag_object_ser_deser(self):
        # 1. Deserialize JSON to model
        tag_object = TagObject(
            key=self.server_json.get("key"),
            type=self.server_json.get("type"),
            value=self.server_json.get("value")
        )

        # 2. Verify fields are properly populated
        self.assertEqual(tag_object.key, self.server_json.get("key"), "Key field not correctly deserialized")
        self.assertEqual(tag_object.type, self.server_json.get("type"), "Type field not correctly deserialized")
        self.assertEqual(tag_object.value, self.server_json.get("value"), "Value field not correctly deserialized")

        # Verify enum values if applicable
        if tag_object.type:
            self.assertIn(tag_object.type, [TypeEnum.METADATA.value, TypeEnum.RATE_LIMIT.value],
                          "Type field not correctly mapped to enum")

        # 3. Serialize model back to dictionary
        result_dict = tag_object.to_dict()

        # Convert keys from snake_case to camelCase if needed
        # For TagObject, the attribute_map shows no transformation is needed

        # 4. Verify serialized JSON matches original
        self.assertEqual(result_dict.get("key"), self.server_json.get("key"),
                         "Key field not correctly serialized")
        self.assertEqual(result_dict.get("type"), self.server_json.get("type"),
                         "Type field not correctly serialized")
        self.assertEqual(result_dict.get("value"), self.server_json.get("value"),
                         "Value field not correctly serialized")

        # Verify overall structure matches
        for key in self.server_json:
            self.assertIn(key, result_dict, f"Field {key} missing from serialized output")
            self.assertEqual(result_dict[key], self.server_json[key],
                             f"Field {key} has different value in serialized output")


if __name__ == '__main__':
    unittest.main()