from dataclasses import dataclass
from typing import Optional
import six


@dataclass
class ProtoRegistryEntry:
    """Protocol buffer registry entry for storing service definitions."""

    swagger_types = {
        'service_name': 'str',
        'filename': 'str',
        'data': 'bytes'
    }

    attribute_map = {
        'service_name': 'serviceName',
        'filename': 'filename',
        'data': 'data'
    }

    service_name: str
    filename: str
    data: bytes

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
        return f"ProtoRegistryEntry(service_name='{self.service_name}', filename='{self.filename}', data_size={len(self.data)})"