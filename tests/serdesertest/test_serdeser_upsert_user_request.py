import unittest
from conductor.client.http.models.upsert_user_request import UpsertUserRequest, RolesEnum
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestUpsertUserRequestSerdeSer(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("UpsertUserRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_upsert_user_request_serdeser(self):
        # 1. Deserialize JSON into model object
        model_obj = UpsertUserRequest(
            name=self.server_json.get('name'),
            roles=self.server_json.get('roles'),
            groups=self.server_json.get('groups')
        )

        # 2. Verify all fields are properly populated
        # Verify name field
        self.assertEqual(self.server_json.get('name'), model_obj.name)

        # Verify roles list and enum values
        roles = self.server_json.get('roles')
        if roles:
            self.assertEqual(len(roles), len(model_obj.roles))
            for role in model_obj.roles:
                self.assertIn(role, [e.value for e in RolesEnum])
                self.assertIn(role, roles)

        # Verify groups list
        groups = self.server_json.get('groups')
        if groups:
            self.assertEqual(len(groups), len(model_obj.groups))
            for i, group in enumerate(groups):
                self.assertEqual(group, model_obj.groups[i])

        # 3. Serialize model back to JSON
        model_dict = model_obj.to_dict()
        model_json = json.dumps(model_dict)

        # 4. Verify the resulting JSON matches the original
        # Convert both JSONs to dictionaries for comparison
        deserialized_json = json.loads(model_json)

        # Compare key by key to handle any field name transformations
        for key in self.server_json:
            self.assertIn(key, deserialized_json)
            if isinstance(self.server_json[key], list):
                self.assertEqual(len(self.server_json[key]), len(deserialized_json[key]))
                for i, item in enumerate(self.server_json[key]):
                    self.assertEqual(item, deserialized_json[key][i])
            else:
                self.assertEqual(self.server_json[key], deserialized_json[key])


if __name__ == '__main__':
    unittest.main()