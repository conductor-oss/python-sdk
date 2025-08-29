import pytest

from conductor.client.http.models.upsert_user_request import \
    UpsertUserRequest


@pytest.fixture
def valid_name():
    """Set up test fixture with valid name."""
    return "John Doe"


@pytest.fixture
def valid_roles():
    """Set up test fixture with valid roles."""
    return ["ADMIN", "USER"]


@pytest.fixture
def valid_groups():
    """Set up test fixture with valid groups."""
    return ["group1", "group2"]


@pytest.fixture
def required_role_values():
    """Set up test fixture with known allowed role values that must continue to work."""
    return [
        "ADMIN",
        "USER",
        "WORKER",
        "METADATA_MANAGER",
        "WORKFLOW_MANAGER",
    ]


def test_constructor_signature_compatibility(valid_name, valid_roles, valid_groups):
    """Test that constructor accepts same parameters as before."""
    # Constructor should accept all parameters as optional (with defaults)
    request = UpsertUserRequest()
    assert request is not None

    # Constructor should accept name only
    request = UpsertUserRequest(name=valid_name)
    assert request is not None

    # Constructor should accept all parameters
    request = UpsertUserRequest(
        name=valid_name,
        roles=valid_roles,
        groups=valid_groups,
    )
    assert request is not None


def test_required_fields_exist():
    """Test that all expected fields exist and are accessible."""
    request = UpsertUserRequest()

    # These fields must exist for backward compatibility
    assert hasattr(request, "name")
    assert hasattr(request, "roles")
    assert hasattr(request, "groups")

    # Properties must be accessible
    assert hasattr(request, "_name")
    assert hasattr(request, "_roles")
    assert hasattr(request, "_groups")


def test_field_types_unchanged(valid_name, valid_roles, valid_groups):
    """Test that field types remain the same."""
    request = UpsertUserRequest(
        name=valid_name,
        roles=valid_roles,
        groups=valid_groups,
    )

    # Name should be string
    assert isinstance(request.name, str)

    # Roles should be list
    assert isinstance(request.roles, list)
    if request.roles:
        assert isinstance(request.roles[0], str)

    # Groups should be list
    assert isinstance(request.groups, list)
    if request.groups:
        assert isinstance(request.groups[0], str)


def test_property_getters_setters_exist(valid_name, valid_roles, valid_groups):
    """Test that property getters and setters still work."""
    request = UpsertUserRequest()

    # Test name property
    request.name = valid_name
    assert request.name == valid_name

    # Test roles property
    request.roles = valid_roles
    assert request.roles == valid_roles

    # Test groups property
    request.groups = valid_groups
    assert request.groups == valid_groups


def test_existing_role_values_still_allowed(required_role_values):
    """Test that all previously allowed role values still work."""
    request = UpsertUserRequest()

    # Test each individual role value
    for role in required_role_values:
        request.roles = [role]
        assert request.roles == [role]

    # Test all roles together
    request.roles = required_role_values
    assert request.roles == required_role_values

    # Test subset combinations
    request.roles = ["ADMIN", "USER"]
    assert request.roles == ["ADMIN", "USER"]


def test_role_validation_behavior_unchanged():
    """Test that role validation still works as expected."""
    request = UpsertUserRequest()

    # Invalid role should raise ValueError
    with pytest.raises(ValueError, match="Invalid values for `roles`") as excinfo:
        request.roles = ["INVALID_ROLE"]

    # Error message should contain expected information
    error_msg = str(excinfo.value)
    assert "INVALID_ROLE" in error_msg


def test_roles_validation_with_mixed_valid_invalid():
    """Test validation with mix of valid and invalid roles."""
    request = UpsertUserRequest()

    # Mix of valid and invalid should fail
    with pytest.raises(ValueError, match="Invalid"):
        request.roles = ["ADMIN", "INVALID_ROLE", "USER"]


def test_none_values_handling():
    """Test that None values are handled consistently."""
    request = UpsertUserRequest()

    # Initially should be None or empty
    assert request.name is None
    assert request.roles is None
    assert request.groups is None

    # Setting to None should work
    request.name = None
    request.groups = None
    # Note: roles=None might be handled differently due to validation


def test_core_methods_exist(valid_name, valid_roles, valid_groups):
    """Test that essential methods still exist."""
    request = UpsertUserRequest(
        name=valid_name,
        roles=valid_roles,
        groups=valid_groups,
    )

    # These methods must exist for backward compatibility
    assert hasattr(request, "to_dict")
    assert hasattr(request, "to_str")
    assert hasattr(request, "__repr__")
    assert hasattr(request, "__eq__")
    assert hasattr(request, "__ne__")

    # Methods should be callable
    assert callable(request.to_dict)
    assert callable(request.to_str)


def test_to_dict_structure_compatibility(valid_name, valid_roles, valid_groups):
    """Test that to_dict() returns expected structure."""
    request = UpsertUserRequest(
        name=valid_name,
        roles=valid_roles,
        groups=valid_groups,
    )

    result = request.to_dict()

    # Must be a dictionary
    assert isinstance(result, dict)

    # Must contain expected keys
    expected_keys = {"name", "roles", "groups"}
    assert expected_keys.issubset(set(result.keys()))

    # Values should match
    assert result["name"] == valid_name
    assert result["roles"] == valid_roles
    assert result["groups"] == valid_groups


def test_equality_comparison_works(valid_name, valid_roles, valid_groups):
    """Test that equality comparison still functions."""
    request1 = UpsertUserRequest(
        name=valid_name,
        roles=valid_roles,
        groups=valid_groups,
    )

    request2 = UpsertUserRequest(
        name=valid_name,
        roles=valid_roles,
        groups=valid_groups,
    )

    request3 = UpsertUserRequest(name="Different Name")

    # Equal objects should be equal
    assert request1 == request2
    assert not (request1 != request2)

    # Different objects should not be equal
    assert request1 != request3
    assert request1 != request3


def test_string_representation_works(valid_name, valid_roles, valid_groups):
    """Test that string representation methods work."""
    request = UpsertUserRequest(
        name=valid_name,
        roles=valid_roles,
        groups=valid_groups,
    )

    # Should return strings
    assert isinstance(str(request), str)
    assert isinstance(repr(request), str)
    assert isinstance(request.to_str(), str)

    # repr() should return the dictionary representation (current behavior)
    # This is backward compatibility - maintaining existing behavior
    repr_result = repr(request)
    assert "name" in repr_result
    assert "John Doe" in repr_result


def test_swagger_metadata_exists():
    """Test that swagger metadata is still available."""
    # swagger_types should exist as class attribute
    assert hasattr(UpsertUserRequest, "swagger_types")
    assert hasattr(UpsertUserRequest, "attribute_map")

    # Should contain expected mappings
    swagger_types = UpsertUserRequest.swagger_types
    assert "name" in swagger_types
    assert "roles" in swagger_types
    assert "groups" in swagger_types

    # Types should be as expected
    assert swagger_types["name"] == "str"
    assert swagger_types["roles"] == "list[str]"
    assert swagger_types["groups"] == "list[str]"


def test_field_assignment_after_construction(valid_name, valid_roles, valid_groups):
    """Test that fields can be modified after object creation."""
    request = UpsertUserRequest()

    # Should be able to assign all fields after construction
    request.name = valid_name
    request.roles = valid_roles
    request.groups = valid_groups

    assert request.name == valid_name
    assert request.roles == valid_roles
    assert request.groups == valid_groups


def test_empty_lists_handling():
    """Test that empty lists are handled properly."""
    request = UpsertUserRequest()

    # Empty lists should be acceptable
    request.roles = []
    request.groups = []

    assert request.roles == []
    assert request.groups == []
