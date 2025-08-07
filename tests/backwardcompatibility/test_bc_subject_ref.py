import pytest

from conductor.client.http.models import SubjectRef
from conductor.shared.http.enums.subject_type import SubjectType


def test_constructor_signature_compatibility():
    """Test that constructor signature remains backward compatible."""
    # Should accept no arguments (all optional)
    obj1 = SubjectRef()
    assert obj1.type is None
    assert obj1.id is None

    # Should accept type only
    obj2 = SubjectRef(type="USER")
    assert obj2.type == "USER"
    assert obj2.id is None

    # Should accept id only
    obj3 = SubjectRef(id="test-id")
    assert obj3.type is None
    assert obj3.id == "test-id"

    # Should accept both parameters
    obj4 = SubjectRef(type="ROLE", id="admin-role")
    assert obj4.type == "ROLE"
    assert obj4.id == "admin-role"


def test_required_fields_exist():
    """Test that all existing fields still exist."""
    obj = SubjectRef()

    # Core fields must exist
    assert hasattr(obj, "type")
    assert hasattr(obj, "id")

    # Internal fields must exist
    assert hasattr(obj, "_type")
    assert hasattr(obj, "_id")

    # Metadata fields must exist
    assert hasattr(obj, "discriminator")
    assert hasattr(obj, "swagger_types")
    assert hasattr(obj, "attribute_map")


def test_field_types_unchanged():
    """Test that field types haven't changed."""
    obj = SubjectRef(type="USER", id="test-id")

    # Type field should be string
    assert isinstance(obj.type, str)

    # ID field should be string
    assert isinstance(obj.id, str)

    # Swagger types metadata unchanged
    expected_types = {"type": "str", "id": "str"}
    assert obj.swagger_types == expected_types

    # Attribute map unchanged
    expected_map = {"type": "type", "id": "id"}
    assert obj.attribute_map == expected_map


def test_type_validation_rules_preserved():
    """Test that existing type validation rules still apply."""
    obj = SubjectRef()

    # Valid values should work (existing enum values)
    valid_types = ["USER", "ROLE", "GROUP"]
    for valid_type in valid_types:
        obj.type = valid_type
        assert obj.type == valid_type

    # Invalid values should raise ValueError
    invalid_types = ["INVALID", "user", "role", "group", "", None, 123, []]
    for invalid_type in invalid_types:
        with pytest.raises(ValueError, match="Invalid") as excinfo:
            obj.type = invalid_type
        assert "Invalid value for `type`" in str(excinfo.value)
        assert "must be one of" in str(excinfo.value)


def test_constructor_validation_behavior():
    """Test that constructor validation behavior is preserved."""
    # Constructor with None type should not validate (current behavior)
    obj1 = SubjectRef(type=None, id="test")
    assert obj1.type is None
    assert obj1.id == "test"

    # Constructor with valid type should work
    obj2 = SubjectRef(type="USER", id="test")
    assert obj2.type == "USER"
    assert obj2.id == "test"

    # Constructor with invalid type should raise error
    with pytest.raises(ValueError, match="Invalid"):
        SubjectRef(type="INVALID", id="test")


def test_id_field_no_validation():
    """Test that ID field has no validation (current behavior)."""
    obj = SubjectRef()

    # Any value should be acceptable for ID
    test_values = ["test", "", None, 123, [], {}]
    for value in test_values:
        obj.id = value
        assert obj.id == value


def test_property_accessors_work():
    """Test that property getters and setters still work."""
    obj = SubjectRef()

    # Type property
    obj.type = "USER"
    assert obj.type == "USER"
    assert obj._type == "USER"  # Internal field should match

    # ID property
    obj.id = "test-id"
    assert obj.id == "test-id"
    assert obj._id == "test-id"  # Internal field should match


def test_core_methods_exist():
    """Test that essential methods still exist and work."""
    obj = SubjectRef(type="USER", id="test-id")

    # to_dict method
    assert hasattr(obj, "to_dict")
    result_dict = obj.to_dict()
    assert isinstance(result_dict, dict)
    assert result_dict["type"] == "USER"
    assert result_dict["id"] == "test-id"

    # to_str method
    assert hasattr(obj, "to_str")
    result_str = obj.to_str()
    assert isinstance(result_str, str)

    # __repr__ method
    repr_str = repr(obj)
    assert isinstance(repr_str, str)

    # __eq__ method
    obj2 = SubjectRef(type="USER", id="test-id")
    assert obj == obj2

    # __ne__ method
    obj3 = SubjectRef(type="ROLE", id="test-id")
    assert obj != obj3


def test_subject_type_enum_compatibility():
    """Test that SubjectType enum values are preserved."""
    # Existing enum values must still exist
    assert SubjectType.USER == "USER"
    assert SubjectType.ROLE == "ROLE"
    assert SubjectType.GROUP == "GROUP"

    # Note: TAG is in enum but not in validation - this is current behavior
    assert SubjectType.TAG == "TAG"

    # Enum should be usable with the model
    obj = SubjectRef()
    obj.type = SubjectType.USER.value
    assert obj.type == "USER"


def test_discriminator_field_preserved():
    """Test that discriminator field behavior is preserved."""
    obj = SubjectRef()
    assert obj.discriminator is None  # Should be None by default

    # Should be assignable (if needed for future compatibility)
    obj.discriminator = "test"
    assert obj.discriminator == "test"


def test_serialization_compatibility():
    """Test that serialization format hasn't changed."""
    obj = SubjectRef(type="USER", id="user-123")

    # to_dict should produce expected structure
    expected_dict = {"type": "USER", "id": "user-123"}
    assert obj.to_dict() == expected_dict


def test_existing_validation_error_format():
    """Test that validation error messages haven't changed format."""
    obj = SubjectRef()

    with pytest.raises(ValueError, match="Invalid") as excinfo:
        obj.type = "INVALID"

    error_msg = str(excinfo.value)
    # Check specific error message format
    assert "Invalid value for `type` (INVALID)" in error_msg
    assert "must be one of ['USER', 'ROLE', 'GROUP']" in error_msg


def test_edge_cases_compatibility():
    """Test edge cases that should maintain backward compatibility."""
    # Empty constructor
    obj1 = SubjectRef()
    assert obj1.type is None
    assert obj1.id is None

    # Setting type to None after initialization
    obj2 = SubjectRef(type="USER")
    obj2._type = None  # Direct assignment to bypass setter
    assert obj2.type is None

    # Case sensitivity (should fail)
    with pytest.raises(ValueError, match="Invalid"):
        SubjectRef(type="user")  # lowercase should fail
