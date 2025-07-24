import unittest
import json

from conductor.client.http.models import CreateOrUpdateApplicationRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestCreateOrUpdateApplicationRequest(unittest.TestCase):
    """Test case for serialization and deserialization of CreateOrUpdateApplicationRequest model."""

    def setUp(self):
        """Set up test fixtures."""
        self.server_json_str = JsonTemplateResolver.get_json_string("CreateOrUpdateApplicationRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_deserialize_serialize(self):
        """Test deserialization from JSON and serialization back to JSON."""
        # 1. Deserialize server JSON into model object
        model = CreateOrUpdateApplicationRequest()
        model_dict = self.server_json

        # Set attributes from JSON
        if 'name' in model_dict:
            model.name = model_dict['name']

        # 2. Verify all fields are properly populated
        expected_name = self.server_json.get('name')
        self.assertEqual(model.name, expected_name,
                         f"Field 'name' was not properly deserialized. Expected: {expected_name}, Got: {model.name}")

        # 3. Serialize model back to JSON
        serialized_dict = model.to_dict()

        # 4. Verify the resulting JSON matches the original
        # Check field by field to make detailed assertions
        self.assertEqual(serialized_dict.get('name'), self.server_json.get('name'),
                         "Field 'name' did not match after serialization")

        # Verify overall dictionary equality
        self.assertEqual(serialized_dict, self.server_json,
                         "Serialized JSON doesn't match the original server JSON")


if __name__ == '__main__':
    unittest.main()