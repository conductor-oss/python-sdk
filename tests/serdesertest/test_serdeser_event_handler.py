import unittest
import json
from conductor.client.http.models.event_handler import EventHandler
from conductor.client.http.models.action import Action
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestEventHandlerSerDe(unittest.TestCase):
    """Test serialization and deserialization of EventHandler model"""

    def setUp(self):
        # Load template JSON using resolver
        self.server_json_str = JsonTemplateResolver.get_json_string("EventHandler")
        self.server_json = json.loads(self.server_json_str)

    def test_deserialize_serialize(self):
        """Test deserialization and serialization of EventHandler model"""
        # 1. Deserialize server JSON into SDK model object
        # Create Action objects first for the actions list
        actions = []
        if self.server_json.get('actions'):
            for action_json in self.server_json.get('actions'):
                # Convert JSON keys to Python attribute names using the attribute map
                converted_action = {}
                for key, value in action_json.items():
                    # Find the Python attribute name for this JSON key
                    python_attr = None
                    for attr, json_key in Action.attribute_map.items():
                        if json_key == key:
                            python_attr = attr
                            break

                    if python_attr:
                        converted_action[python_attr] = value
                    else:
                        # Skip keys not in attribute_map
                        pass

                action = Action(**converted_action)
                actions.append(action)

        # Create EventHandler object using constructor
        model = EventHandler(
            name=self.server_json.get('name'),
            event=self.server_json.get('event'),
            condition=self.server_json.get('condition'),
            actions=actions,
            active=self.server_json.get('active'),
            evaluator_type=self.server_json.get('evaluatorType')
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(model.name, self.server_json.get('name'))
        self.assertEqual(model.event, self.server_json.get('event'))
        self.assertEqual(model.condition, self.server_json.get('condition'))
        self.assertEqual(model.active, self.server_json.get('active'))
        self.assertEqual(model.evaluator_type, self.server_json.get('evaluatorType'))

        # Verify actions list
        self.assertIsNotNone(model.actions)
        self.assertEqual(len(model.actions), len(self.server_json.get('actions', [])))

        # If actions exist in the JSON, verify each action is properly deserialized
        if self.server_json.get('actions'):
            for i, action in enumerate(model.actions):
                self.assertIsInstance(action, Action)
                # Further verification of Action properties could be done here

        # 3. Serialize the model back to JSON
        result_json = model.to_dict()

        # 4. Ensure the resulting JSON matches the original
        # Verify field mapping between camelCase and snake_case
        self.assertEqual(result_json.get('name'), self.server_json.get('name'))
        self.assertEqual(result_json.get('event'), self.server_json.get('event'))
        self.assertEqual(result_json.get('condition'), self.server_json.get('condition'))
        self.assertEqual(result_json.get('active'), self.server_json.get('active'))

        # The SDK uses evaluator_type internally but the JSON may use evaluatorType
        # Check how the field is serialized in the result
        if 'evaluator_type' in result_json:
            self.assertEqual(result_json.get('evaluator_type'), self.server_json.get('evaluatorType'))
        elif 'evaluatorType' in result_json:
            self.assertEqual(result_json.get('evaluatorType'), self.server_json.get('evaluatorType'))

        # Verify complex structures like lists
        if self.server_json.get('actions'):
            self.assertEqual(len(result_json.get('actions')), len(self.server_json.get('actions')))

            # Additional validation of actions could be done here
            # This would depend on how Action.to_dict() handles serialization


if __name__ == '__main__':
    unittest.main()