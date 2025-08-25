from conductor.client.adapters.models.integration_api_update_adapter import IntegrationApiUpdateAdapter


def test_constructor_with_no_arguments():
    """Test that model can be instantiated with no arguments (current behavior)."""
    model = IntegrationApiUpdateAdapter()

    # Verify original fields are initialized to None (current behavior)
    assert model.configuration is None
    assert model.description is None
    assert model.enabled is None


def test_constructor_with_all_original_arguments():
    """Test that model can be instantiated with all original arguments."""
    config = {"key": "value", "timeout": 30}
    description = "Test integration"
    enabled = True

    model = IntegrationApiUpdateAdapter(
        configuration=config, description=description, enabled=enabled
    )

    assert model.configuration == config
    assert model.description == description
    assert model.enabled == enabled


def test_constructor_with_partial_arguments():
    """Test that model can be instantiated with partial arguments."""
    # Test with only description
    model1 = IntegrationApiUpdateAdapter(description="Test desc")
    assert model1.description == "Test desc"
    assert model1.configuration is None
    assert model1.enabled is None

    # Test with only enabled
    model2 = IntegrationApiUpdateAdapter(enabled=False)
    assert model2.enabled is False
    assert model2.configuration is None
    assert model2.description is None


def test_original_required_fields_exist():
    """Test that all original expected fields exist on the model."""
    model = IntegrationApiUpdateAdapter()

    # Verify original required attributes exist
    assert hasattr(model, "configuration")
    assert hasattr(model, "description")
    assert hasattr(model, "enabled")

    # Verify swagger metadata exists
    assert hasattr(model, "swagger_types")
    assert hasattr(model, "attribute_map")


def test_original_field_types_preserved():
    """Test that original field types remain as expected."""
    model = IntegrationApiUpdateAdapter()

    # Verify original fields are still present with correct types
    original_expected_types = {
        "configuration": "dict(str, object)",
        "description": "str",
        "enabled": "bool",
    }

    # Check that all original types are preserved
    for field, expected_type in original_expected_types.items():
        assert field in model.swagger_types
        assert model.swagger_types[field] == expected_type


def test_original_attribute_map_preserved():
    """Test that original attribute mapping is preserved."""
    model = IntegrationApiUpdateAdapter()

    # Verify original mappings are still present
    original_expected_map = {
        "configuration": "configuration",
        "description": "description",
        "enabled": "enabled",
    }

    # Check that all original mappings are preserved
    for field, expected_mapping in original_expected_map.items():
        assert field in model.attribute_map
        assert model.attribute_map[field] == expected_mapping


def test_configuration_field_behavior():
    """Test configuration field accepts dict types and None."""
    model = IntegrationApiUpdateAdapter()

    # Test None assignment (default)
    model.configuration = None
    assert model.configuration is None

    # Test dict assignment
    config_dict = {"api_key": "test123", "timeout": 60}
    model.configuration = config_dict
    assert model.configuration == config_dict

    # Test empty dict
    model.configuration = {}
    assert model.configuration == {}


def test_description_field_behavior():
    """Test description field accepts string types and None."""
    model = IntegrationApiUpdateAdapter()

    # Test None assignment (default)
    model.description = None
    assert model.description is None

    # Test string assignment
    model.description = "Integration description"
    assert model.description == "Integration description"

    # Test empty string
    model.description = ""
    assert model.description == ""


def test_enabled_field_behavior():
    """Test enabled field accepts boolean types and None."""
    model = IntegrationApiUpdateAdapter()

    # Test None assignment (default)
    model.enabled = None
    assert model.enabled is None

    # Test boolean assignments
    model.enabled = True
    assert model.enabled is True

    model.enabled = False
    assert model.enabled is False


def test_property_getters():
    """Test that all original property getters work correctly."""
    config = {"test": "value"}
    description = "Test description"
    enabled = True

    model = IntegrationApiUpdateAdapter(
        configuration=config, description=description, enabled=enabled
    )

    # Test getters return correct values
    assert model.configuration == config
    assert model.description == description
    assert model.enabled == enabled


def test_property_setters():
    """Test that all original property setters work correctly."""
    model = IntegrationApiUpdateAdapter()

    # Test configuration setter
    config = {"api": "test"}
    model.configuration = config
    assert model.configuration == config

    # Test description setter
    desc = "New description"
    model.description = desc
    assert model.description == desc

    # Test enabled setter
    model.enabled = True
    assert model.enabled is True


def test_to_dict_contains_original_fields():
    """Test that to_dict method contains all original fields."""
    config = {"key": "value"}
    description = "Test integration"
    enabled = True

    model = IntegrationApiUpdateAdapter(
        configuration=config, description=description, enabled=enabled
    )

    result_dict = model.to_dict()

    # Verify original fields are present with correct values
    assert result_dict["configuration"] == config
    assert result_dict["description"] == description
    assert result_dict["enabled"] == enabled


def test_to_dict_with_none_values_includes_original_fields():
    """Test to_dict method with None values includes original fields."""
    model = IntegrationApiUpdateAdapter()
    result_dict = model.to_dict()

    # Verify original fields are present
    assert "configuration" in result_dict
    assert "description" in result_dict
    assert "enabled" in result_dict

    # Verify they have None values
    assert result_dict["configuration"] is None
    assert result_dict["description"] is None
    assert result_dict["enabled"] is None


def test_to_str_method():
    """Test that to_str method works correctly."""
    model = IntegrationApiUpdateAdapter(description="Test")
    str_result = model.to_str()

    # Should return a formatted string representation
    assert isinstance(str_result, str)
    assert "description" in str_result
    assert "Test" in str_result


def test_repr_method():
    """Test that __repr__ method works correctly."""
    model = IntegrationApiUpdateAdapter(enabled=True)
    repr_result = repr(model)

    # Should return same as to_str()
    assert repr_result == model.to_str()


def test_equality_comparison():
    """Test that equality comparison works correctly."""
    model1 = IntegrationApiUpdateAdapter(
        configuration={"key": "value"}, description="Test", enabled=True
    )

    model2 = IntegrationApiUpdateAdapter(
        configuration={"key": "value"}, description="Test", enabled=True
    )

    model3 = IntegrationApiUpdateAdapter(
        configuration={"key": "different"}, description="Test", enabled=True
    )

    # Test equality
    assert model1 == model2
    assert model1 != model3

    # Test inequality with different types
    assert model1 != "not a model"
    assert model1 is not None


def test_inequality_comparison():
    """Test that inequality comparison works correctly."""
    model1 = IntegrationApiUpdateAdapter(description="Test1")
    model2 = IntegrationApiUpdateAdapter(description="Test2")

    assert model1 != model2


def test_discriminator_attribute():
    """Test that discriminator attribute exists and is None."""
    model = IntegrationApiUpdateAdapter()
    assert hasattr(model, "discriminator")
    assert model.discriminator is None


def test_original_private_attributes_exist():
    """Test that original private attributes are properly initialized."""
    model = IntegrationApiUpdateAdapter()

    # Verify original private attributes exist
    assert hasattr(model, "_configuration")
    assert hasattr(model, "_description")
    assert hasattr(model, "_enabled")


def test_field_assignment_independence():
    """Test that field assignments are independent."""
    model = IntegrationApiUpdateAdapter()

    # Set one field and verify others remain None
    model.description = "Test description"
    assert model.description == "Test description"
    assert model.configuration is None
    assert model.enabled is None

    # Set another field and verify first remains
    model.enabled = True
    assert model.description == "Test description"
    assert model.enabled is True
    assert model.configuration is None


def test_original_functionality_unchanged():
    """Test that original functionality works exactly as before."""
    # Test that we can still create instances with only original fields
    model = IntegrationApiUpdateAdapter(
        configuration={"test": "value"}, description="Original behavior", enabled=True
    )

    # Original functionality should work exactly the same
    assert model.configuration == {"test": "value"}
    assert model.description == "Original behavior"
    assert model.enabled is True

    # Test that original constructor patterns still work
    model2 = IntegrationApiUpdateAdapter()
    assert model2.configuration is None
    assert model2.description is None
    assert model2.enabled is None


def test_backward_compatible_serialization():
    """Test that serialization maintains compatibility for SDK usage."""
    # Create model with only original fields set
    model = IntegrationApiUpdateAdapter(
        configuration={"api_key": "test"}, description="Test integration", enabled=True
    )

    result_dict = model.to_dict()

    # Should contain original fields with correct values
    assert result_dict["configuration"] == {"api_key": "test"}
    assert result_dict["description"] == "Test integration"
    assert result_dict["enabled"] is True

    # Additional fields may be present but shouldn't break existing logic
    # that only cares about the original fields
    for key in ["configuration", "description", "enabled"]:
        assert key in result_dict
