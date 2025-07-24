import unittest
import json
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver

# Import the classes being tested
from conductor.client.http.models.authorization_request import AuthorizationRequest


class TestAuthorizationRequestSerDes(unittest.TestCase):
    """
    Unit tests for serialization and deserialization of AuthorizationRequest model.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Load the template JSON for testing
        self.server_json_str = JsonTemplateResolver.get_json_string("AuthorizationRequest")
        self.server_json = json.loads(self.server_json_str)

    def test_serialization_deserialization(self):
        """Test complete serialization and deserialization process."""
        # Create the authorization request object directly from JSON
        # The model's __init__ should handle the nested objects
        auth_request = AuthorizationRequest(
            subject=self.server_json.get('subject'),
            target=self.server_json.get('target'),
            access=self.server_json.get('access')
        )

        # Verify model is properly initialized
        self.assertIsNotNone(auth_request, "Deserialized object should not be null")

        # Verify access list
        self.assertIsNotNone(auth_request.access, "Access list should not be null")
        self.assertTrue(all(access in ["CREATE", "READ", "UPDATE", "DELETE", "EXECUTE"]
                            for access in auth_request.access))

        # Verify subject and target are present
        self.assertIsNotNone(auth_request.subject, "Subject should not be null")
        self.assertIsNotNone(auth_request.target, "Target should not be null")

        # Serialize back to dictionary
        result_dict = auth_request.to_dict()

        # Verify structure matches the original
        self.assertEqual(
            set(self.server_json.keys()),
            set(result_dict.keys()),
            "Serialized JSON should have the same keys as the original"
        )

        # Convert both to JSON strings and compare (similar to objectMapper.readTree)
        original_json_normalized = json.dumps(self.server_json, sort_keys=True)
        result_json_normalized = json.dumps(result_dict, sort_keys=True)

        self.assertEqual(
            original_json_normalized,
            result_json_normalized,
            "Serialized JSON should match the original SERVER_JSON"
        )


if __name__ == '__main__':
    unittest.main()