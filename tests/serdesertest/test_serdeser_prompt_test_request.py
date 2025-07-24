import unittest
import json
from conductor.client.http.models.prompt_test_request import PromptTemplateTestRequest
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestPromptTemplateTestRequestSerDes(unittest.TestCase):
    """Test case for serialization and deserialization of PromptTemplateTestRequest."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.server_json_str = JsonTemplateResolver.get_json_string("PromptTemplateTestRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_prompt_template_test_request_serde(self):
        """Test PromptTemplateTestRequest serialization/deserialization."""
        # 1. Deserialize JSON to model object
        model_obj = PromptTemplateTestRequest(
            llm_provider=self.server_json.get('llmProvider'),
            model=self.server_json.get('model'),
            prompt=self.server_json.get('prompt'),
            prompt_variables=self.server_json.get('promptVariables'),
            stop_words=self.server_json.get('stopWords'),
            temperature=self.server_json.get('temperature'),
            top_p=self.server_json.get('topP')
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get('llmProvider'), model_obj.llm_provider)
        self.assertEqual(self.server_json.get('model'), model_obj.model)
        self.assertEqual(self.server_json.get('prompt'), model_obj.prompt)

        # Check complex data structures
        self.assertEqual(self.server_json.get('promptVariables'), model_obj.prompt_variables)
        self.assertEqual(self.server_json.get('stopWords'), model_obj.stop_words)

        # Check numeric values
        self.assertEqual(self.server_json.get('temperature'), model_obj.temperature)
        self.assertEqual(self.server_json.get('topP'), model_obj.top_p)

        # 3. Serialize model back to JSON
        model_json = model_obj.to_dict()

        # Convert snake_case keys back to camelCase for comparison
        converted_model_json = {}
        for key, value in model_json.items():
            # Use the attribute_map to convert back to camelCase
            camel_key = model_obj.attribute_map.get(key, key)
            converted_model_json[camel_key] = value

        # 4. Verify that the resulting JSON matches the original
        for key, value in self.server_json.items():
            self.assertIn(key, converted_model_json)
            if isinstance(value, dict):
                self.assertEqual(value, converted_model_json[key])
            elif isinstance(value, list):
                self.assertEqual(value, converted_model_json[key])
            else:
                self.assertEqual(value, converted_model_json[key])


if __name__ == '__main__':
    unittest.main()