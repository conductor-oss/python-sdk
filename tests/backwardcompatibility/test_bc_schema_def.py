import pytest

from conductor.client.adapters.models import SchemaDef, SchemaType


@pytest.fixture
def valid_name():
    """Set up test fixture with valid name."""
    return "test_schema"


@pytest.fixture
def valid_version():
    """Set up test fixture with valid version."""
    return 1


@pytest.fixture
def valid_type():
    """Set up test fixture with valid type."""
    return SchemaType.JSON


@pytest.fixture
def valid_data():
    """Set up test fixture with valid data."""
    return {"field1": "value1", "field2": 123}


@pytest.fixture
def valid_external_ref():
    """Set up test fixture with valid external ref."""
    return "http://example.com/schema"


def test_constructor_with_no_args():
    """Test that constructor works with no arguments (all defaults)."""
    schema = SchemaDef()

    # Verify all fields are accessible and have expected default values
    assert schema.name is None
    assert schema.version == 1  # version defaults to 1, not None
    assert schema.type is None
    assert schema.data is None
    assert schema.external_ref is None


def test_constructor_with_all_args(
    valid_name, valid_version, valid_type, valid_data, valid_external_ref
):
    """Test constructor with all valid arguments."""
    schema = SchemaDef(
        name=valid_name,
        version=valid_version,
        type=valid_type,
        data=valid_data,
        external_ref=valid_external_ref,
    )

    # Verify all fields are set correctly
    assert schema.name == valid_name
    assert schema.version == valid_version
    assert schema.type == valid_type
    assert schema.data == valid_data
    assert schema.external_ref == valid_external_ref


def test_default_version_value():
    """Test that version defaults to 1 when not specified."""
    schema = SchemaDef()
    assert schema.version == 1

    # Test explicit None sets version to None
    schema = SchemaDef(version=None)
    assert schema.version is None


def test_constructor_with_partial_args(valid_name, valid_version):
    """Test constructor with partial arguments."""
    schema = SchemaDef(name=valid_name, version=valid_version)

    assert schema.name == valid_name
    assert schema.version == valid_version
    assert schema.type is None
    assert schema.data is None
    assert schema.external_ref is None


def test_field_existence():
    """Test that all expected fields exist and are accessible."""
    schema = SchemaDef()

    # Verify all expected fields exist as properties
    assert hasattr(schema, "name")
    assert hasattr(schema, "version")
    assert hasattr(schema, "type")
    assert hasattr(schema, "data")
    assert hasattr(schema, "external_ref")

    # Verify private attributes exist
    assert hasattr(schema, "_name")
    assert hasattr(schema, "_version")
    assert hasattr(schema, "_type")
    assert hasattr(schema, "_data")
    assert hasattr(schema, "_external_ref")


def test_property_getters_and_setters(
    valid_name, valid_version, valid_type, valid_data, valid_external_ref
):
    """Test that all properties have working getters and setters."""
    schema = SchemaDef()

    # Test name property
    schema.name = valid_name
    assert schema.name == valid_name

    # Test version property
    schema.version = valid_version
    assert schema.version == valid_version

    # Test type property
    schema.type = valid_type
    assert schema.type == valid_type

    # Test data property
    schema.data = valid_data
    assert schema.data == valid_data

    # Test external_ref property
    schema.external_ref = valid_external_ref
    assert schema.external_ref == valid_external_ref


def test_schema_type_enum_values():
    """Test that all expected SchemaType enum values exist and work."""
    # Test that all expected enum values exist
    assert hasattr(SchemaType, "JSON")
    assert hasattr(SchemaType, "AVRO")
    assert hasattr(SchemaType, "PROTOBUF")

    # Test enum values work with the model
    schema = SchemaDef()

    schema.type = SchemaType.JSON
    assert schema.type == SchemaType.JSON

    schema.type = SchemaType.AVRO
    assert schema.type == SchemaType.AVRO

    schema.type = SchemaType.PROTOBUF
    assert schema.type == SchemaType.PROTOBUF


def test_schema_type_enum_string_representation():
    """Test SchemaType enum string representation behavior."""
    assert str(SchemaType.JSON) == "JSON"
    assert str(SchemaType.AVRO) == "AVRO"
    assert str(SchemaType.PROTOBUF) == "PROTOBUF"


def test_field_type_constraints():
    """Test that field types work as expected."""
    schema = SchemaDef()

    # Test name accepts string
    schema.name = "test_string"
    assert isinstance(schema.name, str)

    # Test version accepts int
    schema.version = 42
    assert isinstance(schema.version, int)

    # Test type accepts SchemaType enum
    schema.type = SchemaType.JSON
    assert isinstance(schema.type, SchemaType)

    # Test data accepts dict
    test_dict = {"key": "value"}
    schema.data = test_dict
    assert isinstance(schema.data, dict)

    # Test external_ref accepts string
    schema.external_ref = "http://example.com"
    assert isinstance(schema.external_ref, str)


def test_to_dict_method(
    valid_name, valid_version, valid_type, valid_data, valid_external_ref
):
    """Test that to_dict method exists and works correctly."""
    schema = SchemaDef(
        name=valid_name,
        version=valid_version,
        type=valid_type,
        data=valid_data,
        external_ref=valid_external_ref,
    )

    result = schema.to_dict()

    # Verify to_dict returns a dictionary
    assert isinstance(result, dict)

    # Verify all original fields are in the result
    assert "name" in result
    assert "version" in result
    assert "type" in result
    assert "data" in result
    assert "external_ref" in result

    # Verify values are correct
    assert result["name"] == valid_name
    assert result["version"] == valid_version
    assert result["type"] == valid_type
    assert result["data"] == valid_data
    assert result["external_ref"] == valid_external_ref


def test_to_str_method(valid_name):
    """Test that to_str method exists and returns string."""
    schema = SchemaDef(name=valid_name)
    result = schema.to_str()

    assert isinstance(result, str)
    assert valid_name in result


def test_repr_method(valid_name):
    """Test that __repr__ method works."""
    schema = SchemaDef(name=valid_name)
    result = repr(schema)

    assert isinstance(result, str)
    assert valid_name in result


def test_equality_methods():
    """Test __eq__ and __ne__ methods."""
    schema1 = SchemaDef(name="test", version=1)
    schema2 = SchemaDef(name="test", version=1)
    schema3 = SchemaDef(name="different", version=1)

    # Test equality
    assert schema1 == schema2
    assert schema1 != schema3

    # Test inequality
    assert not (schema1 != schema2)
    assert schema1 != schema3

    # Test comparison with non-SchemaDef object
    assert schema1 != "not_a_schema"
    assert schema1 != "not_a_schema"


def test_swagger_types_attribute():
    """Test that all original swagger_types exist with correct types."""
    # Define the original expected types that must exist
    expected_types = {
        "name": "str",
        "version": "int",
        "type": "str",
        "data": "dict(str, object)",
        "external_ref": "str",
    }

    # Check that all expected fields exist with correct types
    for field, expected_type in expected_types.items():
        assert (
            field in SchemaDef.swagger_types
        ), f"Field '{field}' missing from swagger_types"
        assert (
            SchemaDef.swagger_types[field] == expected_type
        ), f"Field '{field}' has wrong type in swagger_types"

    # Verify swagger_types is a dictionary (structure check)
    assert isinstance(SchemaDef.swagger_types, dict)


def test_attribute_map_attribute():
    """Test that all original attribute mappings exist correctly."""
    # Define the original expected mappings that must exist
    expected_map = {
        "name": "name",
        "version": "version",
        "type": "type",
        "data": "data",
        "external_ref": "externalRef",
    }

    # Check that all expected mappings exist
    for field, expected_mapping in expected_map.items():
        assert (
            field in SchemaDef.attribute_map
        ), f"Field '{field}' missing from attribute_map"
        assert (
            SchemaDef.attribute_map[field] == expected_mapping
        ), f"Field '{field}' has wrong mapping in attribute_map"

    # Verify attribute_map is a dictionary (structure check)
    assert isinstance(SchemaDef.attribute_map, dict)


def test_discriminator_attribute():
    """Test that discriminator attribute exists and is accessible."""
    schema = SchemaDef()
    assert hasattr(schema, "discriminator")
    assert schema.discriminator is None


def test_none_value_handling():
    """Test that None values are handled correctly."""
    schema = SchemaDef()

    # All fields should accept None
    schema.name = None
    assert schema.name is None

    schema.version = None
    assert schema.version is None

    schema.type = None
    assert schema.type is None

    schema.data = None
    assert schema.data is None

    schema.external_ref = None
    assert schema.external_ref is None


def test_constructor_parameter_names():
    """Test that constructor accepts parameters with expected names."""
    # This ensures parameter names haven't changed
    schema = SchemaDef(
        name="test",
        version=2,
        type=SchemaType.AVRO,
        data={"test": "data"},
        external_ref="ref",
    )

    assert schema.name == "test"
    assert schema.version == 2
    assert schema.type == SchemaType.AVRO
    assert schema.data == {"test": "data"}
    assert schema.external_ref == "ref"


def test_backward_compatibility_core_functionality():
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
    assert schema.name == "compatibility_test"
    assert schema.version == 5
    assert schema.type == SchemaType.JSON
    assert schema.data == {"test": "data"}
    assert schema.external_ref == "http://test.com"

    # Test serialization still works
    result_dict = schema.to_dict()
    assert isinstance(result_dict, dict)

    # Test string representation still works
    result_str = schema.to_str()
    assert isinstance(result_str, str)


def test_original_api_surface_unchanged():
    """Test that the original API surface is completely unchanged."""
    # Create instance using original constructor signature
    schema = SchemaDef(
        name="api_test",
        version=1,
        type=SchemaType.AVRO,
        data={"original": "api"},
        external_ref="original_ref",
    )

    # Verify all original methods exist and work
    assert callable(getattr(schema, "to_dict", None))
    assert callable(getattr(schema, "to_str", None))

    # Verify original properties exist and work
    original_properties = ["name", "version", "type", "data", "external_ref"]
    for prop in original_properties:
        assert hasattr(schema, prop)
        # Test that we can get and set each property
        original_value = getattr(schema, prop)
        setattr(schema, prop, original_value)
        assert getattr(schema, prop) == original_value


def test_inheritance_does_not_break_original_behavior():
    """Test that inheritance doesn't affect original SchemaDef behavior."""
    # Create two instances with same data
    schema1 = SchemaDef(name="test", version=1, type=SchemaType.JSON)
    schema2 = SchemaDef(name="test", version=1, type=SchemaType.JSON)

    # Test equality still works
    assert schema1 == schema2

    # Test inequality works
    schema3 = SchemaDef(name="different", version=1, type=SchemaType.JSON)
    assert schema1 != schema3

    # Test that additional inherited fields don't interfere with core equality
    # (This tests that __eq__ method handles inheritance correctly)
    assert schema1.__dict__.keys() & {
        "_name",
        "_version",
        "_type",
        "_data",
        "_external_ref",
    } == schema2.__dict__.keys() & {
        "_name",
        "_version",
        "_type",
        "_data",
        "_external_ref",
    }
