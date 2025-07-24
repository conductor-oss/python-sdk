import unittest
from conductor.client.http.models.group import Group
from conductor.client.http.models.role import Role
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestGroupSerDeSer(unittest.TestCase):
    def setUp(self):
        # Load JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("Group")
        self.server_json = json.loads(self.server_json_str)

    def test_group_serde(self):
        # 1. Deserialize server JSON into SDK model
        group = Group(
            id=self.server_json.get("id"),
            description=self.server_json.get("description"),
            roles=[Role(**role) for role in self.server_json.get("roles", [])],
            default_access=self.server_json.get("defaultAccess")
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("id"), group.id)
        self.assertEqual(self.server_json.get("description"), group.description)

        # Verify roles list
        if self.server_json.get("roles"):
            self.assertIsNotNone(group.roles)
            self.assertEqual(len(self.server_json.get("roles")), len(group.roles))
            for i, role in enumerate(group.roles):
                self.assertIsInstance(role, Role)
                # Check key properties of role objects
                self.assertEqual(self.server_json.get("roles")[i].get("name"), role.name)

        # Verify default_access map
        if self.server_json.get("defaultAccess"):
            self.assertIsNotNone(group.default_access)
            for key in self.server_json.get("defaultAccess").keys():
                self.assertIn(key, group.default_access)
                self.assertEqual(self.server_json.get("defaultAccess")[key], group.default_access[key])

        # 3. Serialize model back to dict
        result_dict = group.to_dict()

        # Transform dict keys from snake_case to camelCase for comparison
        camel_case_dict = {}
        for key, value in result_dict.items():
            json_key = Group.attribute_map.get(key, key)
            camel_case_dict[json_key] = value

        # 4. Verify the resulting dict matches the original
        for key in self.server_json.keys():
            if key == "roles":
                # For roles list, we need to compare their dict representations
                if self.server_json.get("roles"):
                    self.assertEqual(len(self.server_json.get("roles")), len(camel_case_dict.get("roles", [])))
                    for i, role_dict in enumerate(camel_case_dict.get("roles", [])):
                        for role_key in self.server_json.get("roles")[i].keys():
                            self.assertEqual(
                                self.server_json.get("roles")[i].get(role_key),
                                role_dict.get(
                                    Role.attribute_map.get(role_key.replace("camelCase", "snake_case"), role_key))
                            )
            elif key == "defaultAccess":
                # For maps, compare each key-value pair
                if self.server_json.get("defaultAccess"):
                    for map_key, map_value in self.server_json.get("defaultAccess").items():
                        self.assertIn(map_key, camel_case_dict.get("defaultAccess", {}))
                        self.assertEqual(map_value, camel_case_dict.get("defaultAccess", {}).get(map_key))
            else:
                # For simple fields, direct comparison
                self.assertEqual(self.server_json.get(key), camel_case_dict.get(key))


if __name__ == "__main__":
    unittest.main()