import unittest
import json
from typing import Dict, List

from conductor.client.http.models.state_change_event import StateChangeEvent, StateChangeConfig, StateChangeEventType
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestStateChangeEventSerialization(unittest.TestCase):
    def setUp(self):
        # Load JSON templates
        self.state_change_event_json_str = JsonTemplateResolver.get_json_string("StateChangeEvent")

    def test_state_change_event_serde(self):
        # 1. Deserialize JSON to SDK model
        state_change_event_json = json.loads(self.state_change_event_json_str)

        # Create model instance using constructor
        event = StateChangeEvent(
            type=state_change_event_json["type"],
            payload=state_change_event_json["payload"]
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(event.type, state_change_event_json["type"])
        self.assertEqual(event.payload, state_change_event_json["payload"])

        # 3. Serialize back to JSON
        serialized_json = event.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(serialized_json["type"], state_change_event_json["type"])
        self.assertEqual(serialized_json["payload"], state_change_event_json["payload"])

    def test_state_change_config_multiple_event_types(self):
        # Test with multiple event types
        event_types = [StateChangeEventType.onStart, StateChangeEventType.onSuccess]
        events = [
            StateChangeEvent(type="sample_type", payload={"key": "value"})
        ]

        config = StateChangeConfig(event_type=event_types, events=events)

        # Verify type field contains comma-separated event type names
        self.assertEqual(config.type, "onStart,onSuccess")

        # Serialize and verify
        serialized_json = config.to_dict()
        self.assertEqual(serialized_json["type"], "onStart,onSuccess")
        self.assertEqual(len(serialized_json["events"]), 1)
        self.assertEqual(serialized_json["events"][0]["type"], "sample_type")
        self.assertEqual(serialized_json["events"][0]["payload"], {"key": "value"})


if __name__ == '__main__':
    unittest.main()