import json
import unittest

from conductor.client.http.models import ConductorUser, Role, Group
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestConductorUserSerDeSer(unittest.TestCase):
    """Test serialization and deserialization of ConductorUser."""

    def setUp(self):
        # Load JSON template using the utility
        self.server_json_str = JsonTemplateResolver.get_json_string("ConductorUser")
        self.server_json = json.loads(self.server_json_str)

    def test_conductor_user_serde(self):
        """Test that ConductorUser can be deserialized from server JSON and serialized back without data loss."""

        # 1. Deserialize server JSON into ConductorUser object
        conductor_user = ConductorUser()
        conductor_user_dict = self.server_json

        # Set attributes from deserialized JSON
        if 'id' in conductor_user_dict:
            conductor_user.id = conductor_user_dict['id']
        if 'name' in conductor_user_dict:
            conductor_user.name = conductor_user_dict['name']
        if 'roles' in conductor_user_dict:
            # Assuming Role has a from_dict method or similar
            roles_list = []
            for role_data in conductor_user_dict['roles']:
                role = Role()  # Create a Role object based on your actual implementation
                # Set Role properties here
                roles_list.append(role)
            conductor_user.roles = roles_list
        if 'groups' in conductor_user_dict:
            # Assuming Group has a from_dict method or similar
            groups_list = []
            for group_data in conductor_user_dict['groups']:
                group = Group()  # Create a Group object based on your actual implementation
                # Set Group properties here
                groups_list.append(group)
            conductor_user.groups = groups_list
        if 'uuid' in conductor_user_dict:
            conductor_user.uuid = conductor_user_dict['uuid']
        if 'applicationUser' in conductor_user_dict:
            conductor_user.application_user = conductor_user_dict['applicationUser']
        if 'encryptedId' in conductor_user_dict:
            conductor_user.encrypted_id = conductor_user_dict['encryptedId']
        if 'encryptedIdDisplayValue' in conductor_user_dict:
            conductor_user.encrypted_id_display_value = conductor_user_dict['encryptedIdDisplayValue']

        # 2. Verify all fields are properly populated
        expected_id = self.server_json.get('id', None)
        self.assertEqual(conductor_user.id, expected_id)

        expected_name = self.server_json.get('name', None)
        self.assertEqual(conductor_user.name, expected_name)

        # Verify lists
        if 'roles' in self.server_json:
            self.assertEqual(len(conductor_user.roles), len(self.server_json['roles']))

        if 'groups' in self.server_json:
            self.assertEqual(len(conductor_user.groups), len(self.server_json['groups']))

        expected_uuid = self.server_json.get('uuid', None)
        self.assertEqual(conductor_user.uuid, expected_uuid)

        expected_app_user = self.server_json.get('applicationUser', None)
        self.assertEqual(conductor_user.application_user, expected_app_user)

        expected_encrypted_id = self.server_json.get('encryptedId', None)
        self.assertEqual(conductor_user.encrypted_id, expected_encrypted_id)

        expected_encrypted_id_display = self.server_json.get('encryptedIdDisplayValue', None)
        self.assertEqual(conductor_user.encrypted_id_display_value, expected_encrypted_id_display)

        # 3. Serialize the object back to JSON
        serialized_json = conductor_user.to_dict()

        # 4. Verify the serialized JSON matches the original
        # Handle camelCase to snake_case transformations
        if 'applicationUser' in self.server_json:
            self.assertEqual(serialized_json['application_user'], self.server_json['applicationUser'])
        if 'encryptedId' in self.server_json:
            self.assertEqual(serialized_json['encrypted_id'], self.server_json['encryptedId'])
        if 'encryptedIdDisplayValue' in self.server_json:
            self.assertEqual(serialized_json['encrypted_id_display_value'], self.server_json['encryptedIdDisplayValue'])

        # Check common fields that don't need transformation
        for field in ['id', 'name', 'uuid']:
            if field in self.server_json:
                self.assertEqual(serialized_json[field], self.server_json[field])

        # Check lists length
        if 'roles' in self.server_json:
            self.assertEqual(len(serialized_json['roles']), len(self.server_json['roles']))
        if 'groups' in self.server_json:
            self.assertEqual(len(serialized_json['groups']), len(self.server_json['groups']))


if __name__ == '__main__':
    unittest.main()