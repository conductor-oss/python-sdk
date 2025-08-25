from conductor.client.adapters.models.conductor_user_adapter import ConductorUserAdapter


def test_constructor_with_no_arguments():
    """Test that constructor works with no arguments (all fields optional)."""
    user = ConductorUserAdapter()

    # All fields should be None by default
    assert user.id is None
    assert user.name is None
    assert user.roles is None
    assert user.groups is None
    assert user.uuid is None
    assert user.application_user is None
    assert user.encrypted_id is None
    assert user.encrypted_id_display_value is None


def test_constructor_with_all_arguments(mocker):
    """Test constructor with all existing fields to ensure no breaking changes."""
    # Create mocks locally for this test
    mock_role = mocker.Mock()
    mock_role.to_dict.return_value = {"role": "test_role"}

    mock_group = mocker.Mock()
    mock_group.to_dict.return_value = {"group": "test_group"}

    user = ConductorUserAdapter(
        id="user123",
        name="Test User",
        roles=[mock_role],
        groups=[mock_group],
        uuid="uuid-123",
        application_user=True,
        encrypted_id=False,
        encrypted_id_display_value="display_value",
    )

    # Verify all fields are set correctly
    assert user.id == "user123"
    assert user.name == "Test User"
    assert user.roles == [mock_role]
    assert user.groups == [mock_group]
    assert user.uuid == "uuid-123"
    assert user.application_user is True
    assert user.encrypted_id is False
    assert user.encrypted_id_display_value == "display_value"


def test_required_fields_exist():
    """Test that all expected fields exist and are accessible."""
    user = ConductorUserAdapter()

    # Test that all expected attributes exist (no AttributeError)
    required_fields = [
        "id",
        "name",
        "roles",
        "groups",
        "uuid",
        "application_user",
        "encrypted_id",
        "encrypted_id_display_value",
    ]

    for field in required_fields:
        assert hasattr(user, field), f"Field '{field}' should exist"
        # Should be able to get and set without error
        getattr(user, field)
        setattr(user, field, None)


def test_field_types_unchanged(mocker):
    """Test that field types match expected swagger types."""
    # Create mocks locally for this test
    mock_role = mocker.Mock()
    mock_group = mocker.Mock()

    user = ConductorUserAdapter()

    # Test string fields
    user.id = "test"
    assert isinstance(user.id, str)

    user.name = "test"
    assert isinstance(user.name, str)

    user.uuid = "test"
    assert isinstance(user.uuid, str)

    user.encrypted_id_display_value = "test"
    assert isinstance(user.encrypted_id_display_value, str)

    # Test boolean fields
    user.application_user = True
    assert isinstance(user.application_user, bool)

    user.encrypted_id = False
    assert isinstance(user.encrypted_id, bool)

    # Test list fields
    user.roles = [mock_role]
    assert isinstance(user.roles, list)

    user.groups = [mock_group]
    assert isinstance(user.groups, list)


def test_swagger_types_mapping_unchanged():
    """Test that swagger_types mapping hasn't changed."""
    expected_swagger_types = {
        "id": "str",
        "name": "str",
        "roles": "list[Role]",
        "groups": "list[Group]",
        "uuid": "str",
        "application_user": "bool",
        "encrypted_id": "bool",
        "encrypted_id_display_value": "str",
    }

    # Check that all expected types are present
    for field, expected_type in expected_swagger_types.items():
        assert (
            field in ConductorUserAdapter.swagger_types
        ), f"Field '{field}' missing from swagger_types"
        assert (
            ConductorUserAdapter.swagger_types[field] == expected_type
        ), f"Type for '{field}' changed from '{expected_type}'"


def test_attribute_map_unchanged():
    """Test that attribute mapping to JSON keys hasn't changed."""
    expected_attribute_map = {
        "id": "id",
        "name": "name",
        "roles": "roles",
        "groups": "groups",
        "uuid": "uuid",
        "application_user": "applicationUser",
        "encrypted_id": "encryptedId",
        "encrypted_id_display_value": "encryptedIdDisplayValue",
    }

    # Check that all expected mappings are present
    for field, expected_json_key in expected_attribute_map.items():
        assert (
            field in ConductorUserAdapter.attribute_map
        ), f"Field '{field}' missing from attribute_map"
        assert (
            ConductorUserAdapter.attribute_map[field] == expected_json_key
        ), f"JSON key for '{field}' changed from '{expected_json_key}'"


def test_to_dict_method_exists_and_works():
    """Test that to_dict method exists and produces expected structure."""
    user = ConductorUserAdapter(id="test123", name="Test User", application_user=True)

    result = user.to_dict()

    # Should be a dictionary
    assert isinstance(result, dict)

    # Should contain our set values
    assert result["id"] == "test123"
    assert result["name"] == "Test User"
    assert result["application_user"] is True


def test_to_dict_with_complex_objects(mocker):
    """Test to_dict method with Role and Group objects."""
    # Create mocks locally for this test
    mock_role = mocker.Mock()
    mock_role.to_dict.return_value = {"role": "test_role"}

    mock_group = mocker.Mock()
    mock_group.to_dict.return_value = {"group": "test_group"}

    user = ConductorUserAdapter(roles=[mock_role], groups=[mock_group])

    result = user.to_dict()

    # Complex objects should be converted via their to_dict method
    assert result["roles"] == [{"role": "test_role"}]
    assert result["groups"] == [{"group": "test_group"}]


def test_string_representation_methods():
    """Test that string representation methods exist and work."""
    user = ConductorUserAdapter(id="test", name="Test User")

    # to_str method should exist and return string
    str_repr = user.to_str()
    assert isinstance(str_repr, str)

    # __repr__ should exist and return string
    repr_str = repr(user)
    assert isinstance(repr_str, str)

    # __str__ (inherited) should work
    str_result = str(user)
    assert isinstance(str_result, str)


def test_equality_methods():
    """Test that equality comparison methods work correctly."""
    user1 = ConductorUserAdapter(id="test", name="Test User")
    user2 = ConductorUserAdapter(id="test", name="Test User")
    user3 = ConductorUserAdapter(id="different", name="Test User")

    # Equal objects
    assert user1 == user2
    assert not (user1 != user2)

    # Different objects
    assert user1 != user3
    assert user1 != user3

    # Different types
    assert user1 != "not a user"
    assert user1 != "not a user"


def test_property_setters_and_getters(mocker):
    """Test that all property setters and getters work without validation errors."""
    # Create mocks locally for this test
    mock_role = mocker.Mock()
    mock_group = mocker.Mock()

    user = ConductorUserAdapter()

    # Test that we can set and get all properties without errors
    test_values = {
        "id": "test_id",
        "name": "test_name",
        "roles": [mock_role],
        "groups": [mock_group],
        "uuid": "test_uuid",
        "application_user": True,
        "encrypted_id": False,
        "encrypted_id_display_value": "test_display",
    }

    for field, value in test_values.items():
        # Should be able to set
        setattr(user, field, value)
        # Should be able to get and value should match
        assert getattr(user, field) == value


def test_none_values_accepted():
    """Test that None values are accepted for all fields (backward compatibility)."""
    user = ConductorUserAdapter()

    # All fields should accept None values
    for field in [
        "id",
        "name",
        "roles",
        "groups",
        "uuid",
        "application_user",
        "encrypted_id",
        "encrypted_id_display_value",
    ]:
        setattr(user, field, None)
        assert getattr(user, field) is None


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists (swagger-generated classes often have this)."""
    user = ConductorUserAdapter()
    assert hasattr(user, "discriminator")
    assert user.discriminator is None  # Should be None by default
