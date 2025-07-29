import pytest

from conductor.client.http.models.target_ref import TargetRef, TargetType


@pytest.fixture
def valid_enum_values():
    """Set up test fixture with current valid enum values."""
    return [
        "WORKFLOW_DEF",
        "TASK_DEF",
        "APPLICATION",
        "USER",
        "SECRET",
        "TAG",
        "DOMAIN",
    ]


def test_class_exists_and_importable():
    """Verify TargetRef class still exists and is importable."""
    assert hasattr(TargetRef, "__init__")
    assert callable(TargetRef)


def test_target_type_enum_exists_and_importable():
    """Verify TargetType enum still exists and is importable."""
    assert hasattr(TargetType, "__members__")


def test_existing_enum_values_still_exist(valid_enum_values):
    """Verify all existing TargetType enum values are still present."""
    for expected_value in valid_enum_values:
        # Check enum has the attribute
        assert hasattr(TargetType, expected_value)
        # Check the value is correct
        enum_member = getattr(TargetType, expected_value)
        assert enum_member.value == expected_value


def test_no_parameter_constructor_behavior():
    """Test the actual behavior when no parameters are provided."""
    # Based on the model, constructor with no params should fail
    # because type=None triggers validation
    with pytest.raises(ValueError, match="Invalid") as excinfo:
        TargetRef()

    # Verify it's the expected validation error
    error_message = str(excinfo.value)
    assert "Invalid value for `type` (None)" in error_message


def test_constructor_signature_backward_compatible():
    """Verify constructor still accepts the same parameters that work."""
    # Should work with valid type parameter only
    target_ref = TargetRef(type="WORKFLOW_DEF")
    assert target_ref is not None

    # Should work with both parameters
    target_ref = TargetRef(type="TASK_DEF", id="test-id")
    assert target_ref is not None


def test_constructor_with_only_id_parameter():
    """Test constructor behavior when only id is provided."""
    # This should also fail because type defaults to None
    with pytest.raises(ValueError, match="Invalid") as excinfo:
        TargetRef(id="test-id")

    # Verify it's the expected validation error
    error_message = str(excinfo.value)
    assert "Invalid value for `type` (None)" in error_message


def test_required_attributes_exist():
    """Verify all existing attributes still exist."""
    target_ref = TargetRef(type="WORKFLOW_DEF")

    # Core attributes must exist
    assert hasattr(target_ref, "type")
    assert hasattr(target_ref, "id")

    # Internal attributes must exist
    assert hasattr(target_ref, "_type")
    assert hasattr(target_ref, "_id")

    # Swagger metadata must exist
    assert hasattr(target_ref, "swagger_types")
    assert hasattr(target_ref, "attribute_map")
    assert hasattr(target_ref, "discriminator")


def test_swagger_types_structure_unchanged():
    """Verify swagger_types contains existing fields with correct types."""
    expected_swagger_types = {"type": "str", "id": "str"}

    target_ref = TargetRef(type="APPLICATION")

    # Existing fields must be present with correct types
    for field, expected_type in expected_swagger_types.items():
        assert field in target_ref.swagger_types
        assert target_ref.swagger_types[field] == expected_type


def test_attribute_map_structure_unchanged():
    """Verify attribute_map contains existing mappings."""
    expected_attribute_map = {"type": "type", "id": "id"}

    target_ref = TargetRef(type="USER")

    # Existing mappings must be present
    for attr, expected_json_key in expected_attribute_map.items():
        assert attr in target_ref.attribute_map
        assert target_ref.attribute_map[attr] == expected_json_key


def test_type_property_getter_behavior():
    """Verify type property getter works as expected."""
    target_ref = TargetRef(type="WORKFLOW_DEF")

    # Should return assigned value
    assert target_ref.type == "WORKFLOW_DEF"

    # Test by setting directly to internal field
    target_ref._type = "TASK_DEF"
    assert target_ref.type == "TASK_DEF"


def test_id_property_getter_behavior():
    """Verify id property getter works as expected."""
    target_ref = TargetRef(type="SECRET")

    # Initially should be None (since we only set type)
    assert target_ref.id is None

    # Should return assigned value
    target_ref._id = "test-id"
    assert target_ref.id == "test-id"


def test_type_setter_validation_with_valid_values(valid_enum_values):
    """Verify type setter accepts all existing valid enum values."""
    target_ref = TargetRef(type="WORKFLOW_DEF")  # Start with valid value

    for valid_value in valid_enum_values:
        # Should not raise exception
        target_ref.type = valid_value
        assert target_ref.type == valid_value
        assert target_ref._type == valid_value


def test_type_setter_validation_rejects_invalid_values():
    """Verify type setter still validates and rejects invalid values."""
    target_ref = TargetRef(type="TAG")  # Start with valid value

    invalid_values = ["INVALID", "workflow_def", "", None, 123]

    for invalid_value in invalid_values:
        with pytest.raises(ValueError, match="Invalid") as excinfo:
            target_ref.type = invalid_value

        # Verify error message format is preserved
        error_message = str(excinfo.value)
        assert "Invalid value for `type`" in error_message
        assert "must be one of" in error_message


def test_id_setter_behavior_unchanged():
    """Verify id setter accepts any value (no validation)."""
    target_ref = TargetRef(type="DOMAIN")  # Start with valid type

    test_values = ["test-id", "", None, 123, [], {}]

    for test_value in test_values:
        # Should not raise exception
        target_ref.id = test_value
        assert target_ref.id == test_value
        assert target_ref._id == test_value


def test_constructor_assignment_triggers_validation():
    """Verify constructor parameter assignment triggers proper validation."""
    # Valid type should work
    target_ref = TargetRef(type="WORKFLOW_DEF")
    assert target_ref.type == "WORKFLOW_DEF"

    # Invalid type should raise error during construction
    with pytest.raises(ValueError, match="Invalid"):
        TargetRef(type="INVALID_TYPE")

    # None type should raise error during construction
    with pytest.raises(ValueError, match="Invalid"):
        TargetRef(type=None)


def test_required_methods_exist_with_correct_signatures():
    """Verify all existing methods still exist."""
    target_ref = TargetRef(type="APPLICATION")

    # Core methods must exist and be callable
    assert hasattr(target_ref, "to_dict")
    assert callable(target_ref.to_dict)

    assert hasattr(target_ref, "to_str")
    assert callable(target_ref.to_str)

    assert hasattr(target_ref, "__repr__")
    assert callable(target_ref.__repr__)

    assert hasattr(target_ref, "__eq__")
    assert callable(target_ref.__eq__)

    assert hasattr(target_ref, "__ne__")
    assert callable(target_ref.__ne__)


def test_to_dict_method_behavior():
    """Verify to_dict method returns expected structure."""
    target_ref = TargetRef(type="APPLICATION", id="app-123")
    result = target_ref.to_dict()

    # Should be a dictionary
    assert isinstance(result, dict)

    # Should contain existing fields
    assert "type" in result
    assert "id" in result

    # Values should match
    assert result["type"] == "APPLICATION"
    assert result["id"] == "app-123"


def test_equality_comparison_behavior():
    """Verify equality comparison works as expected."""
    target_ref1 = TargetRef(type="USER", id="user-123")
    target_ref2 = TargetRef(type="USER", id="user-123")
    target_ref3 = TargetRef(type="USER", id="user-456")

    # Equal objects should be equal
    assert target_ref1 == target_ref2
    assert not (target_ref1 != target_ref2)

    # Different objects should not be equal
    assert target_ref1 != target_ref3
    assert target_ref1 != target_ref3

    # Comparison with non-TargetRef should return False
    assert target_ref1 != "not a target ref"
    assert target_ref1 != "not a target ref"


def test_string_representation_works():
    """Verify string representation methods work."""
    target_ref = TargetRef(type="SECRET", id="secret-456")

    # to_str should return a string
    str_result = target_ref.to_str()
    assert isinstance(str_result, str)

    # __repr__ should return a string
    repr_result = repr(target_ref)
    assert isinstance(repr_result, str)

    # They should be the same
    assert str_result == repr_result
