import inspect

import pytest

from conductor.client.adapters.models.permission_adapter import PermissionAdapter


@pytest.fixture
def valid_name():
    """Set up test fixture with known good value."""
    return "test_permission"


def test_constructor_signature_compatibility():
    """Test that constructor signature remains backward compatible."""
    # Get constructor signature
    sig = inspect.signature(PermissionAdapter.__init__)
    params = list(sig.parameters.keys())

    # Verify 'self' and 'name' parameters exist
    assert "self" in params, "Constructor missing 'self' parameter"
    assert "name" in params, "Constructor missing 'name' parameter"

    # Verify 'name' parameter has default value (backward compatibility)
    name_param = sig.parameters["name"]
    assert (
        name_param.default is None
    ), "'name' parameter should default to None for backward compatibility"


def test_constructor_with_no_args():
    """Test constructor can be called without arguments (existing behavior)."""
    permission = PermissionAdapter()
    assert isinstance(permission, PermissionAdapter)
    assert permission.name is None


def test_constructor_with_name_arg(valid_name):
    """Test constructor with name argument (existing behavior)."""
    permission = PermissionAdapter(name=valid_name)
    assert isinstance(permission, PermissionAdapter)
    assert permission.name == valid_name


def test_required_attributes_exist():
    """Test that all existing attributes still exist."""
    permission = PermissionAdapter()

    # Core attributes that must exist for backward compatibility
    required_attrs = [
        "name",  # Property
        "_name",  # Internal storage
        "discriminator",  # Swagger attribute
        "swagger_types",  # Class attribute
        "attribute_map",  # Class attribute
    ]

    for attr in required_attrs:
        assert hasattr(permission, attr) or hasattr(
            PermissionAdapter, attr
        ), f"Missing required attribute: {attr}"


def test_swagger_types_compatibility():
    """Test that swagger_types mapping hasn't changed."""
    expected_types = {"name": "str"}

    # swagger_types must contain at least the expected mappings
    for field, expected_type in expected_types.items():
        assert (
            field in PermissionAdapter.swagger_types
        ), f"Missing field in swagger_types: {field}"
        assert PermissionAdapter.swagger_types[field] == expected_type, (
            f"Type changed for field {field}: expected {expected_type}, "
            f"got {PermissionAdapter.swagger_types[field]}"
        )


def test_attribute_map_compatibility():
    """Test that attribute_map mapping hasn't changed."""
    expected_mappings = {"name": "name"}

    # attribute_map must contain at least the expected mappings
    for field, expected_mapping in expected_mappings.items():
        assert (
            field in PermissionAdapter.attribute_map
        ), f"Missing field in attribute_map: {field}"
        assert PermissionAdapter.attribute_map[field] == expected_mapping, (
            f"Mapping changed for field {field}: expected {expected_mapping}, "
            f"got {PermissionAdapter.attribute_map[field]}"
        )


def test_name_property_behavior(valid_name):
    """Test that name property getter/setter behavior is preserved."""
    permission = PermissionAdapter()

    # Test getter returns None initially
    assert permission.name is None

    # Test setter works
    permission.name = valid_name
    assert permission.name == valid_name

    # Test setter accepts None
    permission.name = None
    assert permission.name is None


def test_name_property_type_flexibility():
    """Test that name property accepts expected types."""
    permission = PermissionAdapter()

    # Test string assignment (primary expected type)
    permission.name = "test_string"
    assert permission.name == "test_string"

    # Test None assignment (for optional behavior)
    permission.name = None
    assert permission.name is None


def test_required_methods_exist():
    """Test that all existing methods still exist and are callable."""
    permission = PermissionAdapter()

    required_methods = [
        "to_dict",
        "to_str",
        "__repr__",
        "__eq__",
        "__ne__",
    ]

    for method_name in required_methods:
        assert hasattr(
            permission, method_name
        ), f"Missing required method: {method_name}"
        method = getattr(permission, method_name)
        assert callable(method), f"Method {method_name} is not callable"


def test_to_dict_method_behavior(valid_name):
    """Test that to_dict method returns expected structure."""
    permission = PermissionAdapter(name=valid_name)
    result = permission.to_dict()

    # Must return a dictionary
    assert isinstance(result, dict)

    # Must contain 'name' field for backward compatibility
    assert "name" in result
    assert result["name"] == valid_name


def test_to_dict_with_none_values():
    """Test to_dict handles None values correctly."""
    permission = PermissionAdapter()  # name will be None
    result = permission.to_dict()

    assert isinstance(result, dict)
    assert "name" in result
    assert result["name"] is None


def test_equality_comparison_behavior(valid_name):
    """Test that equality comparison works as expected."""
    permission1 = PermissionAdapter(name=valid_name)
    permission2 = PermissionAdapter(name=valid_name)
    permission3 = PermissionAdapter(name="different_name")
    permission4 = PermissionAdapter()

    # Test equality
    assert permission1 == permission2

    # Test inequality
    assert permission1 != permission3
    assert permission1 != permission4

    # Test inequality with different types
    assert permission1 != "not_a_permission"
    assert permission1 is not None


def test_string_representation_behavior(valid_name):
    """Test that string representation methods work."""
    permission = PermissionAdapter(name=valid_name)

    # Test to_str returns a string
    str_repr = permission.to_str()
    assert isinstance(str_repr, str)

    # Test __repr__ returns a string
    repr_result = repr(permission)
    assert isinstance(repr_result, str)

    # Both should be the same (based on implementation)
    assert str_repr == repr_result


def test_discriminator_attribute_preserved():
    """Test that discriminator attribute is preserved."""
    permission = PermissionAdapter()

    # discriminator should exist and be None (based on current implementation)
    assert hasattr(permission, "discriminator")
    assert permission.discriminator is None


def test_class_level_attributes_preserved():
    """Test that class-level attributes are preserved."""
    # These must be accessible as class attributes
    assert hasattr(PermissionAdapter, "swagger_types")
    assert hasattr(PermissionAdapter, "attribute_map")

    # They should be dictionaries
    assert isinstance(PermissionAdapter.swagger_types, dict)
    assert isinstance(PermissionAdapter.attribute_map, dict)


def test_constructor_parameter_order_compatibility(valid_name):
    """Test that constructor can be called with positional arguments."""
    # Based on signature: __init__(self, name=None)
    # Should be able to call with positional argument
    permission = PermissionAdapter(valid_name)
    assert permission.name == valid_name


def test_internal_state_consistency(valid_name):
    """Test that internal state remains consistent."""
    permission = PermissionAdapter(name=valid_name)

    # Internal _name should match public name property
    assert permission._name == permission.name

    # Changing via property should update internal state
    new_name = "updated_name"
    permission.name = new_name
    assert permission._name == new_name
