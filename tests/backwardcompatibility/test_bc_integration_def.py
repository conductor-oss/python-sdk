import pytest

from conductor.client.http.models.integration_def import IntegrationDef


@pytest.fixture
def valid_category_values():
    """Valid enum values based on current model."""
    return ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"]


@pytest.fixture
def valid_data():
    """Valid test data."""
    return {
        "category": "API",
        "category_label": "API Integration",
        "configuration": {"key": "value"},
        "description": "Test integration",
        "enabled": True,
        "icon_name": "test-icon",
        "name": "test-integration",
        "tags": ["tag1", "tag2"],
        "type": "custom",
    }


def test_constructor_all_parameters_none():
    """Test that constructor works with all parameters as None (current behavior)."""
    integration = IntegrationDef()

    # Verify all fields are initialized to None
    assert integration.category is None
    assert integration.category_label is None
    assert integration.configuration is None
    assert integration.description is None
    assert integration.enabled is None
    assert integration.icon_name is None
    assert integration.name is None
    assert integration.tags is None
    assert integration.type is None


def test_constructor_with_valid_parameters(valid_data):
    """Test constructor with all valid parameters."""
    integration = IntegrationDef(**valid_data)

    # Verify all values are set correctly
    assert integration.category == "API"
    assert integration.category_label == "API Integration"
    assert integration.configuration == {"key": "value"}
    assert integration.description == "Test integration"
    assert integration.enabled is True
    assert integration.icon_name == "test-icon"
    assert integration.name == "test-integration"
    assert integration.tags == ["tag1", "tag2"]
    assert integration.type == "custom"


def test_all_expected_fields_exist():
    """Test that all expected fields exist and are accessible."""
    integration = IntegrationDef()

    # Test field existence via property access
    expected_fields = [
        "category",
        "category_label",
        "configuration",
        "description",
        "enabled",
        "icon_name",
        "name",
        "tags",
        "type",
    ]

    for field in expected_fields:
        # Should not raise AttributeError
        value = getattr(integration, field)
        assert value is None  # Default value should be None


def test_swagger_types_contains_required_fields():
    """Test that swagger_types contains all required fields (allows type evolution)."""
    required_fields = [
        "category",
        "category_label",
        "configuration",
        "description",
        "enabled",
        "icon_name",
        "name",
        "tags",
        "type",
    ]

    for field in required_fields:
        assert field in IntegrationDef.swagger_types
        # Verify it has a type (but don't enforce specific type for compatibility)
        assert isinstance(IntegrationDef.swagger_types[field], str)
        assert len(IntegrationDef.swagger_types[field]) > 0


def test_attribute_map_structure():
    """Test that attribute_map maintains expected mapping."""
    expected_map = {
        "category": "category",
        "category_label": "categoryLabel",
        "configuration": "configuration",
        "description": "description",
        "enabled": "enabled",
        "icon_name": "iconName",
        "name": "name",
        "tags": "tags",
        "type": "type",
    }

    for field, expected_json_key in expected_map.items():
        assert field in IntegrationDef.attribute_map
        assert IntegrationDef.attribute_map[field] == expected_json_key


def test_category_enum_validation(valid_category_values):
    """Test that category field validates against expected enum values."""
    integration = IntegrationDef()

    # Test valid enum values
    for valid_value in valid_category_values:
        integration.category = valid_value
        assert integration.category == valid_value

    # Test invalid enum value
    with pytest.raises(ValueError, match="Invalid") as excinfo:
        integration.category = "INVALID_CATEGORY"

    assert "Invalid value for `category`" in str(excinfo.value)
    assert "must be one of" in str(excinfo.value)

    # Test None assignment also raises ValueError
    with pytest.raises(ValueError, match="Invalid") as excinfo:
        integration.category = None

    assert "Invalid value for `category`" in str(excinfo.value)


def test_category_constructor_validation():
    """Test category validation during construction."""
    # Valid category in constructor
    integration = IntegrationDef(category="API")
    assert integration.category == "API"

    # None category in constructor (should work - validation happens on setter)
    integration_none = IntegrationDef(category=None)
    assert integration_none.category is None

    # Invalid category in constructor
    with pytest.raises(ValueError, match="Invalid"):
        IntegrationDef(category="INVALID_CATEGORY")


def test_field_type_assignments():
    """Test that fields accept expected types."""
    integration = IntegrationDef()

    # String fields
    string_fields = ["category_label", "description", "icon_name", "name", "type"]
    for field in string_fields:
        setattr(integration, field, "test_value")
        assert getattr(integration, field) == "test_value"

    # Boolean field
    integration.enabled = True
    assert integration.enabled is True
    integration.enabled = False
    assert integration.enabled is False

    # Configuration field (should accept dict for backward compatibility)
    test_config = {"key1": "value1", "key2": 2}
    integration.configuration = test_config
    assert integration.configuration == test_config

    # List field
    test_tags = ["tag1", "tag2", "tag3"]
    integration.tags = test_tags
    assert integration.tags == test_tags


def test_configuration_backward_compatibility():
    """Test that configuration field maintains backward compatibility with dict input."""
    integration = IntegrationDef()

    # Should accept dictionary (original behavior)
    config_dict = {"api_key": "secret", "timeout": 30}
    integration.configuration = config_dict
    assert integration.configuration == config_dict

    # Should work in constructor
    integration2 = IntegrationDef(configuration={"host": "localhost"})
    assert integration2.configuration == {"host": "localhost"}


def test_to_dict_method_exists(valid_data):
    """Test that to_dict method exists and works."""
    integration = IntegrationDef(**valid_data)
    result = integration.to_dict()

    assert isinstance(result, dict)
    # Verify key fields are present in output
    assert result["category"] == "API"
    assert result["name"] == "test-integration"


def test_to_str_method_exists(valid_data):
    """Test that to_str method exists and works."""
    integration = IntegrationDef(**valid_data)
    result = integration.to_str()

    assert isinstance(result, str)
    assert "API" in result


def test_equality_methods_exist(valid_data):
    """Test that equality methods exist and work."""
    integration1 = IntegrationDef(**valid_data)
    integration2 = IntegrationDef(**valid_data)
    integration3 = IntegrationDef(name="different")

    # Test __eq__
    assert integration1 == integration2
    assert integration1 != integration3

    # Test __ne__
    assert not (integration1 != integration2)
    assert integration1 != integration3


def test_repr_method_exists(valid_data):
    """Test that __repr__ method exists and works."""
    integration = IntegrationDef(**valid_data)
    repr_str = repr(integration)

    assert isinstance(repr_str, str)
    assert "API" in repr_str


def test_discriminator_field_exists():
    """Test that discriminator field exists (swagger/openapi compatibility)."""
    integration = IntegrationDef()
    assert integration.discriminator is None


def test_private_attributes_exist():
    """Test that private attributes are properly initialized."""
    integration = IntegrationDef()

    # These private attributes should exist
    private_attrs = [
        "_category",
        "_category_label",
        "_configuration",
        "_description",
        "_enabled",
        "_icon_name",
        "_name",
        "_tags",
        "_type",
    ]

    for attr in private_attrs:
        assert hasattr(integration, attr)
        assert getattr(integration, attr) is None


def test_partial_construction():
    """Test construction with only some parameters."""
    integration = IntegrationDef(name="partial-test", category="API", enabled=True)

    assert integration.name == "partial-test"
    assert integration.category == "API"
    assert integration.enabled is True
    # Other fields should be None
    assert integration.description is None
    assert integration.tags is None


def test_none_assignments_behavior(valid_data):
    """Test None assignment behavior for different field types."""
    integration = IntegrationDef(**valid_data)

    # Verify initial values are set
    assert integration.category is not None

    # Category field does NOT allow None assignment (validates against enum)
    with pytest.raises(ValueError, match="Invalid"):
        integration.category = None

    # Other fields allow None assignment
    integration.category_label = None
    integration.configuration = None
    integration.description = None
    integration.enabled = None
    integration.icon_name = None
    integration.name = None
    integration.tags = None
    integration.type = None

    # Verify non-category fields can be None
    assert integration.category_label is None
    assert integration.configuration is None
    assert integration.description is None
    assert integration.enabled is None
    assert integration.icon_name is None
    assert integration.name is None
    assert integration.tags is None
    assert integration.type is None

    # Category should still have original value
    assert integration.category == "API"


def test_serialization_consistency(valid_data):
    """Test that serialization produces consistent results."""
    integration = IntegrationDef(**valid_data)

    # to_dict should work
    dict_result = integration.to_dict()
    assert isinstance(dict_result, dict)

    # Should contain all the expected fields with correct values
    assert dict_result.get("category") == "API"
    assert dict_result.get("name") == "test-integration"
    assert dict_result.get("enabled") is True

    # Configuration should be serialized properly regardless of internal type
    assert dict_result.get("configuration") is not None


def test_backward_compatible_construction_patterns():
    """Test various construction patterns that existing code might use."""
    # Pattern 1: Positional arguments (if supported)
    try:
        integration1 = IntegrationDef("API", "API Integration")
        # If this works, verify it
        assert integration1.category == "API"
    except TypeError:
        # If positional args not supported, that's fine for this version
        pass

    # Pattern 2: Keyword arguments (most common)
    integration2 = IntegrationDef(category="API", name="test")
    assert integration2.category == "API"
    assert integration2.name == "test"

    # Pattern 3: Mixed with configuration dict
    integration3 = IntegrationDef(
        category="API", configuration={"key": "value"}, enabled=True
    )
    assert integration3.category == "API"
    assert integration3.configuration == {"key": "value"}
    assert integration3.enabled is True


def test_api_contract_stability():
    """Test that the public API contract remains stable."""
    integration = IntegrationDef()

    # All expected public methods should exist
    public_methods = ["to_dict", "to_str", "__eq__", "__ne__", "__repr__"]
    for method in public_methods:
        assert hasattr(integration, method)
        assert callable(getattr(integration, method))

    # All expected properties should exist and be settable
    properties = [
        "category",
        "category_label",
        "configuration",
        "description",
        "enabled",
        "icon_name",
        "name",
        "tags",
        "type",
    ]
    for prop in properties:
        # Should be readable
        getattr(integration, prop)
        # Should be writable (except category needs valid value)
        if prop == "category":
            setattr(integration, prop, "API")
            assert getattr(integration, prop) == "API"
        else:
            setattr(integration, prop, f"test_{prop}")
            assert getattr(integration, prop) == f"test_{prop}"
