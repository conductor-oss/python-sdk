import unittest
import json
from conductor.client.http.models.subject_ref import SubjectRef
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestSubjectRefSerDes(unittest.TestCase):
    def setUp(self):
        # Load the JSON template for SubjectRef
        self.server_json_str = JsonTemplateResolver.get_json_string("SubjectRef")
        self.server_json = json.loads(self.server_json_str)

    def test_subject_ref_serdes(self):
        # 1. Deserialize server JSON into SDK model object
        subject_ref = SubjectRef(
            type=self.server_json.get("type"),
            id=self.server_json.get("id")
        )

        # 2. Verify all fields are properly populated during deserialization
        self.assertEqual(subject_ref.type, self.server_json.get("type"))
        self.assertEqual(subject_ref.id, self.server_json.get("id"))

        # Check type is a valid enum value
        self.assertIn(subject_ref.type, ["USER", "ROLE", "GROUP"])

        # 3. Serialize the SDK model back to JSON
        serialized_json = subject_ref.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(serialized_json["type"], self.server_json.get("type"))
        self.assertEqual(serialized_json["id"], self.server_json.get("id"))

        # Convert both to strings to compare the complete structure
        original_json_str = json.dumps(self.server_json, sort_keys=True)
        serialized_json_str = json.dumps(serialized_json, sort_keys=True)

        self.assertEqual(serialized_json_str, original_json_str)


if __name__ == "__main__":
    unittest.main()