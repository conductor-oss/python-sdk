from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import six


class ServiceType(str, Enum):
    HTTP = "HTTP"
    GRPC = "gRPC"


@dataclass
class OrkesCircuitBreakerConfig:
    """Circuit breaker configuration for Orkes services."""

    swagger_types = {
        'failure_rate_threshold': 'float',
        'sliding_window_size': 'int',
        'minimum_number_of_calls': 'int',
        'wait_duration_in_open_state': 'int',
        'permitted_number_of_calls_in_half_open_state': 'int',
        'slow_call_rate_threshold': 'float',
        'slow_call_duration_threshold': 'int',
        'automatic_transition_from_open_to_half_open_enabled': 'bool',
        'max_wait_duration_in_half_open_state': 'int'
    }

    attribute_map = {
        'failure_rate_threshold': 'failureRateThreshold',
        'sliding_window_size': 'slidingWindowSize',
        'minimum_number_of_calls': 'minimumNumberOfCalls',
        'wait_duration_in_open_state': 'waitDurationInOpenState',
        'permitted_number_of_calls_in_half_open_state': 'permittedNumberOfCallsInHalfOpenState',
        'slow_call_rate_threshold': 'slowCallRateThreshold',
        'slow_call_duration_threshold': 'slowCallDurationThreshold',
        'automatic_transition_from_open_to_half_open_enabled': 'automaticTransitionFromOpenToHalfOpenEnabled',
        'max_wait_duration_in_half_open_state': 'maxWaitDurationInHalfOpenState'
    }

    failure_rate_threshold: Optional[float] = None
    sliding_window_size: Optional[int] = None
    minimum_number_of_calls: Optional[int] = None
    wait_duration_in_open_state: Optional[int] = None
    permitted_number_of_calls_in_half_open_state: Optional[int] = None
    slow_call_rate_threshold: Optional[float] = None
    slow_call_duration_threshold: Optional[int] = None
    automatic_transition_from_open_to_half_open_enabled: Optional[bool] = None
    max_wait_duration_in_half_open_state: Optional[int] = None

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


@dataclass
class Config:
    """Configuration class for service registry."""

    swagger_types = {
        'circuit_breaker_config': 'OrkesCircuitBreakerConfig'
    }

    attribute_map = {
        'circuit_breaker_config': 'circuitBreakerConfig'
    }

    circuit_breaker_config: OrkesCircuitBreakerConfig = field(default_factory=OrkesCircuitBreakerConfig)

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


@dataclass
class ServiceRegistry:
    """Service registry model for registering HTTP and gRPC services."""

    swagger_types = {
        'name': 'str',
        'type': 'str',
        'service_uri': 'str',
        'methods': 'list[ServiceMethod]',
        'request_params': 'list[RequestParam]',
        'config': 'Config'
    }

    attribute_map = {
        'name': 'name',
        'type': 'type',
        'service_uri': 'serviceURI',
        'methods': 'methods',
        'request_params': 'requestParams',
        'config': 'config'
    }

    name: Optional[str] = None
    type: Optional[str] = None
    service_uri: Optional[str] = None
    methods: List['ServiceMethod'] = field(default_factory=list)
    request_params: List['RequestParam'] = field(default_factory=list)
    config: Config = field(default_factory=Config)

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