import json

import pytest

from conductor.client.http.models.action import ActionAdapter
from conductor.client.http.models.event_handler import EventHandlerAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("EventHandler")
    return json.loads(server_json_str)


def test_deserialize_serialize(server_json):
    actions = []
    if server_json.get("actions"):
        for action_json in server_json.get("actions"):
            converted_action = {}
            for key, value in action_json.items():
                python_attr = None
                for attr, json_key in ActionAdapter.attribute_map.items():
                    if json_key == key:
                        python_attr = attr
                        break
                if python_attr:
                    converted_action[python_attr] = value
            action = ActionAdapter(**converted_action)
            actions.append(action)
    model = EventHandlerAdapter(
        name=server_json.get("name"),
        event=server_json.get("event"),
        condition=server_json.get("condition"),
        actions=actions,
        active=server_json.get("active"),
        evaluator_type=server_json.get("evaluatorType"),
    )
    assert model.name == server_json.get("name")
    assert model.event == server_json.get("event")
    assert model.condition == server_json.get("condition")
    assert model.active == server_json.get("active")
    assert model.evaluator_type == server_json.get("evaluatorType")
    assert model.actions is not None
    assert len(model.actions) == len(server_json.get("actions", []))
    if server_json.get("actions"):
        for action in model.actions:
            assert isinstance(action, ActionAdapter)
    result_json = model.to_dict()
    assert result_json.get("name") == server_json.get("name")
    assert result_json.get("event") == server_json.get("event")
    assert result_json.get("condition") == server_json.get("condition")
    assert result_json.get("active") == server_json.get("active")
    if "evaluator_type" in result_json:
        assert result_json.get("evaluator_type") == server_json.get("evaluatorType")
    elif "evaluatorType" in result_json:
        assert result_json.get("evaluatorType") == server_json.get("evaluatorType")
    if server_json.get("actions"):
        assert len(result_json.get("actions")) == len(server_json.get("actions"))
