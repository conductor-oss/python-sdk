import pprint
from dataclasses import dataclass, field, InitVar
from enum import Enum
from typing import Dict, Any, Optional
import six
from deprecated import deprecated

from conductor.client.http.models.auditable import Auditable


class SchemaType(str, Enum):
    JSON = "JSON",
    AVRO = "AVRO",
    PROTOBUF = "PROTOBUF"

    def __str__(self) -> str:
        return self.name.__str__()


@dataclass
class SchemaDef(Auditable):
    swagger_types = {
        **Auditable.swagger_types,
        'name': 'str',
        'version': 'int',
        'type': 'str',
        'data': 'dict(str, object)',
        'external_ref': 'str'
    }

    attribute_map = {
        **Auditable.attribute_map,
        'name': 'name',
        'version': 'version',
        'type': 'type',
        'data': 'data',
        'external_ref': 'externalRef'
    }

    # Private fields for properties
    _name: Optional[str] = field(default=None, init=False)
    _version: int = field(default=1, init=False)
    _type: Optional[SchemaType] = field(default=None, init=False)
    _data: Optional[Dict[str, object]] = field(default=None, init=False)
    _external_ref: Optional[str] = field(default=None, init=False)
    
    # InitVars for constructor parameters
    name_init: InitVar[Optional[str]] = None
    version_init: InitVar[Optional[int]] = 1
    type_init: InitVar[Optional[SchemaType]] = None
    data_init: InitVar[Optional[Dict[str, object]]] = None
    external_ref_init: InitVar[Optional[str]] = None
    
    discriminator: Any = field(default=None, init=False)

    def __init__(self, name: str = None, version: int = 1, type: SchemaType = None,
                 data: Dict[str, object] = None, external_ref: str = None,
                 owner_app: str = None, create_time: int = None, update_time: int = None,
                 created_by: str = None, updated_by: str = None):  # noqa: E501
        super().__init__()
        self._name = None
        self._version = None
        self._type = None
        self._data = None
        self._external_ref = None
        self.discriminator = None
        if name is not None:
            self.name = name
        if version is not None:
            self.version = version
        if type is not None:
            self.type = type
        if data is not None:
            self.data = data
        if external_ref is not None:
            self.external_ref = external_ref

        # Set Auditable fields
        if owner_app is not None:
            self.owner_app = owner_app
        if create_time is not None:
            self.create_time = create_time
        if update_time is not None:
            self.update_time = update_time
        if created_by is not None:
            self.created_by = created_by
        if updated_by is not None:
            self.updated_by = updated_by

    def __post_init__(self, name_init: Optional[str], version_init: Optional[int], 
                     type_init: Optional[SchemaType], data_init: Optional[Dict[str, object]],
                     external_ref_init: Optional[str]):
        # This is called after __init__ when using @dataclass
        # We don't need to do anything here as __init__ handles initialization
        pass

    @property
    def name(self):
        """Gets the name of this SchemaDef.  # noqa: E501

        :return: The name of this SchemaDef.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this SchemaDef.

        :param name: The name of this SchemaDef.  # noqa: E501
        :type: str
        """
        self._name = name

    @property
    @deprecated
    def version(self):
        """Gets the version of this SchemaDef.  # noqa: E501

        :return: The version of this SchemaDef.  # noqa: E501
        :rtype: int
        """
        return self._version

    @version.setter
    @deprecated
    def version(self, version):
        """Sets the version of this SchemaDef.

        :param version: The version of this SchemaDef.  # noqa: E501
        :type: int
        """
        self._version = version

    @property
    def type(self) -> SchemaType:
        """Gets the type of this SchemaDef.  # noqa: E501

        :return: The type of this SchemaDef.  # noqa: E501
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: SchemaType):
        """Sets the type of this SchemaDef.

        :param type: The type of this SchemaDef.  # noqa: E501
        :type: str
        """
        self._type = type

    @property
    def data(self) -> Dict[str, object]:
        """Gets the data of this SchemaDef.  # noqa: E501

        :return: The data of this SchemaDef.  # noqa: E501
        :rtype: Dict[str, object]
        """
        return self._data

    @data.setter
    def data(self, data: Dict[str, object]):
        """Sets the data of this SchemaDef.

        :param data: The data of this SchemaDef.  # noqa: E501
        :type: Dict[str, object]
        """
        self._data = data

    @property
    def external_ref(self):
        """Gets the external_ref of this SchemaDef.  # noqa: E501

        :return: The external_ref of this SchemaDef.  # noqa: E501
        :rtype: str
        """
        return self._external_ref

    @external_ref.setter
    def external_ref(self, external_ref):
        """Sets the external_ref of this SchemaDef.

        :param external_ref: The external_ref of this SchemaDef.  # noqa: E501
        :type: str
        """
        self._external_ref = external_ref

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
        if issubclass(SchemaDef, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, SchemaDef):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other