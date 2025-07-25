import pytest
from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.kafka_publish_input import KafkaPublishInput

@pytest.fixture
def api_client():
    return ApiClient()

@pytest.fixture
def sample_kafka_input():
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

def test_kafka_publish_input_serialization_structure(api_client, sample_kafka_input):
    serialized = api_client.sanitize_for_serialization(sample_kafka_input)
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
    assert serialized["bootStrapServers"] == "kafka-broker:29092"
    assert serialized["key"] == "test-key"
    assert serialized["keySerializer"] == "org.apache.kafka.common.serialization.StringSerializer"
    assert serialized["value"] == '{"test": "data"}'
    assert serialized["requestTimeoutMs"] == "30000"
    assert serialized["maxBlockMs"] == "60000"
    assert serialized["headers"] == {"content-type": "application/json"}
    assert serialized["topic"] == "test-topic"

def test_kafka_publish_input_with_none_values_serialization(api_client):
    kafka_input = KafkaPublishInput(
        bootstrap_servers="kafka:9092", topic="test-topic"
    )
    serialized = api_client.sanitize_for_serialization(kafka_input)
    assert serialized["bootStrapServers"] == "kafka:9092"
    assert serialized["topic"] == "test-topic"
    assert "key" not in serialized
    assert "keySerializer" not in serialized
    assert "value" not in serialized
    assert "requestTimeoutMs" not in serialized
    assert "maxBlockMs" not in serialized
    assert "headers" not in serialized

def test_kafka_publish_input_complex_headers_serialization(api_client):
    complex_headers = {
        "content-type": "application/json",
        "correlation-id": "test-123",
        "user-agent": "conductor-python-sdk",
        "custom-header": "custom-value",
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

def test_kafka_publish_input_swagger_types_consistency(api_client):
    swagger_types = KafkaPublishInput.swagger_types
    kafka_input = KafkaPublishInput(
        bootstrap_servers="test",
        key="test",
        key_serializer="test",
        value="test",
        request_timeout_ms="test",
        max_block_ms="test",
        headers={"test": "test"},
        topic="test",
    )
    serialized = api_client.sanitize_for_serialization(kafka_input)
    for internal_attr, expected_type in swagger_types.items():
        external_attr = KafkaPublishInput.attribute_map[internal_attr]
        assert external_attr in serialized, f"Swagger type '{internal_attr}' not found in serialized output"

def test_kafka_publish_input_attribute_map_consistency(api_client, sample_kafka_input):
    kafka_input = sample_kafka_input
    internal_attrs = [
        attr
        for attr in dir(kafka_input)
        if attr.startswith("_") and not attr.startswith("__")
    ]
    for attr in internal_attrs:
        assert attr in KafkaPublishInput.attribute_map, f"Internal attribute '{attr}' not found in attribute_map"
    for internal_attr in KafkaPublishInput.attribute_map.keys():
        assert hasattr(kafka_input, internal_attr), f"Attribute_map key '{internal_attr}' not found in instance"
