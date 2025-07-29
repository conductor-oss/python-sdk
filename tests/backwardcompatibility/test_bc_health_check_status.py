import pytest
from conductor.client.http.models.health_check_status import HealthCheckStatus


@pytest.fixture
def mock_health_1(mocker):
    """Mock Health object for testing."""
    mock_health = mocker.Mock()
    mock_health.to_dict.return_value = {"status": "UP", "component": "database"}
    return mock_health


@pytest.fixture
def mock_health_2(mocker):
    """Mock Health object for testing."""
    mock_health = mocker.Mock()
    mock_health.to_dict.return_value = {"status": "DOWN", "component": "cache"}
    return mock_health


def test_constructor_with_no_parameters():
    """Test that constructor works with no parameters (all optional)."""
    # This should work as all parameters are optional
    status = HealthCheckStatus()

    # Verify all fields are properly initialized
    assert status.health_results is None
    assert status.suppressed_health_results is None
    assert status.healthy is None
    assert status.discriminator is None


def test_constructor_with_all_parameters(mock_health_1, mock_health_2):
    """Test that constructor works with all parameters provided."""
    health_results = [mock_health_1]
    suppressed_results = [mock_health_2]
    healthy = True

    status = HealthCheckStatus(
        health_results=health_results,
        suppressed_health_results=suppressed_results,
        healthy=healthy,
    )

    # Verify all fields are properly set
    assert status.health_results == health_results
    assert status.suppressed_health_results == suppressed_results
    assert status.healthy == healthy


def test_constructor_with_partial_parameters(mock_health_1):
    """Test that constructor works with partial parameters."""
    # Test with only health_results
    status1 = HealthCheckStatus(health_results=[mock_health_1])
    assert status1.health_results == [mock_health_1]
    assert status1.suppressed_health_results is None
    assert status1.healthy is None

    # Test with only healthy flag
    status2 = HealthCheckStatus(healthy=False)
    assert status2.health_results is None
    assert status2.suppressed_health_results is None
    assert status2.healthy is False


def test_required_fields_exist():
    """Test that all expected fields exist and are accessible."""
    status = HealthCheckStatus()

    # Verify all required fields exist as properties
    assert hasattr(status, "health_results")
    assert hasattr(status, "suppressed_health_results")
    assert hasattr(status, "healthy")

    # Verify internal attributes exist
    assert hasattr(status, "_health_results")
    assert hasattr(status, "_suppressed_health_results")
    assert hasattr(status, "_healthy")
    assert hasattr(status, "discriminator")


def test_field_types_unchanged():
    """Test that field types haven't changed from expected types."""
    # Verify swagger_types structure hasn't changed
    expected_swagger_types = {
        "health_results": "list[Health]",
        "suppressed_health_results": "list[Health]",
        "healthy": "bool",
    }

    assert HealthCheckStatus.swagger_types == expected_swagger_types


def test_attribute_mapping_unchanged():
    """Test that attribute mapping hasn't changed."""
    expected_attribute_map = {
        "health_results": "healthResults",
        "suppressed_health_results": "suppressedHealthResults",
        "healthy": "healthy",
    }

    assert HealthCheckStatus.attribute_map == expected_attribute_map


def test_property_getters_work(mock_health_1, mock_health_2):
    """Test that property getters work correctly."""
    status = HealthCheckStatus(
        health_results=[mock_health_1],
        suppressed_health_results=[mock_health_2],
        healthy=True,
    )

    # Test all property getters
    assert status.health_results == [mock_health_1]
    assert status.suppressed_health_results == [mock_health_2]
    assert status.healthy is True


def test_property_setters_work(mock_health_1, mock_health_2):
    """Test that property setters work correctly."""
    status = HealthCheckStatus()

    # Test all property setters
    status.health_results = [mock_health_1]
    assert status.health_results == [mock_health_1]

    status.suppressed_health_results = [mock_health_2]
    assert status.suppressed_health_results == [mock_health_2]

    status.healthy = False
    assert status.healthy is False


def test_none_values_handling():
    """Test that None values are handled correctly."""
    status = HealthCheckStatus(
        health_results=[mock_health_1],
        suppressed_health_results=[mock_health_2],
        healthy=True,
    )

    # Test setting to None
    status.health_results = None
    status.suppressed_health_results = None
    status.healthy = None

    assert status.health_results is None
    assert status.suppressed_health_results is None
    assert status.healthy is None


def test_to_dict_method_exists(mock_health_1, mock_health_2):
    """Test that to_dict method exists and works correctly."""
    status = HealthCheckStatus(health_results=[mock_health_1], healthy=True)

    assert hasattr(status, "to_dict")
    assert callable(getattr(status, "to_dict"))
    result = status.to_dict()

    assert isinstance(result, dict)


def test_to_str_method_exists(mock_health_1):
    """Test that to_str method exists and works."""
    status = HealthCheckStatus(health_results=[mock_health_1], healthy=True)

    assert hasattr(status, "to_str")
    result = status.to_str()
    assert isinstance(result, str)


def test_repr_method_exists(mock_health_1):
    """Test that __repr__ method exists and works."""
    status = HealthCheckStatus(health_results=[mock_health_1], healthy=True)

    repr_str = repr(status)
    assert isinstance(repr_str, str)


def test_equality_methods_exist(mock_health_1):
    """Test that equality methods work correctly."""
    status1 = HealthCheckStatus(health_results=[mock_health_1], healthy=True)
    status2 = HealthCheckStatus(health_results=[mock_health_1], healthy=True)
    status3 = HealthCheckStatus(health_results=[mock_health_1], healthy=False)

    # Test equality
    assert status1 == status2
    assert status1 != status3

    # Test inequality
    assert not (status1 != status2)
    assert status1 != status3


def test_class_attributes_unchanged():
    """Test that class-level attributes haven't changed."""
    # Test swagger_types is a dict
    assert hasattr(HealthCheckStatus, "swagger_types")
    assert isinstance(HealthCheckStatus.swagger_types, dict)

    # Test attribute_map is a dict
    assert hasattr(HealthCheckStatus, "attribute_map")
    assert isinstance(HealthCheckStatus.attribute_map, dict)


def test_constructor_parameter_order_unchanged(mock_health_1, mock_health_2):
    """Test that constructor parameter order hasn't changed."""
    # Test with keyword arguments in different orders
    status1 = HealthCheckStatus(
        health_results=[mock_health_1],
        suppressed_health_results=[mock_health_2],
        healthy=True,
    )
    status2 = HealthCheckStatus(
        healthy=True,
        health_results=[mock_health_1],
        suppressed_health_results=[mock_health_2],
    )

    # Both should produce the same result
    assert status1.health_results == status2.health_results
    assert status1.suppressed_health_results == status2.suppressed_health_results
    assert status1.healthy == status2.healthy


def test_discriminator_field_exists():
    """Test that discriminator field exists and is None."""
    status = HealthCheckStatus()
    assert hasattr(status, "discriminator")
    assert status.discriminator is None


# Field validation tests
@pytest.fixture
def mock_health_objects(mocker):
    """Create multiple mock health objects for testing."""
    mock_health1 = mocker.Mock()
    mock_health1.to_dict.return_value = {"status": "UP", "component": "db"}

    mock_health2 = mocker.Mock()
    mock_health2.to_dict.return_value = {"status": "DOWN", "component": "cache"}

    return [mock_health1, mock_health2]


def test_health_results_accepts_list(mock_health_objects):
    """Test that health_results field accepts list of Health objects."""
    status = HealthCheckStatus()

    # Test assignment of list
    status.health_results = mock_health_objects
    assert status.health_results == mock_health_objects

    # Test assignment of empty list
    status.health_results = []
    assert status.health_results == []

    # Test assignment of single item list
    status.health_results = [mock_health_objects[0]]
    assert status.health_results == [mock_health_objects[0]]


def test_suppressed_health_results_accepts_list(mock_health_objects):
    """Test that suppressed_health_results field accepts list of Health objects."""
    status = HealthCheckStatus()

    # Test assignment of list
    status.suppressed_health_results = mock_health_objects
    assert status.suppressed_health_results == mock_health_objects

    # Test assignment of empty list
    status.suppressed_health_results = []
    assert status.suppressed_health_results == []

    # Test assignment of single item list
    status.suppressed_health_results = [mock_health_objects[0]]
    assert status.suppressed_health_results == [mock_health_objects[0]]


def test_healthy_accepts_boolean():
    """Test that healthy field accepts boolean values."""
    status = HealthCheckStatus()

    # Test True assignment
    status.healthy = True
    assert status.healthy is True

    # Test False assignment
    status.healthy = False
    assert status.healthy is False

    # Test None assignment
    status.healthy = None
    assert status.healthy is None


def test_backward_compatible_data_flow(mock_health_objects):
    """Test complete data flow for backward compatibility."""
    # Create with constructor
    health_results = [mock_health_objects]
    status = HealthCheckStatus(
        health_results=health_results, suppressed_health_results=[], healthy=True
    )

    # Verify data can be retrieved
    assert status.health_results == health_results
    assert status.suppressed_health_results == []
    assert status.healthy

    # Verify to_dict works
    result_dict = status.to_dict()
    assert isinstance(result_dict, dict)

    # Verify string representation works
    str_repr = str(status)
    assert isinstance(str_repr, str)
