import pytest

from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.kafka_publish_input import KafkaPublishInput


@pytest.fixture
def api_client():
    """Create an API client instance for testing."""
    return ApiClient()

@pytest.fixture
def sample_kafka_input():
    """Create a sample KafkaPublishInput with all fields populated."""
    return KafkaPublishInput(
        bootstrap_servers="kafka-broker:29092",
        key="test-key",
        key_serializer="org.apache.kafka.common.serialization.StringSerializer",
        value='{"test": "data"}',
        request_timeout_ms="30000",
        max_block_ms="60000",
        headers={"content-type": "application/json"},
        topic="test-topic",
    )

@pytest.fixture
def minimal_kafka_input():
    """Create a minimal KafkaPublishInput with only required fields."""
    return KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        topic="test-topic",
    )

def test_initialization_with_all_parameters():
    """Test KafkaPublishInput initialization with all parameters."""
    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        key="test-key",
        key_serializer="org.apache.kafka.common.serialization.StringSerializer",
        value='{"test": "data"}',
        request_timeout_ms="30000",
        max_block_ms="60000",
        headers={"content-type": "application/json"},
        topic="test-topic",
    )

    assert kafka_input.bootstrap_servers == "kafka:9092"
    assert kafka_input.key == "test-key"
    assert kafka_input.key_serializer == "org.apache.kafka.common.serialization.StringSerializer"
    assert kafka_input.value == '{"test": "data"}'
    assert kafka_input.request_timeout_ms == "30000"
    assert kafka_input.max_block_ms == "60000"
    assert kafka_input.headers == {"content-type": "application/json"}
    assert kafka_input.topic == "test-topic"

def test_initialization_with_minimal_parameters():
    """Test KafkaPublishInput initialization with minimal parameters."""
    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        topic="test-topic",
    )

    assert kafka_input.bootstrap_servers == "kafka:9092"
    assert kafka_input.topic == "test-topic"
    assert kafka_input.key is None
    assert kafka_input.key_serializer is None
    assert kafka_input.value is None
    assert kafka_input.request_timeout_ms is None
    assert kafka_input.max_block_ms is None
    assert kafka_input.headers is None

def test_initialization_with_none_values():
    """Test KafkaPublishInput initialization with explicit None values."""
    kafka_input = KafkaPublishInput(
        bootstrap_servers=None,
        key=None,
        key_serializer=None,
        value=None,
        request_timeout_ms=None,
        max_block_ms=None,
        headers=None,
        topic=None,
    )

    assert kafka_input.bootstrap_servers is None
    assert kafka_input.key is None
    assert kafka_input.key_serializer is None
    assert kafka_input.value is None
    assert kafka_input.request_timeout_ms is None
    assert kafka_input.max_block_ms is None
    assert kafka_input.headers is None
    assert kafka_input.topic is None

def test_serialization_with_all_fields(api_client, sample_kafka_input):
    """Test serialization of KafkaPublishInput with all fields populated."""
    serialized = api_client.sanitize_for_serialization(sample_kafka_input)

    expected_data = {
        "bootStrapServers": "kafka-broker:29092",
        "key": "test-key",
        "keySerializer": "org.apache.kafka.common.serialization.StringSerializer",
        "value": '{"test": "data"}',
        "requestTimeoutMs": "30000",
        "maxBlockMs": "60000",
        "headers": {"content-type": "application/json"},
        "topic": "test-topic",
    }

    assert serialized == expected_data

def test_serialization_with_minimal_fields(api_client, minimal_kafka_input):
    """Test serialization of KafkaPublishInput with minimal fields."""
    serialized = api_client.sanitize_for_serialization(minimal_kafka_input)

    expected_data = {
        "bootStrapServers": "kafka:9092",
        "topic": "test-topic",
    }

    assert serialized == expected_data

def test_serialization_with_complex_headers(api_client):
    """Test serialization with complex header structures."""
    complex_headers = {
        "content-type": "application/json",
        "correlation-id": "test-123",
        "user-agent": "conductor-python-sdk",
        "custom-header": "custom-value",
        "nested": {"key": "value"},
    }

    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        headers=complex_headers,
        topic="complex-topic",
        value='{"complex": "data"}',
    )

    serialized = api_client.sanitize_for_serialization(kafka_input)

    assert serialized["headers"] == complex_headers
    assert serialized["bootStrapServers"] == "kafka:9092"
    assert serialized["topic"] == "complex-topic"
    assert serialized["value"] == '{"complex": "data"}'

def test_serialization_with_empty_headers(api_client):
    """Test serialization with empty headers dictionary."""
    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        headers={},
        topic="test-topic",
    )

    serialized = api_client.sanitize_for_serialization(kafka_input)

    assert serialized["headers"] == {}
    assert serialized["bootStrapServers"] == "kafka:9092"
    assert serialized["topic"] == "test-topic"

def test_serialization_with_numeric_strings(api_client):
    """Test serialization with numeric values as strings."""
    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        request_timeout_ms="5000",
        max_block_ms="10000",
        topic="test-topic",
    )

    serialized = api_client.sanitize_for_serialization(kafka_input)

    assert serialized["requestTimeoutMs"] == "5000"
    assert serialized["maxBlockMs"] == "10000"
    assert isinstance(serialized["requestTimeoutMs"], str)
    assert isinstance(serialized["maxBlockMs"], str)

def test_swagger_types_consistency():
    """Test that swagger_types are consistent with the class structure."""
    expected_swagger_types = {
        "_bootstrap_servers": "str",
        "_key": "str",
        "_key_serializer": "str",
        "_value": "str",
        "_request_timeout_ms": "str",
        "_max_block_ms": "str",
        "_headers": "dict[str, Any]",
        "_topic": "str",
    }

    assert KafkaPublishInput.swagger_types == expected_swagger_types

def test_attribute_map_consistency():
    """Test that attribute_map correctly maps internal to external names."""
    expected_attribute_map = {
        "_bootstrap_servers": "bootStrapServers",
        "_key": "key",
        "_key_serializer": "keySerializer",
        "_value": "value",
        "_request_timeout_ms": "requestTimeoutMs",
        "_max_block_ms": "maxBlockMs",
        "_headers": "headers",
        "_topic": "topic",
    }

    assert KafkaPublishInput.attribute_map == expected_attribute_map

def test_property_access(sample_kafka_input):
    """Test that all properties are accessible and return correct values."""
    assert sample_kafka_input.bootstrap_servers == "kafka-broker:29092"
    assert sample_kafka_input.key == "test-key"
    assert sample_kafka_input.key_serializer == "org.apache.kafka.common.serialization.StringSerializer"
    assert sample_kafka_input.value == '{"test": "data"}'
    assert sample_kafka_input.request_timeout_ms == "30000"
    assert sample_kafka_input.max_block_ms == "60000"
    assert sample_kafka_input.headers == {"content-type": "application/json"}
    assert sample_kafka_input.topic == "test-topic"

def test_deep_copy_behavior():
    """Test that the constructor performs deep copy of input parameters."""
    original_headers = {"test": "value"}
    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        headers=original_headers,
        topic="test-topic",
    )

    # Modify the original headers
    original_headers["modified"] = "new_value"

    # The kafka_input headers should remain unchanged
    assert kafka_input.headers == {"test": "value"}
    assert "modified" not in kafka_input.headers

def test_serialization_round_trip(api_client, sample_kafka_input):
    """Test that serialization preserves all data correctly."""
    serialized = api_client.sanitize_for_serialization(sample_kafka_input)

    # Verify all expected keys are present
    expected_keys = [
        "bootStrapServers",
        "key",
        "keySerializer",
        "value",
        "requestTimeoutMs",
        "maxBlockMs",
        "headers",
        "topic",
    ]

    for key in expected_keys:
        assert key in serialized, f"Missing key '{key}' in serialized output"

    # Verify all values match
    assert serialized["bootStrapServers"] == "kafka-broker:29092"
    assert serialized["key"] == "test-key"
    assert serialized["keySerializer"] == "org.apache.kafka.common.serialization.StringSerializer"
    assert serialized["value"] == '{"test": "data"}'
    assert serialized["requestTimeoutMs"] == "30000"
    assert serialized["maxBlockMs"] == "60000"
    assert serialized["headers"] == {"content-type": "application/json"}
    assert serialized["topic"] == "test-topic"

def test_serialization_excludes_none_values(api_client):
    """Test that None values are excluded from serialization."""
    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092",
        topic="test-topic",
    )

    serialized = api_client.sanitize_for_serialization(kafka_input)

    # Only non-None values should be present
    assert "bootStrapServers" in serialized
    assert "topic" in serialized
    assert "key" not in serialized
    assert "keySerializer" not in serialized
    assert "value" not in serialized
    assert "requestTimeoutMs" not in serialized
    assert "maxBlockMs" not in serialized
    assert "headers" not in serialized
