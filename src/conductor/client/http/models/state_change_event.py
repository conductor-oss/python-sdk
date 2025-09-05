from conductor.client.adapters.models.state_change_event_adapter import (
    StateChangeConfig, StateChangeEventAdapter, StateChangeEventType)

StateChangeEvent = StateChangeEventAdapter

__all__ = ["StateChangeEvent", "StateChangeEventType", "StateChangeConfig"]
