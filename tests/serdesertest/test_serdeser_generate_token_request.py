import unittest
import json
from conductor.client.http.models.generate_token_request import GenerateTokenRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestGenerateTokenRequestSerDes(unittest.TestCase):
    def setUp(self):
        # Load the JSON template using JsonTemplateResolver
        self.server_json_str = JsonTemplateResolver.get_json_string("GenerateTokenRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_generate_token_request_ser_des(self):
        """Test serialization and deserialization of GenerateTokenRequest"""

        # 1. Deserialize JSON into model object
        model_obj = GenerateTokenRequest(
            key_id=self.server_json['keyId'],
            key_secret=self.server_json['keySecret']
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(model_obj.key_id, self.server_json['keyId'])
        self.assertEqual(model_obj.key_secret, self.server_json['keySecret'])

        # 3. Serialize model back to JSON
        model_json = model_obj.to_dict()

        # Convert snake_case back to camelCase for comparison
        serialized_json = {
            'keyId': model_json['key_id'],
            'keySecret': model_json['key_secret']
        }

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(serialized_json['keyId'], self.server_json['keyId'])
        self.assertEqual(serialized_json['keySecret'], self.server_json['keySecret'])

        # Verify the object equality methods
        duplicate_obj = GenerateTokenRequest(
            key_id=self.server_json['keyId'],
            key_secret=self.server_json['keySecret']
        )

        self.assertEqual(model_obj, duplicate_obj)
        self.assertNotEqual(model_obj, GenerateTokenRequest(key_id="different", key_secret="values"))


if __name__ == '__main__':
    unittest.main()