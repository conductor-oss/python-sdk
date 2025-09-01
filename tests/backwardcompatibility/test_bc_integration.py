import pytest
from conductor.client.http.models import Integration


@pytest.fixture
def valid_category_values():
    return ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"]


@pytest.fixture
def sample_config():
    return {"key1": "value1", "key2": 123}


@pytest.fixture
def sample_tags():
    return []  # Assuming TagObject list, empty for simplicity


def test_constructor_accepts_all_existing_parameters(sample_config, sample_tags):
    integration = Integration(
        category="API",
        configuration=sample_config,
        created_by="test_user",
        created_on=1234567890,
        description="Test integration",
        enabled=True,
        models_count=5,
        name="test_integration",
        tags=sample_tags,
        type="webhook",
        updated_by="test_user2",
        updated_on=1234567891,
    )
    assert integration.category == "API"
    assert integration.configuration == sample_config
    assert integration.created_by == "test_user"
    assert integration.created_on == 1234567890
    assert integration.description == "Test integration"
    assert integration.enabled is True
    assert integration.models_count == 5
    assert integration.name == "test_integration"
    assert integration.tags == sample_tags
    assert integration.type == "webhook"
    assert integration.updated_by == "test_user2"
    assert integration.updated_on == 1234567891


def test_constructor_with_none_values():
    integration = Integration()
    assert integration.category is None
    assert integration.configuration is None
    assert integration.created_by is None
    assert integration.created_on is None
    assert integration.description is None
    assert integration.enabled is None
    assert integration.models_count is None
    assert integration.name is None
    assert integration.tags is None
    assert integration.type is None
    assert integration.updated_by is None
    assert integration.updated_on is None


def test_all_existing_properties_exist():
    integration = Integration()
    expected_properties = [
        "category",
        "configuration",
        "created_by",
        "created_on",
        "description",
        "enabled",
        "models_count",
        "name",
        "tags",
        "type",
        "updated_by",
        "updated_on",
    ]
    for prop in expected_properties:
        assert hasattr(integration, prop), f"Property {prop} should exist"
        getattr(integration, prop)


def test_all_existing_setters_exist_and_work(sample_config, sample_tags):
    integration = Integration()
    integration.category = "API"
    integration.configuration = sample_config
    integration.created_by = "test_user"
    integration.created_on = 1234567890
    integration.description = "Test description"
    integration.enabled = True
    integration.models_count = 10
    integration.name = "test_name"
    integration.tags = sample_tags
    integration.type = "webhook"
    integration.updated_by = "test_user2"
    integration.updated_on = 1234567891
    assert integration.category == "API"
    assert integration.configuration == sample_config
    assert integration.created_by == "test_user"
    assert integration.created_on == 1234567890
    assert integration.description == "Test description"
    assert integration.enabled is True
    assert integration.models_count == 10
    assert integration.name == "test_name"
    assert integration.tags == sample_tags
    assert integration.type == "webhook"
    assert integration.updated_by == "test_user2"
    assert integration.updated_on == 1234567891


def test_category_enum_validation_existing_values(valid_category_values):
    for value in valid_category_values:
        integration = Integration(category=value)
        assert integration.category == value


def test_category_enum_validation_rejects_invalid_values():
    integration = Integration()
    with pytest.raises(ValueError, match="Invalid"):
        integration.category = "INVALID_CATEGORY"


def test_field_types_unchanged():
    """Test that field types haven't changed from expected types."""
    integration = Integration(
        category="API",
        configuration={"key": "value"},
        created_by="user",
        created_on=123456789,
        description="desc",
        enabled=True,
        models_count=5,
        name="name",
        tags=[],
        type="type",
        updated_by="user2",
        updated_on=123456790,
    )

    # Test expected types
    assert isinstance(integration.category, str)
    assert isinstance(integration.configuration, dict)
    assert isinstance(integration.created_by, str)
    assert isinstance(integration.create_time, int)
    assert isinstance(integration.description, str)
    assert isinstance(integration.enabled, bool)
    assert isinstance(integration.models_count, int)
    assert isinstance(integration.name, str)
    assert isinstance(integration.tags, list)
    assert isinstance(integration.type, str)
    assert isinstance(integration.updated_by, str)
    assert isinstance(integration.update_time, int)


def test_swagger_types_mapping_unchanged():
    assert isinstance(Integration.swagger_types, dict)


def test_attribute_map_unchanged():
    expected_attribute_map = {
        "apis": "apis",
        "category": "category",
        "configuration": "configuration",
        "create_time": "createTime",
        "created_by": "createdBy",
        "description": "description",
        "enabled": "enabled",
        "models_count": "modelsCount",
        "name": "name",
        "tags": "tags",
        "type": "type",
        "updated_by": "updatedBy",
        "update_time": "updateTime",
        "owner_app": "ownerApp",
    }
    for key, expected_json_key in expected_attribute_map.items():
        assert key in Integration.attribute_map, f"attribute_map should contain {key}"
        assert (
            Integration.attribute_map[key] == expected_json_key
        ), f"attribute_map[{key}] should be {expected_json_key}"


def test_to_dict_method_exists_and_works(sample_config, sample_tags):
    integration = Integration(
        category="API",
        configuration=sample_config,
        created_by="test_user",
        created_on=1234567890,
        description="Test integration",
        enabled=True,
        models_count=5,
        name="test_integration",
        tags=sample_tags,
        type="webhook",
        updated_by="test_user2",
        updated_on=1234567891,
    )
    result = integration.to_dict()
    assert isinstance(result, dict)
    assert result["category"] == "API"
    assert result["configuration"] == sample_config
    assert result["created_by"] == "test_user"
    assert result["create_time"] == 1234567890
    assert result["description"] == "Test integration"
    assert result["enabled"] is True
    assert result["models_count"] == 5
    assert result["name"] == "test_integration"
    assert result["tags"] == sample_tags
    assert result["type"] == "webhook"
    assert result["updated_by"] == "test_user2"
    assert result["update_time"] == 1234567891


def test_to_str_method_exists_and_works(sample_config, sample_tags):
    integration = Integration(
        category="API",
        configuration=sample_config,
        created_by="test_user",
        created_on=1234567890,
        description="Test integration",
        enabled=True,
        models_count=5,
        name="test_integration",
        tags=sample_tags,
        type="webhook",
        updated_by="test_user2",
        updated_on=1234567891,
    )
    result = integration.to_str()
    assert isinstance(result, str)
    assert "API" in result
    assert "test_integration" in result


def test_equality_methods_exist_and_work(sample_config, sample_tags):
    integration1 = Integration(
        category="API",
        configuration=sample_config,
        created_by="test_user",
        created_on=1234567890,
        description="Test integration",
        enabled=True,
        models_count=5,
        name="test_integration",
        tags=sample_tags,
        type="webhook",
        updated_by="test_user2",
        updated_on=1234567891,
    )
    integration2 = Integration(
        category="API",
        configuration=sample_config,
        created_by="test_user",
        created_on=1234567890,
        description="Test integration",
        enabled=True,
        models_count=5,
        name="test_integration",
        tags=sample_tags,
        type="webhook",
        updated_by="test_user2",
        updated_on=1234567891,
    )
    integration3 = Integration(
        category="AI_MODEL",
        configuration=sample_config,
        created_by="test_user",
        created_on=1234567890,
        description="Test integration",
        enabled=True,
        models_count=5,
        name="test_integration",
        tags=sample_tags,
        type="webhook",
        updated_by="test_user2",
        updated_on=1234567891,
    )
    assert integration1 == integration2
    assert integration1 != integration3
    assert not (integration1 != integration2)
    assert integration1 != integration3


def test_repr_method_exists_and_works(sample_config, sample_tags):
    integration = Integration(
        category="API",
        configuration=sample_config,
        created_by="test_user",
        created_on=1234567890,
        description="Test integration",
        enabled=True,
        models_count=5,
        name="test_integration",
        tags=sample_tags,
        type="webhook",
        updated_by="test_user2",
        updated_on=1234567891,
    )
    repr_str = repr(integration)
    assert isinstance(repr_str, str)
    assert "API" in repr_str
    assert "test_integration" in repr_str


def test_none_assignment_behavior():
    integration = Integration(category="API", name="test")

    with pytest.raises(ValueError, match="Invalid"):
        integration.category = None

    integration.configuration = None
    integration.created_by = None
    integration.created_on = None
    integration.description = None
    integration.enabled = None
    integration.models_count = None
    integration.name = None
    integration.tags = None
    integration.type = None
    integration.updated_by = None
    integration.updated_on = None

    assert integration.configuration is None
    assert integration.created_by is None
    assert integration.created_on is None
    assert integration.description is None
    assert integration.enabled is None
    assert integration.models_count is None
    assert integration.name is None
    assert integration.tags is None
    assert integration.type is None
    assert integration.updated_by is None
    assert integration.updated_on is None


def test_configuration_accepts_dict_with_mixed_types():
    integration = Integration()
    config = {"a": 1, "b": "str", "c": [1, 2, 3], "d": {"nested": True}}
    integration.configuration = config
    assert integration.configuration == config
