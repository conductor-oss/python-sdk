import unittest
import json

from conductor.client.http.models import ConductorApplication
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver



class TestConductorApplicationSerialization(unittest.TestCase):
    """Test case for ConductorApplication serialization and deserialization."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Load JSON template from the resolver utility
        self.server_json_str = JsonTemplateResolver.get_json_string("ConductorApplication")
        self.server_json = json.loads(self.server_json_str)

    def test_serialization_deserialization(self):
        """Test that validates the serialization and deserialization of ConductorApplication model."""

        # Step 1: Deserialize server JSON into SDK model object
        # Create model object using constructor with fields from the JSON
        conductor_app = ConductorApplication(
            id=self.server_json.get('id'),
            name=self.server_json.get('name'),
            created_by=self.server_json.get('createdBy')
        )

        # Step 2: Verify all fields are correctly populated
        self.assertEqual(conductor_app.id, self.server_json.get('id'))
        self.assertEqual(conductor_app.name, self.server_json.get('name'))
        self.assertEqual(conductor_app.created_by, self.server_json.get('createdBy'))

        # Step 3: Serialize the model back to JSON
        serialized_json = conductor_app.to_dict()

        # Step 4: Verify the serialized JSON matches the original
        # Note: Field names in serialized_json will be in snake_case
        self.assertEqual(serialized_json.get('id'), self.server_json.get('id'))
        self.assertEqual(serialized_json.get('name'), self.server_json.get('name'))
        # Handle the camelCase to snake_case transformation
        self.assertEqual(serialized_json.get('created_by'), self.server_json.get('createdBy'))


if __name__ == '__main__':
    unittest.main()