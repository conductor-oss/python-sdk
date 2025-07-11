from dataclasses import dataclass
from typing import Optional
import six


@dataclass
class CircuitBreakerTransitionResponse:
    """Circuit breaker transition response model."""

    swagger_types = {
        'service': 'str',
        'previous_state': 'str',
        'current_state': 'str',
        'transition_timestamp': 'int',
        'message': 'str'
    }

    attribute_map = {
        'service': 'service',
        'previous_state': 'previousState',
        'current_state': 'currentState',
        'transition_timestamp': 'transitionTimestamp',
        'message': 'message'
    }

    service: Optional[str] = None
    previous_state: Optional[str] = None
    current_state: Optional[str] = None
    transition_timestamp: Optional[int] = None
    message: Optional[str] = None

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}
        for attr, _ in six.iteritems(self.swagger_types):
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

    def __str__(self):
        return f"CircuitBreakerTransitionResponse(service='{self.service}', previous_state='{self.previous_state}', current_state='{self.current_state}', transition_timestamp={self.transition_timestamp}, message='{self.message}')"