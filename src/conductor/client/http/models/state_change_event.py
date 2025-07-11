from dataclasses import dataclass, field, InitVar
from enum import Enum
from typing import Union, List, Dict, Optional
from typing_extensions import Self
from deprecated import deprecated


class StateChangeEventType(Enum):
    onScheduled = 'onScheduled'
    onStart = 'onStart'
    onFailed = 'onFailed'
    onSuccess = 'onSuccess'
    onCancelled = 'onCancelled'


@dataclass
class StateChangeEvent:
    swagger_types = {
        'type': 'str',
        'payload': 'Dict[str, object]'
    }

    attribute_map = {
        'type': 'type',
        'payload': 'payload'
    }

    _type: str = field(default=None, init=False)
    _payload: Dict[str, object] = field(default=None, init=False)
    
    # Keep original init for backward compatibility
    def __init__(self, type: str, payload: Dict[str, object]) -> None:
        self._type = type
        self._payload = payload
    
    def __post_init__(self) -> None:
        pass

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type: str) -> Self:
        self._type = type

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, payload: Dict[str, object]) -> Self:
        self._payload = payload
    
    def to_dict(self) -> Dict:
        """Returns the model properties as a dict"""
        result = {}
        for attr, _ in self.swagger_types.items():
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        return result
    
    def to_str(self) -> str:
        """Returns the string representation of the model"""
        return f"StateChangeEvent{{type='{self.type}', payload={self.payload}}}"
    
    def __repr__(self) -> str:
        return self.to_str()
    
    def __eq__(self, other) -> bool:
        """Returns true if both objects are equal"""
        if not isinstance(other, StateChangeEvent):
            return False
        return self.type == other.type and self.payload == other.payload
    
    def __ne__(self, other) -> bool:
        """Returns true if both objects are not equal"""
        return not self == other


@dataclass
class StateChangeConfig:
    swagger_types = {
        'type': 'str',
        'events': 'list[StateChangeEvent]'
    }

    attribute_map = {
        'type': 'type',
        'events': 'events'
    }

    _type: str = field(default=None, init=False)
    _events: List[StateChangeEvent] = field(default=None, init=False)
    
    # Keep original init for backward compatibility
    def __init__(self, event_type: Union[str, StateChangeEventType, List[StateChangeEventType]] = None, events: List[StateChangeEvent] = None) -> None:
        if event_type is None:
            return
        if isinstance(event_type, list):
            str_values = []
            for et in event_type:
                str_values.append(et.name)
            self._type = ','.join(str_values)
        else:
            self._type = event_type.name
        self._events = events
    
    def __post_init__(self) -> None:
        pass

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
        for attr, _ in self.swagger_types.items():
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
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