import unittest

from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.kafka_publish_input import \
    KafkaPublishInput


class TestKafkaPublishInput(unittest.TestCase):
    """Integration tests for KafkaPublishInput with API client serialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_client = ApiClient()
        self.sample_kafka_input = KafkaPublishInput(
            bootstrap_servers="kafka-broker:29092",
            key="test-key",
            key_serializer="org.apache.kafka.common.serialization.StringSerializer",
            value='{"test": "data"}',
            request_timeout_ms="30000",
            max_block_ms="60000",
            headers={"content-type": "application/json"},
            topic="test-topic",
        )

    def test_kafka_publish_input_serialization_structure(self):
        """Test that serialized KafkaPublishInput has the correct structure."""
        serialized = self.api_client.sanitize_for_serialization(self.sample_kafka_input)

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
            self.assertIn(key, serialized, f"Missing key '{key}' in serialized output")

        self.assertEqual(serialized["bootStrapServers"], "kafka-broker:29092")
        self.assertEqual(serialized["key"], "test-key")
        self.assertEqual(
            serialized["keySerializer"],
            "org.apache.kafka.common.serialization.StringSerializer",
        )
        self.assertEqual(serialized["value"], '{"test": "data"}')
        self.assertEqual(serialized["requestTimeoutMs"], "30000")
        self.assertEqual(serialized["maxBlockMs"], "60000")
        self.assertEqual(serialized["headers"], {"content-type": "application/json"})
        self.assertEqual(serialized["topic"], "test-topic")

    def test_kafka_publish_input_with_none_values_serialization(self):
        """Test that KafkaPublishInput with None values serializes correctly."""
        kafka_input = KafkaPublishInput(
            bootstrap_servers="kafka:9092", topic="test-topic"
        )

        serialized = self.api_client.sanitize_for_serialization(kafka_input)

        self.assertEqual(serialized["bootStrapServers"], "kafka:9092")
        self.assertEqual(serialized["topic"], "test-topic")

        self.assertNotIn("key", serialized)
        self.assertNotIn("keySerializer", serialized)
        self.assertNotIn("value", serialized)
        self.assertNotIn("requestTimeoutMs", serialized)
        self.assertNotIn("maxBlockMs", serialized)
        self.assertNotIn("headers", serialized)

    def test_kafka_publish_input_complex_headers_serialization(self):
        """Test that KafkaPublishInput with complex headers serializes correctly."""
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

        serialized = self.api_client.sanitize_for_serialization(kafka_input)

        self.assertEqual(serialized["headers"], complex_headers)
        self.assertEqual(serialized["bootStrapServers"], "kafka:9092")
        self.assertEqual(serialized["topic"], "complex-topic")
        self.assertEqual(serialized["value"], '{"complex": "data"}')

    def test_kafka_publish_input_swagger_types_consistency(self):
        """Test that swagger_types are consistent with actual serialization."""
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

        serialized = self.api_client.sanitize_for_serialization(kafka_input)

        for internal_attr, expected_type in swagger_types.items():
            external_attr = KafkaPublishInput.attribute_map[internal_attr]
            self.assertIn(
                external_attr,
                serialized,
                f"Swagger type '{internal_attr}' not found in serialized output",
            )

    def test_kafka_publish_input_attribute_map_consistency(self):
        """Test that attribute_map correctly maps all internal attributes."""
        kafka_input = self.sample_kafka_input
        internal_attrs = [
            attr
            for attr in dir(kafka_input)
            if attr.startswith("_") and not attr.startswith("__")
        ]

        for attr in internal_attrs:
            self.assertIn(
                attr,
                KafkaPublishInput.attribute_map,
                f"Internal attribute '{attr}' not found in attribute_map",
            )

        for internal_attr in KafkaPublishInput.attribute_map.keys():
            self.assertTrue(
                hasattr(kafka_input, internal_attr),
                f"Attribute_map key '{internal_attr}' not found in instance",
            )


if __name__ == "__main__":
    unittest.main()
