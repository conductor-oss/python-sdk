from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import six


@dataclass
class ServiceMethod:
    """Service method model matching the Java ServiceMethod POJO."""

    swagger_types = {
        'id': 'int',
        'operation_name': 'str',
        'method_name': 'str',
        'method_type': 'str',
        'input_type': 'str',
        'output_type': 'str',
        'request_params': 'list[RequestParam]',
        'example_input': 'dict'
    }

    attribute_map = {
        'id': 'id',
        'operation_name': 'operationName',
        'method_name': 'methodName',
        'method_type': 'methodType',
        'input_type': 'inputType',
        'output_type': 'outputType',
        'request_params': 'requestParams',
        'example_input': 'exampleInput'
    }

    id: Optional[int] = None
    operation_name: Optional[str] = None
    method_name: Optional[str] = None
    method_type: Optional[str] = None  # GET, PUT, POST, UNARY, SERVER_STREAMING etc.
    input_type: Optional[str] = None
    output_type: Optional[str] = None
    request_params: Optional[List[Any]] = None  # List of RequestParam objects
    example_input: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.request_params is None:
            self.request_params = []
        if self.example_input is None:
            self.example_input = {}

    def to_dict(self):
        """Returns the model properties as a dict using the correct JSON field names."""
        result = {}
        for attr, json_key in six.iteritems(self.attribute_map):
            value = getattr(self, attr)
            if value is not None:
                if isinstance(value, list):
                    result[json_key] = list(map(
                        lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                        value
                    ))
                elif hasattr(value, "to_dict"):
                    result[json_key] = value.to_dict()
                elif isinstance(value, dict):
                    result[json_key] = dict(map(
                        lambda item: (item[0], item[1].to_dict())
                        if hasattr(item[1], "to_dict") else item,
                        value.items()
                    ))
                else:
                    result[json_key] = value
        return result

    def __str__(self):
        return f"ServiceMethod(operation_name='{self.operation_name}', method_name='{self.method_name}', method_type='{self.method_type}')"


# For backwards compatibility, add helper methods
@dataclass
class RequestParam:
    """Request parameter model (placeholder - define based on actual Java RequestParam class)."""

    name: Optional[str] = None
    type: Optional[str] = None
    required: Optional[bool] = False
    description: Optional[str] = None

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'required': self.required,
            'description': self.description
        }