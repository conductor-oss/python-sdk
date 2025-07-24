import unittest
import json
from conductor.client.http.models.target_ref import TargetRef, TargetType
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTargetRefSerDes(unittest.TestCase):
    def setUp(self):
        # Load JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("TargetRef")
        self.server_json = json.loads(self.server_json_str)

    def test_target_ref_serdes(self):
        # 1. Deserialize server JSON into SDK model object
        target_ref = TargetRef(
            type=self.server_json.get('type'),
            id=self.server_json.get('id')
        )

        # 2. Verify all fields are properly populated
        self.assertIsNotNone(target_ref.type)
        self.assertIsNotNone(target_ref.id)

        # Verify type is a valid enum value
        valid_types = ["WORKFLOW_DEF", "TASK_DEF", "APPLICATION",
                       "USER", "SECRET_NAME", "TAG", "DOMAIN"]
        self.assertIn(target_ref.type, valid_types)

        # 3. Serialize SDK model back to JSON
        sdk_json = target_ref.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(self.server_json.get('type'), sdk_json.get('type'))
        self.assertEqual(self.server_json.get('id'), sdk_json.get('id'))

        # Additional check: Complete round trip by deserializing again
        serialized_json = json.dumps(sdk_json)
        deserialized_json = json.loads(serialized_json)
        round_trip_obj = TargetRef(
            type=deserialized_json.get('type'),
            id=deserialized_json.get('id')
        )

        # Verify round trip object matches original
        self.assertEqual(target_ref.type, round_trip_obj.type)
        self.assertEqual(target_ref.id, round_trip_obj.id)

        # Verify equality method works correctly
        self.assertEqual(target_ref, round_trip_obj)


if __name__ == '__main__':
    unittest.main()