import inspect

import pytest

from conductor.client.adapters.models.poll_data_adapter import PollDataAdapter


@pytest.fixture
def valid_queue_name():
    """Set up test fixture with known valid data."""
    return "test_queue"


@pytest.fixture
def valid_domain():
    """Set up test fixture with known valid data."""
    return "test_domain"


@pytest.fixture
def valid_worker_id():
    """Set up test fixture with known valid data."""
    return "worker_123"


@pytest.fixture
def valid_last_poll_time():
    """Set up test fixture with known valid data."""
    return 1640995200  # Unix timestamp


def test_constructor_signature_backward_compatibility():
    """Test that constructor signature remains compatible."""
    # Get constructor signature
    sig = inspect.signature(PollDataAdapter.__init__)
    params = list(sig.parameters.keys())

    # Verify expected parameters exist (excluding 'self')
    expected_params = ["queue_name", "domain", "worker_id", "last_poll_time"]
    for param in expected_params:
        assert (
            param in params
        ), f"Constructor parameter '{param}' missing - breaks backward compatibility"

    # Verify all parameters have default values (None)
    for param_name in expected_params:
        param = sig.parameters[param_name]
        assert (
            param.default is None
        ), f"Parameter '{param_name}' should have default value None"


def test_constructor_with_no_arguments():
    """Test that constructor works with no arguments (all defaults)."""
    poll_data = PollDataAdapter()
    assert isinstance(poll_data, PollDataAdapter)


def test_constructor_with_all_arguments(
    valid_queue_name, valid_domain, valid_worker_id, valid_last_poll_time
):
    """Test that constructor works with all existing arguments."""
    poll_data = PollDataAdapter(
        queue_name=valid_queue_name,
        domain=valid_domain,
        worker_id=valid_worker_id,
        last_poll_time=valid_last_poll_time,
    )
    assert isinstance(poll_data, PollDataAdapter)


def test_constructor_with_partial_arguments(valid_queue_name, valid_domain):
    """Test that constructor works with partial arguments."""
    poll_data = PollDataAdapter(queue_name=valid_queue_name, domain=valid_domain)
    assert isinstance(poll_data, PollDataAdapter)


def test_required_properties_exist():
    """Test that all expected properties exist and are accessible."""
    poll_data = PollDataAdapter()

    required_properties = ["queue_name", "domain", "worker_id", "last_poll_time"]

    for prop in required_properties:
        assert hasattr(
            poll_data, prop
        ), f"Property '{prop}' missing - breaks backward compatibility"

        # Test getter works
        getattr(poll_data, prop)


def test_property_setters_work(
    valid_queue_name, valid_domain, valid_worker_id, valid_last_poll_time
):
    """Test that all property setters continue to work."""
    poll_data = PollDataAdapter()

    # Test setting each property
    test_values = {
        "queue_name": valid_queue_name,
        "domain": valid_domain,
        "worker_id": valid_worker_id,
        "last_poll_time": valid_last_poll_time,
    }

    for prop, value in test_values.items():
        setattr(poll_data, prop, value)
        retrieved_value = getattr(poll_data, prop)
        assert (
            retrieved_value == value
        ), f"Property '{prop}' setter/getter roundtrip failed"


def test_swagger_types_backward_compatibility():
    """Test that swagger_types dict contains expected field types."""
    expected_types = {
        "queue_name": "str",
        "domain": "str",
        "worker_id": "str",
        "last_poll_time": "int",
    }

    # Verify swagger_types exists
    assert hasattr(
        PollDataAdapter, "swagger_types"
    ), "swagger_types attribute missing - breaks backward compatibility"

    # Verify expected types are present and unchanged
    swagger_types = PollDataAdapter.swagger_types
    for field, expected_type in expected_types.items():
        assert field in swagger_types, f"Field '{field}' missing from swagger_types"
        assert (
            swagger_types[field] == expected_type
        ), f"Field '{field}' type changed from '{expected_type}' to '{swagger_types[field]}'"


def test_attribute_map_backward_compatibility():
    """Test that attribute_map contains expected JSON mappings."""
    expected_mappings = {
        "queue_name": "queueName",
        "domain": "domain",
        "worker_id": "workerId",
        "last_poll_time": "lastPollTime",
    }

    # Verify attribute_map exists
    assert hasattr(
        PollDataAdapter, "attribute_map"
    ), "attribute_map attribute missing - breaks backward compatibility"

    # Verify expected mappings are present and unchanged
    attribute_map = PollDataAdapter.attribute_map
    for field, expected_json_key in expected_mappings.items():
        assert field in attribute_map, f"Field '{field}' missing from attribute_map"
        assert (
            attribute_map[field] == expected_json_key
        ), f"Field '{field}' JSON mapping changed from '{expected_json_key}' to '{attribute_map[field]}'"


def test_to_dict_method_exists_and_works(
    valid_queue_name, valid_domain, valid_worker_id, valid_last_poll_time
):
    """Test that to_dict method exists and produces expected structure."""
    poll_data = PollDataAdapter(
        queue_name=valid_queue_name,
        domain=valid_domain,
        worker_id=valid_worker_id,
        last_poll_time=valid_last_poll_time,
    )

    # Verify method exists
    assert hasattr(
        poll_data, "to_dict"
    ), "to_dict method missing - breaks backward compatibility"

    # Test method works
    result = poll_data.to_dict()
    assert isinstance(result, dict)

    # Verify expected keys are present
    expected_keys = ["queue_name", "domain", "worker_id", "last_poll_time"]
    for key in expected_keys:
        assert key in result, f"Key '{key}' missing from to_dict output"


def test_to_str_method_exists_and_works():
    """Test that to_str method exists and works."""
    poll_data = PollDataAdapter()

    assert hasattr(
        poll_data, "to_str"
    ), "to_str method missing - breaks backward compatibility"

    result = poll_data.to_str()
    assert isinstance(result, str)


def test_repr_method_works():
    """Test that __repr__ method works."""
    poll_data = PollDataAdapter()

    result = repr(poll_data)
    assert isinstance(result, str)


def test_equality_comparison_works(valid_queue_name):
    """Test that equality comparison (__eq__) works."""
    poll_data1 = PollDataAdapter(queue_name=valid_queue_name)
    poll_data2 = PollDataAdapter(queue_name=valid_queue_name)
    poll_data3 = PollDataAdapter(queue_name="different")

    # Test equality
    assert poll_data1 == poll_data2, "Equal objects should be equal"

    # Test inequality
    assert poll_data1 != poll_data3, "Different objects should not be equal"


def test_inequality_comparison_works(valid_queue_name):
    """Test that inequality comparison (__ne__) works."""
    poll_data1 = PollDataAdapter(queue_name=valid_queue_name)
    poll_data2 = PollDataAdapter(queue_name="different")

    assert poll_data1 != poll_data2, "Different objects should be not equal"


def test_field_assignment_after_construction(
    valid_queue_name, valid_domain, valid_worker_id, valid_last_poll_time
):
    """Test that fields can be assigned after object construction."""
    poll_data = PollDataAdapter()

    # Test that we can assign values after construction
    poll_data.queue_name = valid_queue_name
    poll_data.domain = valid_domain
    poll_data.worker_id = valid_worker_id
    poll_data.last_poll_time = valid_last_poll_time

    # Verify assignments worked
    assert poll_data.queue_name == valid_queue_name
    assert poll_data.domain == valid_domain
    assert poll_data.worker_id == valid_worker_id
    assert poll_data.last_poll_time == valid_last_poll_time


def test_none_values_handling(valid_queue_name):
    """Test that None values are handled properly."""
    poll_data = PollDataAdapter()

    # All fields should initially be None
    assert poll_data.queue_name is None
    assert poll_data.domain is None
    assert poll_data.worker_id is None
    assert poll_data.last_poll_time is None

    # Setting to None should work
    poll_data.queue_name = valid_queue_name
    poll_data.queue_name = None
    assert poll_data.queue_name is None


def test_discriminator_attribute_exists():
    """Test that discriminator attribute exists (Swagger requirement)."""
    poll_data = PollDataAdapter()

    assert hasattr(
        poll_data, "discriminator"
    ), "discriminator attribute missing - breaks Swagger compatibility"

    # Should be None by default
    assert poll_data.discriminator is None
