import pytest

from conductor.client.http.models import AuthorizationRequest


@pytest.fixture
def mock_subject(mocker):
    """Mock SubjectRef object for testing."""
    mock_subject = mocker.Mock()
    mock_subject.to_dict.return_value = {"id": "test_subject"}
    return mock_subject


@pytest.fixture
def mock_target(mocker):
    """Mock TargetRef object for testing."""
    mock_target = mocker.Mock()
    mock_target.to_dict.return_value = {"id": "test_target"}
    return mock_target


def test_class_exists_and_instantiable(mock_subject, mock_target):
    """Test that the AuthorizationRequest class exists and can be instantiated."""
    # Test constructor with valid access values (None causes validation error)
    auth_request = AuthorizationRequest(
        subject=mock_subject, target=mock_target, access=["READ", "CREATE"]
    )
    assert isinstance(auth_request, AuthorizationRequest)

    # Test constructor with None for subject/target but valid access
    auth_request = AuthorizationRequest(access=["READ"])
    assert isinstance(auth_request, AuthorizationRequest)


def test_required_attributes_exist():
    """Test that all expected attributes exist on the class."""
    # Create instance with valid access to avoid None validation error
    auth_request = AuthorizationRequest(access=["READ"])

    # Test core attributes exist
    assert hasattr(auth_request, "subject")
    assert hasattr(auth_request, "target")
    assert hasattr(auth_request, "access")

    # Test internal attributes exist
    assert hasattr(auth_request, "_subject")
    assert hasattr(auth_request, "_target")
    assert hasattr(auth_request, "_access")
    assert hasattr(auth_request, "discriminator")


def test_class_metadata_exists():
    """Test that required class metadata exists and is correct."""
    # Test swagger_types exists and contains expected fields
    assert hasattr(AuthorizationRequest, "swagger_types")
    swagger_types = AuthorizationRequest.swagger_types

    assert "subject" in swagger_types
    assert "target" in swagger_types
    assert "access" in swagger_types

    # Test attribute_map exists and contains expected mappings
    assert hasattr(AuthorizationRequest, "attribute_map")
    attribute_map = AuthorizationRequest.attribute_map

    assert "subject" in attribute_map
    assert "target" in attribute_map
    assert "access" in attribute_map


def test_field_types_unchanged():
    """Test that field types haven't changed."""
    swagger_types = AuthorizationRequest.swagger_types

    # Verify exact type specifications
    assert swagger_types["subject"] == "SubjectRef"
    assert swagger_types["target"] == "TargetRef"
    assert swagger_types["access"] == "list[str]"


def test_attribute_mapping_unchanged():
    """Test that attribute mappings haven't changed."""
    attribute_map = AuthorizationRequest.attribute_map

    # Verify exact mappings
    assert attribute_map["subject"] == "subject"
    assert attribute_map["target"] == "target"
    assert attribute_map["access"] == "access"


def test_constructor_signature_compatibility(mock_subject, mock_target):
    """Test that constructor signature remains backward compatible."""
    # Test that constructor accepts all expected parameters
    auth_request = AuthorizationRequest(
        subject=mock_subject, target=mock_target, access=["READ"]
    )

    # Verify values are set correctly
    assert auth_request.subject == mock_subject
    assert auth_request.target == mock_target
    assert auth_request.access == ["READ"]


def test_constructor_optional_parameters(mock_subject):
    """Test constructor behavior with optional parameters."""
    # Test that None access causes validation error (current behavior)
    with pytest.raises(TypeError):
        AuthorizationRequest()

    # Test that partial parameters work when access is valid
    auth_request = AuthorizationRequest(subject=mock_subject, access=["READ"])
    assert auth_request.subject == mock_subject
    assert auth_request.target is None
    assert auth_request.access == ["READ"]

    # Test with only access parameter
    auth_request = AuthorizationRequest(access=["CREATE"])
    assert auth_request.subject is None
    assert auth_request.target is None
    assert auth_request.access == ["CREATE"]


def test_property_getters_work(mock_subject, mock_target):
    """Test that all property getters work correctly."""
    auth_request = AuthorizationRequest(
        subject=mock_subject, target=mock_target, access=["READ", "CREATE"]
    )

    # Test getters return correct values
    assert auth_request.subject == mock_subject
    assert auth_request.target == mock_target
    assert auth_request.access == ["READ", "CREATE"]


def test_property_setters_work(mock_subject, mock_target):
    """Test that all property setters work correctly."""
    auth_request = AuthorizationRequest(access=["READ"])

    # Test setting subject
    auth_request.subject = mock_subject
    assert auth_request.subject == mock_subject

    # Test setting target
    auth_request.target = mock_target
    assert auth_request.target == mock_target

    # Test setting access
    auth_request.access = ["READ", "CREATE"]
    assert auth_request.access == ["READ", "CREATE"]


def test_access_validation_rules_preserved():
    """Test that access field validation rules are preserved."""
    auth_request = AuthorizationRequest(access=["READ"])

    # Test valid access values work
    valid_access_values = ["CREATE", "READ", "UPDATE", "DELETE", "EXECUTE"]
    for access_value in valid_access_values:
        auth_request.access = [access_value]
        assert auth_request.access == [access_value]

    # Test combinations work
    auth_request.access = ["READ", "CREATE", "UPDATE"]
    assert auth_request.access == ["READ", "CREATE", "UPDATE"]


def test_access_validation_rejects_invalid_values():
    """Test that access validation still rejects invalid values."""
    auth_request = AuthorizationRequest(access=["READ"])

    # Test invalid single values
    with pytest.raises(ValueError, match="Invalid"):
        auth_request.access = ["INVALID"]

    # Test mixed valid/invalid values
    with pytest.raises(ValueError, match="Invalid"):
        auth_request.access = ["READ", "INVALID"]

    # Test completely invalid values
    with pytest.raises(ValueError, match="Invalid"):
        auth_request.access = ["BAD", "WORSE"]


def test_access_validation_error_message_format():
    """Test that access validation error messages are preserved."""
    auth_request = AuthorizationRequest(access=["READ"])

    with pytest.raises(ValueError, match="Invalid") as context:
        auth_request.access = ["INVALID"]
    error_message = str(context.value)
    # Verify error message contains expected information
    assert "Invalid values for `access`" in error_message
    assert "INVALID" in error_message


def test_core_methods_exist(mock_subject, mock_target):
    """Test that core model methods exist and work."""
    auth_request = AuthorizationRequest(
        subject=mock_subject, target=mock_target, access=["READ"]
    )

    # Test to_dict method exists and works
    assert hasattr(auth_request, "to_dict")
    result_dict = auth_request.to_dict()
    assert isinstance(result_dict, dict)

    # Test to_str method exists and works
    assert hasattr(auth_request, "to_str")
    result_str = auth_request.to_str()
    assert isinstance(result_str, str)

    # Test __repr__ method works
    repr_str = repr(auth_request)
    assert isinstance(repr_str, str)


def test_equality_methods_exist():
    """Test that equality methods exist and work."""
    auth_request1 = AuthorizationRequest(access=["READ"])
    auth_request2 = AuthorizationRequest(access=["READ"])
    auth_request3 = AuthorizationRequest(access=["CREATE"])

    # Test equality
    assert hasattr(auth_request1, "__eq__")
    assert auth_request1 == auth_request2
    assert auth_request1 != auth_request3

    # Test inequality
    assert hasattr(auth_request1, "__ne__")
    assert not (auth_request1 != auth_request2)
    assert auth_request1 != auth_request3


def test_to_dict_structure_preserved(mock_subject, mock_target):
    """Test that to_dict output structure is preserved."""
    auth_request = AuthorizationRequest(
        subject=mock_subject, target=mock_target, access=["READ", "CREATE"]
    )

    result_dict = auth_request.to_dict()

    # Verify expected keys exist
    assert "subject" in result_dict
    assert "target" in result_dict
    assert "access" in result_dict

    # Verify access value is preserved correctly
    assert result_dict["access"] == ["READ", "CREATE"]


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists and is properly initialized."""
    auth_request = AuthorizationRequest(access=["READ"])
    assert hasattr(auth_request, "discriminator")
    assert auth_request.discriminator is None


def test_backward_compatibility_with_existing_enum_values():
    """Test that all existing enum values for access field still work."""
    auth_request = AuthorizationRequest(access=["READ"])

    # Test each existing enum value individually
    existing_enum_values = ["CREATE", "READ", "UPDATE", "DELETE", "EXECUTE"]

    for enum_value in existing_enum_values:
        # Should not raise any exceptions
        auth_request.access = [enum_value]
        assert auth_request.access == [enum_value]

    # Test all values together
    auth_request.access = existing_enum_values
    assert auth_request.access == existing_enum_values


def test_field_assignment_behavior_preserved(mock_subject, mock_target):
    """Test that field assignment behavior is preserved."""
    auth_request = AuthorizationRequest(access=["READ"])

    # Test that None assignment works for subject/target
    auth_request.subject = None
    assert auth_request.subject is None

    auth_request.target = None
    assert auth_request.target is None

    # Test that None assignment for access causes validation error (current behavior)
    with pytest.raises(TypeError):
        auth_request.access = None

    # Test that proper values work
    auth_request.subject = mock_subject
    auth_request.target = mock_target
    auth_request.access = ["READ"]

    assert auth_request.subject == mock_subject
    assert auth_request.target == mock_target
    assert auth_request.access == ["READ"]


def test_none_access_validation_behavior():
    """Test that None access value causes expected validation error."""
    # Test during construction
    with pytest.raises(TypeError) as excinfo:
        AuthorizationRequest()

    error_message = str(excinfo.value)
    assert "'NoneType' object is not iterable" in error_message

    # Test during assignment
    auth_request = AuthorizationRequest(access=["READ"])
    with pytest.raises(TypeError) as excinfo:
        auth_request.access = None

    error_message = str(excinfo.value)
    assert "'NoneType' object is not iterable" in error_message
