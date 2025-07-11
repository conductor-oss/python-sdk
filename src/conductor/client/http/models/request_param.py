from dataclasses import dataclass
from typing import Optional, Any
import six


@dataclass
class Schema:
    """Schema definition for request parameters."""

    swagger_types = {
        'type': 'str',
        'format': 'str',
        'default_value': 'object'
    }

    attribute_map = {
        'type': 'type',
        'format': 'format',
        'default_value': 'defaultValue'
    }

    type: Optional[str] = None
    format: Optional[str] = None
    default_value: Optional[Any] = None

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
        return f"Schema(type='{self.type}', format='{self.format}', default_value={self.default_value})"


@dataclass
class RequestParam:
    """Request parameter model for API endpoints."""

    swagger_types = {
        'name': 'str',
        'type': 'str',
        'required': 'bool',
        'schema': 'Schema'
    }

    attribute_map = {
        'name': 'name',
        'type': 'type',
        'required': 'required',
        'schema': 'schema'
    }

    name: Optional[str] = None
    type: Optional[str] = None  # Query, Header, Path, etc.
    required: bool = False
    schema: Optional[Schema] = None

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
        return f"RequestParam(name='{self.name}', type='{self.type}', required={self.required})"