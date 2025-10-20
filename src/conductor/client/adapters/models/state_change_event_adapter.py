from __future__ import annotations

from enum import Enum
from typing import Dict, List, Union, Optional

from typing_extensions import Self

from conductor.client.codegen.models.state_change_event import StateChangeEvent


class StateChangeEventType(Enum):
    onScheduled = "onScheduled"
    onStart = "onStart"
    onFailed = "onFailed"
    onSuccess = "onSuccess"
    onCancelled = "onCancelled"


class StateChangeConfig:
    swagger_types = {"type": "str", "events": "list[StateChangeEvent]"}

    attribute_map = {"type": "type", "events": "events"}

    # Keep original init for backward compatibility
    def __init__(
        self,
        event_type: Union[str, StateChangeEventType, List[StateChangeEventType]] = None,
        events: Optional[List[StateChangeEvent]] = None,
    ) -> None:
        if event_type is None:
            return
        if isinstance(event_type, list):
            self._type = ",".join(et.name for et in event_type)
        else:
            self._type = event_type.name
        self._events = events

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, event_type: StateChangeEventType) -> Self:
        self._type = event_type.name

    @property
    def events(self):
        return self._events

    @events.setter
    def events(self, events: List[StateChangeEvent]) -> Self:
        self._events = events

    def to_dict(self) -> Dict:
        """Returns the model properties as a dict"""
        result = {}
        for attr in self.swagger_types.keys():
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = [x.to_dict() if hasattr(x, "to_dict") else x for x in value]
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: ((item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item),
                        value.items(),
                    )
                )
            else:
                result[attr] = value
        return result

    def to_str(self) -> str:
        """Returns the string representation of the model"""
        return f"StateChangeConfig{{type='{self.type}', events={self.events}}}"

    def __repr__(self) -> str:
        return self.to_str()

    def __eq__(self, other) -> bool:
        """Returns true if both objects are equal"""
        if not isinstance(other, StateChangeConfig):
            return False
        return self.type == other.type and self.events == other.events

    def __ne__(self, other) -> bool:
        """Returns true if both objects are not equal"""
        return not self == other


class StateChangeEventAdapter(StateChangeEvent):
    def __init__(self, payload=None, type=None):
        """StateChangeEvent - a model defined in Swagger"""
        self._payload = None
        self._type = None
        self.discriminator = None
        self.payload = payload
        self.type = type

    @StateChangeEvent.payload.setter
    def payload(self, payload):
        """Sets the payload of this StateChangeEvent.


        :param payload: The payload of this StateChangeEvent.  # noqa: E501
        :type: dict(str, object)
        """
        if payload is None:
            raise TypeError("Invalid value for `payload`, must not be `None`")

        self._payload = payload

    @StateChangeEvent.type.setter
    def type(self, type):
        """Sets the type of this StateChangeEvent.


        :param type: The type of this StateChangeEvent.  # noqa: E501
        :type: str
        """
        print(f"type: {type}")
        if type is None:
            raise TypeError("Invalid value for `type`, must not be `None`")

        self._type = type
