import pytest

from conductor.client.http.models.integration_update import IntegrationUpdate


@pytest.fixture
def valid_category_values():
    """Valid enum values based on current model."""
    return ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"]


@pytest.fixture
def valid_configuration():
    """Valid configuration data."""
    return {"key1": "value1", "key2": 42}


@pytest.fixture
def valid_description():
    """Valid description data."""
    return "Test integration description"


@pytest.fixture
def valid_enabled():
    """Valid enabled data."""
    return True


@pytest.fixture
def valid_type():
    """Valid type data."""
    return "test_type"


def test_constructor_exists_and_accepts_all_known_parameters(
    valid_category_values,
    valid_configuration,
    valid_description,
    valid_enabled,
    valid_type,
):
    """Test that constructor exists and accepts all known parameters."""
    # Test default constructor (all None)
    model = IntegrationUpdate()
    assert isinstance(model, IntegrationUpdate)

    # Test constructor with all known parameters
    model = IntegrationUpdate(
        category=valid_category_values[0],
        configuration=valid_configuration,
        description=valid_description,
        enabled=valid_enabled,
        type=valid_type,
    )
    assert isinstance(model, IntegrationUpdate)


def test_all_required_fields_exist():
    """Test that all expected fields exist as properties."""
    model = IntegrationUpdate()

    # Verify all known fields exist
    required_fields = ["category", "configuration", "description", "enabled", "type"]
    for field in required_fields:
        assert hasattr(model, field), f"Field '{field}' must exist"
        assert callable(
            getattr(model.__class__, field).fget
        ), f"Field '{field}' must be readable"
        assert callable(
            getattr(model.__class__, field).fset
        ), f"Field '{field}' must be writable"


def test_field_types_unchanged(
    valid_category_values,
    valid_configuration,
    valid_description,
    valid_enabled,
    valid_type,
):
    """Test that field types remain consistent."""
    model = IntegrationUpdate()

    # Test category (str)
    model.category = valid_category_values[0]
    assert isinstance(model.category, str)

    # Test configuration (dict)
    model.configuration = valid_configuration
    assert isinstance(model.configuration, dict)

    # Test description (str)
    model.description = valid_description
    assert isinstance(model.description, str)

    # Test enabled (bool)
    model.enabled = valid_enabled
    assert isinstance(model.enabled, bool)

    # Test type (str)
    model.type = valid_type
    assert isinstance(model.type, str)


def test_category_enum_validation_unchanged(valid_category_values):
    """Test that category enum validation rules remain the same."""
    model = IntegrationUpdate()

    # Test all known valid values still work
    for valid_value in valid_category_values:
        model.category = valid_value
        assert model.category == valid_value

    # Test invalid values still raise ValueError
    invalid_values = ["INVALID", "invalid", "", "api", "Api"]
    for invalid_value in invalid_values:
        with pytest.raises(ValueError, match="Invalid"):
            model.category = invalid_value


def test_category_enum_all_original_values_supported():
    """Test that all original enum values are still supported."""
    model = IntegrationUpdate()

    # These specific values must always work (backward compatibility)
    original_values = ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"]

    for value in original_values:
        model.category = value
        assert model.category == value


def test_field_assignment_behavior_unchanged():
    """Test that field assignment behavior remains consistent."""
    model = IntegrationUpdate()

    # Test None assignment for fields that allow it
    model.configuration = None
    assert model.configuration is None

    model.description = None
    assert model.description is None

    model.enabled = None
    assert model.enabled is None

    model.type = None
    assert model.type is None

    # Test that category validation still prevents None assignment
    with pytest.raises(ValueError, match="Invalid"):
        model.category = None


def test_constructor_parameter_names_unchanged():
    """Test that constructor parameter names haven't changed."""
    # This should work without TypeError
    model = IntegrationUpdate(
        category="API",
        configuration={"test": "value"},
        description="test desc",
        enabled=True,
        type="test_type",
    )
    assert model is not None


def test_swagger_metadata_exists():
    """Test that required swagger metadata still exists."""
    # These class attributes must exist for backward compatibility
    assert hasattr(IntegrationUpdate, "swagger_types")
    assert hasattr(IntegrationUpdate, "attribute_map")

    # Verify known fields are in swagger_types
    swagger_types = IntegrationUpdate.swagger_types
    expected_fields = ["category", "configuration", "description", "enabled", "type"]

    for field in expected_fields:
        assert field in swagger_types, f"Field '{field}' must exist in swagger_types"


def test_object_methods_exist():
    """Test that required object methods still exist."""
    model = IntegrationUpdate()

    # These methods must exist for backward compatibility
    required_methods = ["to_dict", "to_str", "__repr__", "__eq__", "__ne__"]

    for method in required_methods:
        assert hasattr(model, method), f"Method '{method}' must exist"
        assert callable(getattr(model, method)), f"'{method}' must be callable"


def test_to_dict_method_behavior():
    """Test that to_dict method behavior is preserved."""
    model = IntegrationUpdate(
        category="API",
        configuration={"test": "value"},
        description="test desc",
        enabled=True,
        type="test_type",
    )

    result = model.to_dict()
    assert isinstance(result, dict)

    # Verify all set fields appear in dict
    assert result["category"] == "API"
    assert result["configuration"] == {"test": "value"}
    assert result["description"] == "test desc"
    assert result["enabled"] is True
    assert result["type"] == "test_type"


def test_constructor_with_none_values():
    """Test that constructor accepts None for all parameters."""
    # Constructor should accept None for all parameters (no validation during init)
    model = IntegrationUpdate(
        category=None, configuration=None, description=None, enabled=None, type=None
    )

    # Values should be None since constructor doesn't validate
    assert model.category is None
    assert model.configuration is None
    assert model.description is None
    assert model.enabled is None
    assert model.type is None


def test_equality_comparison():
    """Test that object equality comparison still works."""
    model1 = IntegrationUpdate(category="API", enabled=True)
    model2 = IntegrationUpdate(category="API", enabled=True)
    model3 = IntegrationUpdate(category="AI_MODEL", enabled=True)

    # Equal objects should be equal
    assert model1 == model2
    assert not (model1 != model2)

    # Different objects should not be equal
    assert model1 != model3
    assert model1 != model3


def test_configuration_dict_type_handling():
    """Test that configuration field properly handles dict types."""
    model = IntegrationUpdate()

    # Test various dict configurations
    test_configs = [
        {},
        {"string_key": "string_value"},
        {"int_key": 42},
        {"nested": {"key": "value"}},
        {"mixed": ["list", {"nested": "dict"}, 123]},
    ]

    for config in test_configs:
        model.configuration = config
        assert model.configuration == config


def test_boolean_field_handling():
    """Test that enabled field properly handles boolean values."""
    model = IntegrationUpdate()

    # Test boolean values
    model.enabled = True
    assert model.enabled is True

    model.enabled = False
    assert model.enabled is False
