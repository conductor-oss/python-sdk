import pytest

from conductor.client.http.models import StateChangeEvent, StateChangeEventType, StateChangeConfig


def test_state_change_event_type_enum_values_exist():
    """Verify all existing StateChangeEventType enum values still exist."""
    required_enum_values = {
        "onScheduled": "onScheduled",
        "onStart": "onStart",
        "onFailed": "onFailed",
        "onSuccess": "onSuccess",
        "onCancelled": "onCancelled",
    }

    for name, value in required_enum_values.items():
        assert hasattr(
            StateChangeEventType, name
        ), f"StateChangeEventType.{name} must exist"
        assert (
            getattr(StateChangeEventType, name).value == value
        ), f"StateChangeEventType.{name} value must be '{value}'"


def test_state_change_event_type_enum_access():
    """Verify StateChangeEventType enum can be accessed by name and value."""
    # Test access by name
    assert StateChangeEventType.onScheduled.name == "onScheduled"
    assert StateChangeEventType.onStart.name == "onStart"
    assert StateChangeEventType.onFailed.name == "onFailed"
    assert StateChangeEventType.onSuccess.name == "onSuccess"
    assert StateChangeEventType.onCancelled.name == "onCancelled"

    # Test access by value
    assert StateChangeEventType.onScheduled.value == "onScheduled"
    assert StateChangeEventType.onStart.value == "onStart"
    assert StateChangeEventType.onFailed.value == "onFailed"
    assert StateChangeEventType.onSuccess.value == "onSuccess"
    assert StateChangeEventType.onCancelled.value == "onCancelled"


def test_state_change_event_constructor_signature():
    """Verify StateChangeEvent constructor signature remains unchanged."""
    # Test constructor with required parameters
    event = StateChangeEvent(type="test_type", payload={"key": "value"})
    assert event is not None

    # Test constructor parameter requirements - both should be required
    with pytest.raises(ValueError):
        StateChangeEvent()  # No parameters

    with pytest.raises(ValueError):
        StateChangeEvent(type="test")  # Missing payload

    with pytest.raises(ValueError):
        StateChangeEvent(payload={"key": "value"})  # Missing type


def test_state_change_event_required_properties():
    """Verify StateChangeEvent has all required properties."""
    event = StateChangeEvent(type="test_type", payload={"key": "value"})

    # Test property existence and getter functionality
    assert hasattr(event, "type"), "StateChangeEvent must have 'type' property"
    assert hasattr(event, "payload"), "StateChangeEvent must have 'payload' property"

    # Test property values
    assert event.type == "test_type"
    assert event.payload == {"key": "value"}


def test_state_change_event_property_setters():
    """Verify StateChangeEvent property setters work correctly."""
    event = StateChangeEvent(type="initial", payload={})

    # Test type setter
    event.type = "updated_type"
    assert event.type == "updated_type"

    # Test payload setter
    new_payload = {"updated": "payload"}
    event.payload = new_payload
    assert event.payload == new_payload


def test_state_change_event_class_attributes():
    """Verify StateChangeEvent class has required swagger attributes."""
    # Test swagger_types exists and has correct structure
    assert hasattr(StateChangeEvent, "swagger_types")
    swagger_types = StateChangeEvent.swagger_types
    assert "type" in swagger_types
    assert "payload" in swagger_types
    assert swagger_types["type"] == "str"
    assert swagger_types["payload"] == "dict(str, object)"

    # Test attribute_map exists and has correct structure
    assert hasattr(StateChangeEvent, "attribute_map")
    attribute_map = StateChangeEvent.attribute_map
    assert "type" in attribute_map
    assert "payload" in attribute_map
    assert attribute_map["type"] == "type"
    assert attribute_map["payload"] == "payload"


def test_state_change_config_constructor_signature():
    """Verify StateChangeConfig constructor signature remains unchanged."""
    # Test constructor with no parameters (should work)
    config = StateChangeConfig()
    assert config is not None

    # Test constructor with event_type only
    config = StateChangeConfig(event_type=StateChangeEventType.onStart)
    assert config is not None

    # Test constructor with both parameters
    events = [StateChangeEvent("test", {})]
    config = StateChangeConfig(event_type=StateChangeEventType.onSuccess, events=events)
    assert config is not None


def test_state_change_config_constructor_behavior():
    """Verify StateChangeConfig constructor behavior with different input types."""
    # Test with None (should return early)
    config = StateChangeConfig(event_type=None)
    assert config is not None

    # Test with single StateChangeEventType
    config = StateChangeConfig(event_type=StateChangeEventType.onStart)
    assert config.type == "onStart"

    # Test with list of StateChangeEventType
    event_types = [StateChangeEventType.onStart, StateChangeEventType.onSuccess]
    config = StateChangeConfig(event_type=event_types)
    assert config.type == "onStart,onSuccess"

    # Test with events
    events = [StateChangeEvent("test", {})]
    config = StateChangeConfig(event_type=StateChangeEventType.onFailed, events=events)
    assert config.events == events


def test_state_change_config_required_properties():
    """Verify StateChangeConfig has all required properties."""
    config = StateChangeConfig(event_type=StateChangeEventType.onScheduled)

    # Test property existence
    assert hasattr(config, "type"), "StateChangeConfig must have 'type' property"
    assert hasattr(config, "events"), "StateChangeConfig must have 'events' property"


def test_state_change_config_property_setters():
    """Verify StateChangeConfig property setters work correctly."""
    config = StateChangeConfig()

    # Test type setter (expects StateChangeEventType)
    config.type = StateChangeEventType.onCancelled
    assert config.type == "onCancelled"

    # Test events setter
    events = [StateChangeEvent("test", {"data": "value"})]
    config.events = events
    assert config.events == events


def test_state_change_config_class_attributes():
    """Verify StateChangeConfig class has required swagger attributes."""
    # Test swagger_types exists and has correct structure
    assert hasattr(StateChangeConfig, "swagger_types")
    swagger_types = StateChangeConfig.swagger_types
    assert "type" in swagger_types
    assert "events" in swagger_types
    assert swagger_types["type"] == "str"
    assert swagger_types["events"] == "list[StateChangeEvent]"

    # Test attribute_map exists and has correct structure
    assert hasattr(StateChangeConfig, "attribute_map")
    attribute_map = StateChangeConfig.attribute_map
    assert "type" in attribute_map
    assert "events" in attribute_map
    assert attribute_map["type"] == "type"
    assert attribute_map["events"] == "events"


def test_integration_scenario():
    """Test complete integration scenario with all components."""
    # Create events
    event1 = StateChangeEvent(type="workflow_started", payload={"workflow_id": "123"})
    event2 = StateChangeEvent(type="task_completed", payload={"task_id": "456"})

    # Create config with single event type
    config1 = StateChangeConfig(
        event_type=StateChangeEventType.onStart, events=[event1]
    )

    # Create config with multiple event types
    config2 = StateChangeConfig(
        event_type=[StateChangeEventType.onSuccess, StateChangeEventType.onFailed],
        events=[event1, event2],
    )

    # Verify everything works together
    assert config1.type == "onStart"
    assert len(config1.events) == 1
    assert config1.events[0].type == "workflow_started"

    assert config2.type == "onSuccess,onFailed"
    assert len(config2.events) == 2


def test_type_annotations_compatibility():
    """Verify type annotations remain compatible."""
    # This test ensures that the models can still be used with type checking
    event: StateChangeEvent = StateChangeEvent("test", {})
    config: StateChangeConfig = StateChangeConfig()
    event_type: StateChangeEventType = StateChangeEventType.onScheduled

    # Test that assignments work without type errors
    config.type = event_type
    config.events = [event]
    event.type = "new_type"
    event.payload = {"new": "payload"}

    assert event is not None
    assert config is not None
    assert event_type is not None
