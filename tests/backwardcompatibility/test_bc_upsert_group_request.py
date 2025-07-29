import pytest

from conductor.client.http.models import UpsertGroupRequest


@pytest.fixture
def valid_roles():
    """Set up test fixture with known valid enum values."""
    return ["ADMIN", "USER", "WORKER", "METADATA_MANAGER", "WORKFLOW_MANAGER"]


@pytest.fixture
def valid_description():
    """Set up test fixture with valid description."""
    return "Test group description"


def test_constructor_signature_preserved(valid_description, valid_roles):
    """Verify constructor signature hasn't changed - both params optional."""
    # Test all constructor variations that should continue working
    obj1 = UpsertGroupRequest()
    assert obj1 is not None

    obj2 = UpsertGroupRequest(description=valid_description)
    assert obj2 is not None

    obj3 = UpsertGroupRequest(roles=valid_roles)
    assert obj3 is not None

    obj4 = UpsertGroupRequest(description=valid_description, roles=valid_roles)
    assert obj4 is not None


def test_required_fields_exist():
    """Verify all expected fields still exist."""
    obj = UpsertGroupRequest()

    # These fields must exist for backward compatibility
    assert hasattr(obj, "description")
    assert hasattr(obj, "roles")

    # Property access should work
    assert hasattr(obj, "_description")
    assert hasattr(obj, "_roles")


def test_field_types_unchanged(valid_description, valid_roles):
    """Verify field types haven't changed."""
    obj = UpsertGroupRequest(description=valid_description, roles=valid_roles)

    # Description should be string or None
    assert isinstance(obj.description, str)

    # Roles should be list or None
    assert isinstance(obj.roles, list)
    if obj.roles:
        for role in obj.roles:
            assert isinstance(role, str)


def test_description_field_behavior(valid_description):
    """Verify description field behavior unchanged."""
    obj = UpsertGroupRequest()

    # Initially None
    assert obj.description is None

    # Can be set to string
    obj.description = valid_description
    assert obj.description == valid_description

    # Can be set to None
    obj.description = None
    assert obj.description is None


def test_roles_field_behavior(valid_roles):
    """Verify roles field behavior unchanged."""
    obj = UpsertGroupRequest()

    # Initially None
    assert obj.roles is None

    # Can be set to valid roles list
    obj.roles = valid_roles
    assert obj.roles == valid_roles


def test_existing_enum_values_preserved(valid_roles):
    """Verify all existing enum values still work."""
    obj = UpsertGroupRequest()

    # Test each known enum value individually
    for role in valid_roles:
        obj.roles = [role]
        assert obj.roles == [role]

    # Test all values together
    obj.roles = valid_roles
    assert obj.roles == valid_roles


def test_roles_validation_behavior_preserved():
    """Verify roles validation still works as expected."""
    obj = UpsertGroupRequest()

    # Invalid role should raise ValueError during assignment
    with pytest.raises(ValueError, match="Invalid values for `roles`") as excinfo:
        obj.roles = ["INVALID_ROLE"]

    error_msg = str(excinfo.value)
    assert "INVALID_ROLE" in error_msg

    # Mixed valid/invalid should also fail
    with pytest.raises(ValueError, match="Invalid"):
        obj.roles = ["ADMIN", "INVALID_ROLE"]


def test_validation_timing_preserved():
    """Verify when validation occurs hasn't changed."""
    # Constructor with valid roles should work
    obj = UpsertGroupRequest(roles=["ADMIN"])
    assert obj.roles == ["ADMIN"]

    # Constructor with None roles should work (skips setter validation)
    obj2 = UpsertGroupRequest(roles=None)
    assert obj2.roles is None

    # But setting invalid role later should raise error
    with pytest.raises(ValueError, match="Invalid"):
        obj.roles = ["INVALID_ROLE"]

    # And setting None after creation should raise TypeError
    with pytest.raises(TypeError):
        obj.roles = None


def test_property_accessors_preserved(valid_description, valid_roles):
    """Verify property getters/setters still work."""
    obj = UpsertGroupRequest()

    # Description property
    obj.description = valid_description
    assert obj.description == valid_description

    # Roles property
    obj.roles = valid_roles
    assert obj.roles == valid_roles


def test_serialization_methods_preserved(valid_description, valid_roles):
    """Verify serialization methods still exist and work."""
    obj = UpsertGroupRequest(description=valid_description, roles=valid_roles)

    # to_dict method
    assert hasattr(obj, "to_dict")
    result_dict = obj.to_dict()
    assert isinstance(result_dict, dict)
    assert result_dict["description"] == valid_description
    assert result_dict["roles"] == valid_roles

    # to_str method
    assert hasattr(obj, "to_str")
    result_str = obj.to_str()
    assert isinstance(result_str, str)

    # __repr__ method
    repr_str = repr(obj)
    assert isinstance(repr_str, str)


def test_equality_methods_preserved(valid_description, valid_roles):
    """Verify equality comparison methods still work."""
    obj1 = UpsertGroupRequest(description=valid_description, roles=valid_roles)
    obj2 = UpsertGroupRequest(description=valid_description, roles=valid_roles)
    obj3 = UpsertGroupRequest(description="Different", roles=valid_roles)

    # __eq__ method
    assert obj1 == obj2
    assert obj1 != obj3

    # __ne__ method
    assert not (obj1 != obj2)
    assert obj1 != obj3


def test_class_attributes_preserved():
    """Verify important class attributes still exist."""
    # swagger_types mapping
    assert hasattr(UpsertGroupRequest, "swagger_types")
    swagger_types = UpsertGroupRequest.swagger_types
    assert "description" in swagger_types
    assert "roles" in swagger_types
    assert swagger_types["description"] == "str"
    assert swagger_types["roles"] == "list[str]"

    # attribute_map mapping
    assert hasattr(UpsertGroupRequest, "attribute_map")
    attribute_map = UpsertGroupRequest.attribute_map
    assert "description" in attribute_map
    assert "roles" in attribute_map


def test_none_handling_preserved():
    """Verify None value handling hasn't changed."""
    obj = UpsertGroupRequest()

    # None should be acceptable for description
    obj.description = None
    assert obj.description is None

    # Roles should initially be None (from constructor)
    assert obj.roles is None

    # Constructor with roles=None should work
    obj2 = UpsertGroupRequest(roles=None)
    assert obj2.roles is None

    # But setting roles = None after creation should fail (current behavior)
    with pytest.raises(TypeError):
        obj.roles = None

    # Serialization should handle None values
    result_dict = obj.to_dict()
    assert result_dict.get("description") is None
    assert result_dict.get("roles") is None


def test_empty_roles_list_handling():
    """Verify empty roles list handling preserved."""
    obj = UpsertGroupRequest()

    # Empty list should be valid
    obj.roles = []
    assert obj.roles == []

    # Should serialize properly
    result_dict = obj.to_dict()
    assert result_dict["roles"] == []
