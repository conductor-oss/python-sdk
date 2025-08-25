import pytest

from conductor.client.adapters.models.integration_api_adapter import IntegrationApiAdapter


@pytest.fixture
def mock_tag(mocker):
    """Mock TagObject for testing."""
    mock_tag = mocker.Mock()
    mock_tag.to_dict.return_value = {"name": "test-tag"}
    return mock_tag


@pytest.fixture
def valid_data(mock_tag):
    """Valid data for testing."""
    return {
        "api": "test-api",
        "configuration": {"key": "value", "timeout": 30},
        "created_by": "test-user",
        "created_on": 1640995200000,  # Unix timestamp
        "description": "Test integration description",
        "enabled": True,
        "integration_name": "test-integration",
        "tags": [mock_tag],
        "updated_by": "update-user",
        "updated_on": 1641081600000,
    }


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (current behavior)."""
    integration = IntegrationApiAdapter()

    # All fields should be None initially
    assert integration.api is None
    assert integration.configuration is None
    assert integration.created_by is None
    assert integration.created_on is None
    assert integration.description is None
    assert integration.enabled is None
    assert integration.integration_name is None
    assert integration.tags is None
    assert integration.updated_by is None
    assert integration.updated_on is None


def test_constructor_with_all_parameters(valid_data, mock_tag):
    """Test constructor with all known parameters."""
    integration = IntegrationApiAdapter(**valid_data)

    # Verify all fields are set correctly
    assert integration.api == "test-api"
    assert integration.configuration == {"key": "value", "timeout": 30}
    assert integration.created_by == "test-user"
    assert integration.created_on == 1640995200000
    assert integration.description == "Test integration description"
    assert integration.enabled is True
    assert integration.integration_name == "test-integration"
    assert integration.tags == [mock_tag]
    assert integration.updated_by == "update-user"
    assert integration.updated_on == 1641081600000


def test_constructor_with_partial_parameters():
    """Test constructor with subset of parameters."""
    partial_data = {
        "api": "partial-api",
        "enabled": False,
        "integration_name": "partial-integration",
    }

    integration = IntegrationApiAdapter(**partial_data)

    # Specified fields should be set
    assert integration.api == "partial-api"
    assert integration.enabled is False
    assert integration.integration_name == "partial-integration"

    # Unspecified fields should be None
    assert integration.configuration is None
    assert integration.created_by is None
    assert integration.description is None


def test_field_existence_and_types(valid_data):
    """Test that all expected fields exist and have correct types."""
    integration = IntegrationApiAdapter(**valid_data)

    # Test field existence and types
    assert isinstance(integration.api, str)
    assert isinstance(integration.configuration, dict)
    assert isinstance(integration.created_by, str)
    assert isinstance(integration.created_on, int)
    assert isinstance(integration.description, str)
    assert isinstance(integration.enabled, bool)
    assert isinstance(integration.integration_name, str)
    assert isinstance(integration.tags, list)
    assert isinstance(integration.updated_by, str)
    assert isinstance(integration.updated_on, int)


def test_property_getters(valid_data, mock_tag):
    """Test that all property getters work correctly."""
    integration = IntegrationApiAdapter(**valid_data)

    # Test getters return expected values
    assert integration.api == "test-api"
    assert integration.configuration == {"key": "value", "timeout": 30}
    assert integration.created_by == "test-user"
    assert integration.created_on == 1640995200000
    assert integration.description == "Test integration description"
    assert integration.enabled is True
    assert integration.integration_name == "test-integration"
    assert integration.tags == [mock_tag]
    assert integration.updated_by == "update-user"
    assert integration.updated_on == 1641081600000


def test_property_setters(mock_tag):
    """Test that all property setters work correctly."""
    integration = IntegrationApiAdapter()

    # Test setting all properties
    integration.api = "new-api"
    integration.configuration = {"new_key": "new_value"}
    integration.created_by = "new-creator"
    integration.created_on = 9999999999
    integration.description = "New description"
    integration.enabled = False
    integration.integration_name = "new-integration"
    integration.tags = [mock_tag]
    integration.updated_by = "new-updater"
    integration.updated_on = 8888888888

    # Verify values were set
    assert integration.api == "new-api"
    assert integration.configuration == {"new_key": "new_value"}
    assert integration.created_by == "new-creator"
    assert integration.created_on == 9999999999
    assert integration.description == "New description"
    assert integration.enabled is False
    assert integration.integration_name == "new-integration"
    assert integration.tags == [mock_tag]
    assert integration.updated_by == "new-updater"
    assert integration.updated_on == 8888888888


def test_none_value_assignment(valid_data):
    """Test that None can be assigned to all fields."""
    integration = IntegrationApiAdapter(**valid_data)

    # Set all fields to None
    integration.api = None
    integration.configuration = None
    integration.created_by = None
    integration.created_on = None
    integration.description = None
    integration.enabled = None
    integration.integration_name = None
    integration.tags = None
    integration.updated_by = None
    integration.updated_on = None

    # Verify all fields are None
    assert integration.api is None
    assert integration.configuration is None
    assert integration.created_by is None
    assert integration.created_on is None
    assert integration.description is None
    assert integration.enabled is None
    assert integration.integration_name is None
    assert integration.tags is None
    assert integration.updated_by is None
    assert integration.updated_on is None


def test_swagger_types_structure():
    """Test that swagger_types dictionary contains expected field definitions."""
    expected_swagger_types = {
        'api': 'str',
        'configuration': 'dict(str, object)',
        'create_time': 'int',
        'created_by': 'str',
        'description': 'str',
        'enabled': 'bool',
        'integration_name': 'str',
        'owner_app': 'str',
        'tags': 'list[Tag]',
        'update_time': 'int',
        'updated_by': 'str'
    }

    assert IntegrationApiAdapter.swagger_types == expected_swagger_types


def test_attribute_map_structure():
    """Test that attribute_map dictionary contains expected mappings."""
    expected_attribute_map = {
        'api': 'api',
        'configuration': 'configuration',
        'create_time': 'createTime',
        'created_by': 'createdBy',
        'description': 'description',
        'enabled': 'enabled',
        'integration_name': 'integrationName',
        'owner_app': 'ownerApp',
        'tags': 'tags',
        'update_time': 'updateTime',
        'updated_by': 'updatedBy'
    }

    assert IntegrationApiAdapter.attribute_map == expected_attribute_map


def test_to_dict_method(valid_data):
    """Test that to_dict method works and returns expected structure."""
    integration = IntegrationApiAdapter(**valid_data)
    result_dict = integration.to_dict()

    # Verify dictionary contains expected keys
    expected_keys = {
        "api",
        "configuration",
        "created_by",
        "create_time",
        "description",
        "enabled",
        "integration_name",
        "tags",
        "updated_by",
        "update_time",
        "owner_app",
    }

    assert set(result_dict.keys()) == expected_keys

    # Verify values are correctly converted
    assert result_dict["api"] == "test-api"
    assert result_dict["configuration"] == {"key": "value", "timeout": 30}
    assert result_dict["enabled"] is True


def test_to_str_method():
    """Test that to_str method works."""
    integration = IntegrationApiAdapter(api="test", enabled=True)
    str_repr = integration.to_str()

    # Should return a string representation
    assert isinstance(str_repr, str)
    assert "test" in str_repr


def test_repr_method():
    """Test that __repr__ method works."""
    integration = IntegrationApiAdapter(api="test", enabled=True)
    repr_str = repr(integration)

    # Should return a string representation
    assert isinstance(repr_str, str)
    assert "test" in repr_str


def test_equality_comparison(valid_data):
    """Test that equality comparison works correctly."""
    integration1 = IntegrationApiAdapter(**valid_data)
    integration2 = IntegrationApiAdapter(**valid_data)
    integration3 = IntegrationApiAdapter(api="different")

    # Same data should be equal
    assert integration1 == integration2

    # Different data should not be equal
    assert integration1 != integration3

    # Different type should not be equal
    assert integration1 != "not an integration"


def test_inequality_comparison(valid_data):
    """Test that inequality comparison works correctly."""
    integration1 = IntegrationApiAdapter(**valid_data)
    integration2 = IntegrationApiAdapter(api="different")

    # Different objects should be not equal
    assert integration1 != integration2
    assert integration1 != integration2


def test_discriminator_attribute():
    """Test that discriminator attribute exists and is None."""
    integration = IntegrationApiAdapter()
    assert integration.discriminator is None


def test_configuration_dict_flexibility():
    """Test that configuration field accepts various dict structures."""
    configs = [
        {},  # Empty dict
        {"simple": "value"},  # Simple key-value
        {"nested": {"key": "value"}},  # Nested dict
        {"list_value": [1, 2, 3]},  # Dict with list
        {"mixed": {"str": "value", "int": 42, "bool": True}},  # Mixed types
    ]

    for config in configs:
        integration = IntegrationApiAdapter(configuration=config)
        assert integration.configuration == config


def test_tags_list_handling(mocker):
    """Test that tags field properly handles list of objects."""
    # Empty list
    integration = IntegrationApiAdapter(tags=[])
    assert integration.tags == []

    # List with mock objects
    mock_tags = [mocker.Mock(), mocker.Mock()]
    integration = IntegrationApiAdapter(tags=mock_tags)
    assert integration.tags == mock_tags
