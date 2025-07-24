import json
import unittest
from typing import List

from conductor.client.http.models.role import Role
from conductor.client.http.models.permission import Permission
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestRoleSerialization(unittest.TestCase):
    """Test serialization and deserialization of the Role model."""

    def setUp(self):
        """Set up test fixtures."""
        self.server_json_str = JsonTemplateResolver.get_json_string("Role")
        self.server_json = json.loads(self.server_json_str)

    def test_role_serialization_deserialization(self):
        """Test that Role objects can be properly serialized and deserialized."""
        # 1. Test deserialization from server JSON to SDK model
        role_obj = Role(
            name=self.server_json.get('name'),
            permissions=[Permission(**perm) if isinstance(perm, dict) else perm
                         for perm in self.server_json.get('permissions', [])]
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get('name'), role_obj.name)

        # Verify permissions list if present
        if 'permissions' in self.server_json:
            self.assertIsNotNone(role_obj.permissions)
            self.assertEqual(len(self.server_json['permissions']), len(role_obj.permissions))

            # Check first permission in list if available
            if self.server_json['permissions'] and role_obj.permissions:
                # This would need to be adapted based on the Permission class structure
                if hasattr(role_obj.permissions[0], 'to_dict'):
                    permission_dict = role_obj.permissions[0].to_dict()
                    for key, value in self.server_json['permissions'][0].items():
                        # Convert JSON camelCase to Python snake_case if needed
                        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
                        if snake_key in permission_dict:
                            self.assertEqual(value, permission_dict[snake_key])

        # 3. Test serialization back to JSON
        serialized_json = role_obj.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(self.server_json.get('name'), serialized_json.get('name'))

        # Compare permissions lists if present
        if 'permissions' in self.server_json and 'permissions' in serialized_json:
            self.assertEqual(len(self.server_json['permissions']), len(serialized_json['permissions']))

            # Deeper comparison would depend on Permission class structure
            if self.server_json['permissions'] and serialized_json['permissions']:
                # This assumes Permission has a similar structure and serialization logic
                for i, (orig_perm, serial_perm) in enumerate(
                        zip(self.server_json['permissions'], serialized_json['permissions'])
                ):
                    if isinstance(orig_perm, dict) and isinstance(serial_perm, dict):
                        for key in orig_perm:
                            snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
                            camel_key = ''.join(
                                [word.capitalize() if i > 0 else word for i, word in enumerate(snake_key.split('_'))]
                            )
                            self.assertTrue(
                                key in serial_perm or camel_key in serial_perm,
                                f"Key {key} or {camel_key} missing from serialized permission"
                            )


if __name__ == '__main__':
    unittest.main()