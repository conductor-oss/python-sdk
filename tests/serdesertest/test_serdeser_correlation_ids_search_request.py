import unittest
import json

from conductor.client.http.models.correlation_ids_search_request import CorrelationIdsSearchRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver

class TestCorrelationIdsSearchRequest(unittest.TestCase):
    """Test case for CorrelationIdsSearchRequest class."""

    def setUp(self):
        """Set up test fixtures."""
        # Load the JSON template for CorrelationIdsSearchRequest
        self.server_json_str = JsonTemplateResolver.get_json_string("CorrelationIdsSearchRequest")
        self.server_json = json.loads(self.server_json_str)

        # Convert camelCase to snake_case for initialization
        self.python_format_json = {}
        for key, value in self.server_json.items():
            # Use the attribute_map to find the Python property name
            python_key = next((k for k, v in CorrelationIdsSearchRequest.attribute_map.items() if v == key), key)
            self.python_format_json[python_key] = value

    def test_serdeser_correlation_ids_search_request(self):
        """Test serialization and deserialization of CorrelationIdsSearchRequest."""
        # 1. Server JSON can be correctly deserialized into SDK model object
        model_obj = CorrelationIdsSearchRequest(**self.python_format_json)

        # 2. All fields are properly populated during deserialization
        # Check correlation_ids (list[str])
        self.assertIsNotNone(model_obj.correlation_ids)
        self.assertIsInstance(model_obj.correlation_ids, list)
        for item in model_obj.correlation_ids:
            self.assertIsInstance(item, str)

        # Check workflow_names (list[str])
        self.assertIsNotNone(model_obj.workflow_names)
        self.assertIsInstance(model_obj.workflow_names, list)
        for item in model_obj.workflow_names:
            self.assertIsInstance(item, str)

        # 3. The SDK model can be serialized back to JSON
        serialized_dict = model_obj.to_dict()

        # 4. The resulting JSON matches the original
        # Convert serialized dict keys to camelCase for comparison
        json_dict = {}
        for attr, value in serialized_dict.items():
            if attr in model_obj.attribute_map:
                json_dict[model_obj.attribute_map[attr]] = value
            else:
                json_dict[attr] = value

        # Compare with original JSON
        self.assertEqual(self.server_json, json_dict)


if __name__ == '__main__':
    unittest.main()