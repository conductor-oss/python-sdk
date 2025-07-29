import pytest

from conductor.client.http.models.tag_string import TagString


@pytest.fixture
def valid_type_values():
    """Set up test fixture with valid enum values."""
    return ["METADATA", "RATE_LIMIT"]


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (current behavior)."""
    tag = TagString()
    assert tag.key is None
    assert tag.type is None
    assert tag.value is None


def test_constructor_with_all_parameters():
    """Test constructor with all valid parameters."""
    tag = TagString(key="test_key", type="METADATA", value="test_value")
    assert tag.key == "test_key"
    assert tag.type == "METADATA"
    assert tag.value == "test_value"


def test_constructor_with_partial_parameters():
    """Test constructor with some parameters."""
    tag = TagString(key="test_key")
    assert tag.key == "test_key"
    assert tag.type is None
    assert tag.value is None


def test_required_fields_exist():
    """Test that all expected fields exist and are accessible."""
    tag = TagString()

    # Test field existence via property access
    assert hasattr(tag, "key")
    assert hasattr(tag, "type")
    assert hasattr(tag, "value")

    # Test that properties can be accessed without error
    _ = tag.key
    _ = tag.type
    _ = tag.value


def test_field_types_unchanged():
    """Test that field types are still strings as expected."""
    tag = TagString(key="test", type="METADATA", value="test_value")

    assert isinstance(tag.key, str)
    assert isinstance(tag.type, str)
    assert isinstance(tag.value, str)


def test_key_property_behavior():
    """Test key property getter/setter behavior."""
    tag = TagString()

    # Test setter
    tag.key = "test_key"
    assert tag.key == "test_key"

    # Test that None is allowed
    tag.key = None
    assert tag.key is None


def test_value_property_behavior():
    """Test value property getter/setter behavior."""
    tag = TagString()

    # Test setter
    tag.value = "test_value"
    assert tag.value == "test_value"

    # Test that None is allowed
    tag.value = None
    assert tag.value is None


def test_type_property_validation_existing_values(valid_type_values):
    """Test that existing enum values for type are still accepted."""
    tag = TagString()

    # Test all current valid values
    for valid_type in valid_type_values:
        tag.type = valid_type
        assert tag.type == valid_type


def test_type_property_validation_invalid_values(valid_type_values):
    """Test that invalid type values still raise ValueError."""
    tag = TagString()

    invalid_values = ["INVALID", "metadata", "rate_limit", "", "OTHER", None]

    for invalid_type in invalid_values:
        with pytest.raises(ValueError, match="Invalid") as excinfo:
            tag.type = invalid_type

        # Verify error message format hasn't changed
        error_msg = str(excinfo.value)
        assert "Invalid value for `type`" in error_msg
        assert str(invalid_type) in error_msg
        assert str(valid_type_values) in error_msg


def test_type_constructor_none_behavior():
    """Test that type can be None when set via constructor but not via setter."""
    # Constructor allows None (no validation during __init__)
    tag = TagString(type=None)
    assert tag.type is None

    # But setter validates and rejects None
    tag2 = TagString()
    with pytest.raises(ValueError, match="Invalid"):
        tag2.type = None


def test_swagger_types_structure():
    """Test that swagger_types class attribute structure is unchanged."""
    expected_swagger_types = {"key": "str", "type": "str", "value": "str"}

    assert TagString.swagger_types == expected_swagger_types


def test_attribute_map_structure():
    """Test that attribute_map class attribute structure is unchanged."""
    expected_attribute_map = {"key": "key", "type": "type", "value": "value"}

    assert TagString.attribute_map == expected_attribute_map


def test_to_dict_method_exists_and_works():
    """Test that to_dict method exists and returns expected structure."""
    tag = TagString(key="test_key", type="METADATA", value="test_value")
    result = tag.to_dict()

    assert isinstance(result, dict)
    assert result["key"] == "test_key"
    assert result["type"] == "METADATA"
    assert result["value"] == "test_value"


def test_to_dict_with_none_values():
    """Test to_dict behavior with None values."""
    tag = TagString()
    result = tag.to_dict()

    assert isinstance(result, dict)
    assert "key" in result
    assert "type" in result
    assert "value" in result


def test_to_str_method_exists():
    """Test that to_str method exists and returns string."""
    tag = TagString(key="test", type="METADATA", value="test_value")
    result = tag.to_str()

    assert isinstance(result, str)


def test_repr_method_exists():
    """Test that __repr__ method works."""
    tag = TagString(key="test", type="METADATA", value="test_value")
    result = repr(tag)

    assert isinstance(result, str)


def test_equality_comparison():
    """Test that equality comparison works as expected."""
    tag1 = TagString(key="test", type="METADATA", value="value")
    tag2 = TagString(key="test", type="METADATA", value="value")
    tag3 = TagString(key="different", type="METADATA", value="value")

    assert tag1 == tag2
    assert tag1 != tag3
    assert tag1 != "not_a_tag_string"


def test_inequality_comparison():
    """Test that inequality comparison works."""
    tag1 = TagString(key="test", type="METADATA", value="value")
    tag2 = TagString(key="different", type="METADATA", value="value")

    assert tag1 != tag2


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists (swagger generated code)."""
    tag = TagString()
    assert hasattr(tag, "discriminator")
    assert tag.discriminator is None


def test_private_attributes_exist():
    """Test that private attributes used by properties exist."""
    tag = TagString()

    # These are implementation details but important for backward compatibility
    assert hasattr(tag, "_key")
    assert hasattr(tag, "_type")
    assert hasattr(tag, "_value")
