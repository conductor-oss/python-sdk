import json

import pytest

# Import the model - adjust path as needed
from conductor.client.http.models.tag_object import TagObject


@pytest.fixture
def valid_metadata_tag():
    """Set up test fixture with valid metadata tag data."""
    return {
        "key": "environment",
        "type": "METADATA",
        "value": "production",
    }


@pytest.fixture
def valid_rate_limit_tag():
    """Set up test fixture with valid rate limit tag data."""
    return {
        "key": "max_requests",
        "type": "RATE_LIMIT",
        "value": 1000,
    }


def test_constructor_all_fields_none_should_work():
    """Test that constructor works with all None values (current behavior)."""
    tag = TagObject()
    assert tag.key is None
    assert tag.type is None
    assert tag.value is None


def test_constructor_with_valid_parameters():
    """Test constructor with valid parameters."""
    tag = TagObject(key="test_key", type="METADATA", value="test_value")
    assert tag.key == "test_key"
    assert tag.type == "METADATA"
    assert tag.value == "test_value"


def test_constructor_supports_all_existing_parameters():
    """Verify all existing constructor parameters are still supported."""
    # Test that constructor accepts these specific parameter names
    tag = TagObject(key="k", type="METADATA", value="v")
    assert tag is not None

    # Test each parameter individually
    tag1 = TagObject(key="test")
    assert tag1.key == "test"

    tag2 = TagObject(type="RATE_LIMIT")
    assert tag2.type == "RATE_LIMIT"

    tag3 = TagObject(value=42)
    assert tag3.value == 42


# Field Existence Tests
def test_key_field_exists():
    """Verify 'key' field exists and is accessible."""
    tag = TagObject()
    assert hasattr(tag, "key")
    assert hasattr(tag, "_key")
    # Test getter
    _ = tag.key
    # Test setter
    tag.key = "test"
    assert tag.key == "test"


def test_type_field_exists():
    """Verify 'type' field exists and is accessible."""
    tag = TagObject()
    assert hasattr(tag, "type")
    assert hasattr(tag, "_type")
    # Test getter
    _ = tag.type
    # Test setter with valid value
    tag.type = "METADATA"
    assert tag.type == "METADATA"


def test_value_field_exists():
    """Verify 'value' field exists and is accessible."""
    tag = TagObject()
    assert hasattr(tag, "value")
    assert hasattr(tag, "_value")
    # Test getter
    _ = tag.value
    # Test setter
    tag.value = "test_value"
    assert tag.value == "test_value"


# Type Validation Tests
def test_key_accepts_string_type():
    """Verify key field accepts string values."""
    tag = TagObject()
    tag.key = "string_value"
    assert tag.key == "string_value"
    assert isinstance(tag.key, str)


def test_key_accepts_none():
    """Verify key field accepts None."""
    tag = TagObject()
    tag.key = None
    assert tag.key is None


def test_value_accepts_various_types():
    """Verify value field accepts various object types."""
    tag = TagObject()

    # String
    tag.value = "string"
    assert tag.value == "string"

    # Integer
    tag.value = 123
    assert tag.value == 123

    # Dictionary
    tag.value = {"nested": "dict"}
    assert tag.value == {"nested": "dict"}

    # List
    tag.value = [1, 2, 3]
    assert tag.value == [1, 2, 3]

    # None
    tag.value = None
    assert tag.value is None


# Enum Validation Tests
def test_type_accepts_metadata_enum_value():
    """Verify 'METADATA' enum value is still supported."""
    tag = TagObject()
    tag.type = "METADATA"
    assert tag.type == "METADATA"


def test_type_accepts_rate_limit_enum_value():
    """Verify 'RATE_LIMIT' enum value is still supported."""
    tag = TagObject()
    tag.type = "RATE_LIMIT"
    assert tag.type == "RATE_LIMIT"


def test_type_rejects_invalid_enum_values():
    """Verify type field validation still works for invalid values."""
    tag = TagObject()
    with pytest.raises(ValueError, match="Invalid") as excinfo:
        tag.type = "INVALID_TYPE"

    error_msg = str(excinfo.value)
    assert "Invalid value for `type`" in error_msg
    assert "INVALID_TYPE" in error_msg
    assert "METADATA" in error_msg
    assert "RATE_LIMIT" in error_msg


def test_type_setter_rejects_none():
    """Verify type setter rejects None (current behavior)."""
    tag = TagObject()
    with pytest.raises(ValueError, match="Invalid") as excinfo:
        tag.type = None

    error_msg = str(excinfo.value)
    assert "Invalid value for `type`" in error_msg
    assert "None" in error_msg


def test_type_none_allowed_via_constructor_only():
    """Verify None is allowed via constructor but not setter."""
    # Constructor allows None
    tag = TagObject(type=None)
    assert tag.type is None

    # But setter rejects None
    tag2 = TagObject()
    with pytest.raises(ValueError, match="Invalid"):
        tag2.type = None


# Method Existence Tests
def test_to_dict_method_exists():
    """Verify to_dict method exists and works."""
    tag = TagObject(key="test", type="METADATA", value="val")
    assert hasattr(tag, "to_dict")
    result = tag.to_dict()
    assert isinstance(result, dict)
    assert result["key"] == "test"
    assert result["type"] == "METADATA"
    assert result["value"] == "val"


def test_to_str_method_exists():
    """Verify to_str method exists and works."""
    tag = TagObject(key="test", type="METADATA", value="val")
    assert hasattr(tag, "to_str")
    result = tag.to_str()
    assert isinstance(result, str)


def test_repr_method_exists():
    """Verify __repr__ method exists and works."""
    tag = TagObject(key="test", type="METADATA", value="val")
    result = repr(tag)
    assert isinstance(result, str)


def test_eq_method_exists():
    """Verify __eq__ method exists and works."""
    tag1 = TagObject(key="test", type="METADATA", value="val")
    tag2 = TagObject(key="test", type="METADATA", value="val")
    tag3 = TagObject(key="different", type="METADATA", value="val")

    assert tag1 == tag2
    assert tag1 != tag3


def test_ne_method_exists():
    """Verify __ne__ method exists and works."""
    tag1 = TagObject(key="test", type="METADATA", value="val")
    tag2 = TagObject(key="different", type="METADATA", value="val")

    assert tag1 != tag2
    assert tag1 != tag2


# Class Attributes Tests
def test_swagger_types_attribute_exists():
    """Verify swagger_types class attribute exists with expected structure."""
    assert hasattr(TagObject, "swagger_types")
    swagger_types = TagObject.swagger_types

    # Verify existing type mappings
    assert "key" in swagger_types
    assert swagger_types["key"] == "str"

    assert "type" in swagger_types
    assert swagger_types["type"] == "str"

    assert "value" in swagger_types
    assert swagger_types["value"] == "object"


def test_attribute_map_exists():
    """Verify attribute_map class attribute exists with expected structure."""
    assert hasattr(TagObject, "attribute_map")
    attribute_map = TagObject.attribute_map

    # Verify existing attribute mappings
    assert "key" in attribute_map
    assert attribute_map["key"] == "key"

    assert "type" in attribute_map
    assert attribute_map["type"] == "type"

    assert "value" in attribute_map
    assert attribute_map["value"] == "value"


# Integration Tests
def test_complete_workflow_metadata_tag():
    """Test complete workflow with METADATA tag type."""
    # Create
    tag = TagObject()

    # Set values
    tag.key = "environment"
    tag.type = "METADATA"
    tag.value = "production"

    # Verify
    assert tag.key == "environment"
    assert tag.type == "METADATA"
    assert tag.value == "production"

    # Convert to dict
    tag_dict = tag.to_dict()
    expected = {
        "key": "environment",
        "type": "METADATA",
        "value": "production",
    }
    assert tag_dict == expected


def test_complete_workflow_rate_limit_tag():
    """Test complete workflow with RATE_LIMIT tag type."""
    # Create with constructor
    tag = TagObject(key="max_requests", type="RATE_LIMIT", value=1000)

    # Verify
    assert tag.key == "max_requests"
    assert tag.type == "RATE_LIMIT"
    assert tag.value == 1000

    # Test string representation
    str_repr = tag.to_str()
    assert isinstance(str_repr, str)
    assert "max_requests" in str_repr
    assert "RATE_LIMIT" in str_repr
    assert "1000" in str_repr


def test_discriminator_attribute_exists():
    """Verify discriminator attribute exists and is properly initialized."""
    tag = TagObject()
    assert hasattr(tag, "discriminator")
    assert tag.discriminator is None


def test_private_attributes_exist():
    """Verify private attributes are properly initialized."""
    tag = TagObject()
    assert hasattr(tag, "_key")
    assert hasattr(tag, "_type")
    assert hasattr(tag, "_value")

    # Initially should be None
    assert tag._key is None
    assert tag._type is None
    assert tag._value is None


# Regression Tests
def test_json_serialization_compatibility():
    """Test that to_dict output is JSON serializable."""

    tag = TagObject(
        key="test_key", type="METADATA", value={"nested": "data", "number": 42}
    )

    tag_dict = tag.to_dict()
    # Should not raise exception
    json_str = json.dumps(tag_dict)
    assert isinstance(json_str, str)

    # Verify round trip
    parsed = json.loads(json_str)
    assert parsed["key"] == "test_key"
    assert parsed["type"] == "METADATA"
    assert parsed["value"] == {"nested": "data", "number": 42}


def test_copy_and_modify_pattern():
    """Test common pattern of copying and modifying objects."""
    original = TagObject(key="orig", type="METADATA", value="orig_val")

    # Create new instance with modified values
    modified = TagObject(
        key=original.key + "_modified",
        type=original.type,
        value=original.value + "_modified",
    )

    assert modified.key == "orig_modified"
    assert modified.type == "METADATA"
    assert modified.value == "orig_val_modified"

    # Original should be unchanged
    assert original.key == "orig"
    assert original.value == "orig_val"


def test_edge_case_empty_string_values():
    """Test edge cases with empty string values."""
    tag = TagObject()

    # Empty string key
    tag.key = ""
    assert tag.key == ""

    # Empty string value
    tag.value = ""
    assert tag.value == ""

    # Type should still validate
    tag.type = "METADATA"
    assert tag.type == "METADATA"
