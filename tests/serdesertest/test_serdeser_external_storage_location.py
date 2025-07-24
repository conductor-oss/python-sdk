import json
import unittest
from conductor.client.http.models.external_storage_location import ExternalStorageLocation
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestExternalStorageLocationSerDe(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("ExternalStorageLocation")
        self.server_json = json.loads(self.server_json_str)

    def test_external_storage_location_serde(self):
        # 1. Deserialize JSON to model object
        model = ExternalStorageLocation(
            uri=self.server_json.get('uri'),
            path=self.server_json.get('path')
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get('uri'), model.uri)
        self.assertEqual(self.server_json.get('path'), model.path)

        # 3. Serialize model back to dict
        model_dict = model.to_dict()

        # 4. Verify the serialized model matches the original JSON
        self.assertEqual(self.server_json.get('uri'), model_dict.get('uri'))
        self.assertEqual(self.server_json.get('path'), model_dict.get('path'))

        # Additional check for dictionary equivalence
        self.assertEqual(set(self.server_json.keys()), set(model_dict.keys()))


if __name__ == '__main__':
    unittest.main()