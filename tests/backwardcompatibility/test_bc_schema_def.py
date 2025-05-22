import unittest
from conductor.client.http.models.schema_def import SchemaDef, SchemaType


class TestSchemaDefBackwardCompatibility(unittest.TestCase):
    """
    Backward compatibility tests for SchemaDef model.

    These tests ensure:
    - All existing fields remain accessible
    - Field types haven't changed
    - Constructor behavior is preserved
    - Existing enum values work
    - Validation rules remain consistent
    """

    def setUp(self):
        """Set up test fixtures with valid data."""
        self.valid_name = "test_schema"
        self.valid_version = 1
        self.valid_type = SchemaType.JSON
        self.valid_data = {"field1": "value1", "field2": 123}
        self.valid_external_ref = "http://example.com/schema"

    def test_constructor_with_no_args(self):
        """Test that constructor works with no arguments (all defaults)."""
        schema = SchemaDef()

        # Verify all fields are accessible and have expected default values
        self.assertIsNone(schema.name)
        self.assertEqual(schema.version, 1)  # version defaults to 1, not None
        self.assertIsNone(schema.type)
        self.assertIsNone(schema.data)
        self.assertIsNone(schema.external_ref)

    def test_constructor_with_all_args(self):
        """Test constructor with all valid arguments."""
        schema = SchemaDef(
            name=self.valid_name,
            version=self.valid_version,
            type=self.valid_type,
            data=self.valid_data,
            external_ref=self.valid_external_ref
        )

        # Verify all fields are set correctly
        self.assertEqual(schema.name, self.valid_name)
        self.assertEqual(schema.version, self.valid_version)
        self.assertEqual(schema.type, self.valid_type)
        self.assertEqual(schema.data, self.valid_data)
        self.assertEqual(schema.external_ref, self.valid_external_ref)

    def test_default_version_value(self):
        """Test that version defaults to 1 when not specified."""
        schema = SchemaDef()
        self.assertEqual(schema.version, 1)

        # Test explicit None sets version to None
        schema = SchemaDef(version=None)
        self.assertIsNone(schema.version)

    def test_constructor_with_partial_args(self):
        """Test constructor with partial arguments."""
        schema = SchemaDef(name=self.valid_name, version=self.valid_version)

        self.assertEqual(schema.name, self.valid_name)
        self.assertEqual(schema.version, self.valid_version)
        self.assertIsNone(schema.type)
        self.assertIsNone(schema.data)
        self.assertIsNone(schema.external_ref)

    def test_field_existence(self):
        """Test that all expected fields exist and are accessible."""
        schema = SchemaDef()

        # Verify all expected fields exist as properties
        self.assertTrue(hasattr(schema, 'name'))
        self.assertTrue(hasattr(schema, 'version'))
        self.assertTrue(hasattr(schema, 'type'))
        self.assertTrue(hasattr(schema, 'data'))
        self.assertTrue(hasattr(schema, 'external_ref'))

        # Verify private attributes exist
        self.assertTrue(hasattr(schema, '_name'))
        self.assertTrue(hasattr(schema, '_version'))
        self.assertTrue(hasattr(schema, '_type'))
        self.assertTrue(hasattr(schema, '_data'))
        self.assertTrue(hasattr(schema, '_external_ref'))

    def test_property_getters_and_setters(self):
        """Test that all properties have working getters and setters."""
        schema = SchemaDef()

        # Test name property
        schema.name = self.valid_name
        self.assertEqual(schema.name, self.valid_name)

        # Test version property
        schema.version = self.valid_version
        self.assertEqual(schema.version, self.valid_version)

        # Test type property
        schema.type = self.valid_type
        self.assertEqual(schema.type, self.valid_type)

        # Test data property
        schema.data = self.valid_data
        self.assertEqual(schema.data, self.valid_data)

        # Test external_ref property
        schema.external_ref = self.valid_external_ref
        self.assertEqual(schema.external_ref, self.valid_external_ref)

    def test_schema_type_enum_values(self):
        """Test that all expected SchemaType enum values exist and work."""
        # Test that all expected enum values exist
        self.assertTrue(hasattr(SchemaType, 'JSON'))
        self.assertTrue(hasattr(SchemaType, 'AVRO'))
        self.assertTrue(hasattr(SchemaType, 'PROTOBUF'))

        # Test enum values work with the model
        schema = SchemaDef()

        schema.type = SchemaType.JSON
        self.assertEqual(schema.type, SchemaType.JSON)

        schema.type = SchemaType.AVRO
        self.assertEqual(schema.type, SchemaType.AVRO)

        schema.type = SchemaType.PROTOBUF
        self.assertEqual(schema.type, SchemaType.PROTOBUF)

    def test_schema_type_enum_string_representation(self):
        """Test SchemaType enum string representation behavior."""
        self.assertEqual(str(SchemaType.JSON), "JSON")
        self.assertEqual(str(SchemaType.AVRO), "AVRO")
        self.assertEqual(str(SchemaType.PROTOBUF), "PROTOBUF")

    def test_field_type_constraints(self):
        """Test that field types work as expected."""
        schema = SchemaDef()

        # Test name accepts string
        schema.name = "test_string"
        self.assertIsInstance(schema.name, str)

        # Test version accepts int
        schema.version = 42
        self.assertIsInstance(schema.version, int)

        # Test type accepts SchemaType enum
        schema.type = SchemaType.JSON
        self.assertIsInstance(schema.type, SchemaType)

        # Test data accepts dict
        test_dict = {"key": "value"}
        schema.data = test_dict
        self.assertIsInstance(schema.data, dict)

        # Test external_ref accepts string
        schema.external_ref = "http://example.com"
        self.assertIsInstance(schema.external_ref, str)

    def test_to_dict_method(self):
        """Test that to_dict method exists and works correctly."""
        schema = SchemaDef(
            name=self.valid_name,
            version=self.valid_version,
            type=self.valid_type,
            data=self.valid_data,
            external_ref=self.valid_external_ref
        )

        result = schema.to_dict()

        # Verify to_dict returns a dictionary
        self.assertIsInstance(result, dict)

        # Verify all original fields are in the result
        self.assertIn('name', result)
        self.assertIn('version', result)
        self.assertIn('type', result)
        self.assertIn('data', result)
        self.assertIn('external_ref', result)

        # Verify values are correct
        self.assertEqual(result['name'], self.valid_name)
        self.assertEqual(result['version'], self.valid_version)
        self.assertEqual(result['type'], self.valid_type)
        self.assertEqual(result['data'], self.valid_data)
        self.assertEqual(result['external_ref'], self.valid_external_ref)

    def test_to_str_method(self):
        """Test that to_str method exists and returns string."""
        schema = SchemaDef(name=self.valid_name)
        result = schema.to_str()

        self.assertIsInstance(result, str)
        self.assertIn(self.valid_name, result)

    def test_repr_method(self):
        """Test that __repr__ method works."""
        schema = SchemaDef(name=self.valid_name)
        result = repr(schema)

        self.assertIsInstance(result, str)
        self.assertIn(self.valid_name, result)

    def test_equality_methods(self):
        """Test __eq__ and __ne__ methods."""
        schema1 = SchemaDef(name="test", version=1)
        schema2 = SchemaDef(name="test", version=1)
        schema3 = SchemaDef(name="different", version=1)

        # Test equality
        self.assertEqual(schema1, schema2)
        self.assertNotEqual(schema1, schema3)

        # Test inequality
        self.assertFalse(schema1 != schema2)
        self.assertTrue(schema1 != schema3)

        # Test comparison with non-SchemaDef object
        self.assertNotEqual(schema1, "not_a_schema")
        self.assertTrue(schema1 != "not_a_schema")

    def test_swagger_types_attribute(self):
        """Test that all original swagger_types exist with correct types."""
        # Define the original expected types that must exist
        expected_types = {
            'name': 'str',
            'version': 'int',
            'type': 'str',
            'data': 'dict(str, object)',
            'external_ref': 'str'
        }

        # Check that all expected fields exist with correct types
        for field, expected_type in expected_types.items():
            self.assertIn(field, SchemaDef.swagger_types,
                          f"Field '{field}' missing from swagger_types")
            self.assertEqual(SchemaDef.swagger_types[field], expected_type,
                             f"Field '{field}' has wrong type in swagger_types")

        # Verify swagger_types is a dictionary (structure check)
        self.assertIsInstance(SchemaDef.swagger_types, dict)

    def test_attribute_map_attribute(self):
        """Test that all original attribute mappings exist correctly."""
        # Define the original expected mappings that must exist
        expected_map = {
            'name': 'name',
            'version': 'version',
            'type': 'type',
            'data': 'data',
            'external_ref': 'externalRef'
        }

        # Check that all expected mappings exist
        for field, expected_mapping in expected_map.items():
            self.assertIn(field, SchemaDef.attribute_map,
                          f"Field '{field}' missing from attribute_map")
            self.assertEqual(SchemaDef.attribute_map[field], expected_mapping,
                             f"Field '{field}' has wrong mapping in attribute_map")

        # Verify attribute_map is a dictionary (structure check)
        self.assertIsInstance(SchemaDef.attribute_map, dict)

    def test_discriminator_attribute(self):
        """Test that discriminator attribute exists and is accessible."""
        schema = SchemaDef()
        self.assertTrue(hasattr(schema, 'discriminator'))
        self.assertIsNone(schema.discriminator)

    def test_none_value_handling(self):
        """Test that None values are handled correctly."""
        schema = SchemaDef()

        # All fields should accept None
        schema.name = None
        self.assertIsNone(schema.name)

        schema.version = None
        self.assertIsNone(schema.version)

        schema.type = None
        self.assertIsNone(schema.type)

        schema.data = None
        self.assertIsNone(schema.data)

        schema.external_ref = None
        self.assertIsNone(schema.external_ref)

    def test_constructor_parameter_names(self):
        """Test that constructor accepts parameters with expected names."""
        # This ensures parameter names haven't changed
        schema = SchemaDef(
            name="test",
            version=2,
            type=SchemaType.AVRO,
            data={"test": "data"},
            external_ref="ref"
        )

        self.assertEqual(schema.name, "test")
        self.assertEqual(schema.version, 2)
        self.assertEqual(schema.type, SchemaType.AVRO)
        self.assertEqual(schema.data, {"test": "data"})
        self.assertEqual(schema.external_ref, "ref")

    def test_backward_compatibility_core_functionality(self):
        """Test that core functionality remains unchanged."""
        # Test that the class can be instantiated and used exactly as before
        schema = SchemaDef()

        # Test property setting and getting
        schema.name = "compatibility_test"
        schema.version = 5
        schema.type = SchemaType.JSON
        schema.data = {"test": "data"}
        schema.external_ref = "http://test.com"

        # Test all properties return expected values
        self.assertEqual(schema.name, "compatibility_test")
        self.assertEqual(schema.version, 5)
        self.assertEqual(schema.type, SchemaType.JSON)
        self.assertEqual(schema.data, {"test": "data"})
        self.assertEqual(schema.external_ref, "http://test.com")

        # Test serialization still works
        result_dict = schema.to_dict()
        self.assertIsInstance(result_dict, dict)

        # Test string representation still works
        result_str = schema.to_str()
        self.assertIsInstance(result_str, str)

    def test_original_api_surface_unchanged(self):
        """Test that the original API surface is completely unchanged."""
        # Create instance using original constructor signature
        schema = SchemaDef(
            name="api_test",
            version=1,
            type=SchemaType.AVRO,
            data={"original": "api"},
            external_ref="original_ref"
        )

        # Verify all original methods exist and work
        self.assertTrue(callable(getattr(schema, 'to_dict', None)))
        self.assertTrue(callable(getattr(schema, 'to_str', None)))

        # Verify original properties exist and work
        original_properties = ['name', 'version', 'type', 'data', 'external_ref']
        for prop in original_properties:
            self.assertTrue(hasattr(schema, prop))
            # Test that we can get and set each property
            original_value = getattr(schema, prop)
            setattr(schema, prop, original_value)
            self.assertEqual(getattr(schema, prop), original_value)

    def test_inheritance_does_not_break_original_behavior(self):
        """Test that inheritance doesn't affect original SchemaDef behavior."""
        # Create two instances with same data
        schema1 = SchemaDef(name="test", version=1, type=SchemaType.JSON)
        schema2 = SchemaDef(name="test", version=1, type=SchemaType.JSON)

        # Test equality still works
        self.assertEqual(schema1, schema2)

        # Test inequality works
        schema3 = SchemaDef(name="different", version=1, type=SchemaType.JSON)
        self.assertNotEqual(schema1, schema3)

        # Test that additional inherited fields don't interfere with core equality
        # (This tests that __eq__ method handles inheritance correctly)
        self.assertEqual(schema1.__dict__.keys() & {'_name', '_version', '_type', '_data', '_external_ref'},
                         schema2.__dict__.keys() & {'_name', '_version', '_type', '_data', '_external_ref'})


if __name__ == '__main__':
    unittest.main()