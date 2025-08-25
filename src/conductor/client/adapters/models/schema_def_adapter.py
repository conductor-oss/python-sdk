from enum import Enum

from conductor.client.http.models.schema_def import SchemaDef


class SchemaType(str, Enum):
    JSON = ("JSON",)
    AVRO = ("AVRO",)
    PROTOBUF = "PROTOBUF"

    def __str__(self) -> str:
        return self.name.__str__()


class SchemaDefAdapter(SchemaDef):
    @SchemaDef.type.setter
    def type(self, type):
        """Sets the type of this SchemaDef.


        :param type: The type of this SchemaDef.
        :type: str
        """
        self._type = type

    @SchemaDef.name.setter
    def name(self, name):
        """Sets the name of this SchemaDef.


        :param name: The name of this SchemaDef.  # noqa: E501
        :type: str
        """
        self._name = name

    @SchemaDef.version.setter
    def version(self, version):
        """Sets the data of this SchemaDef.


        :param data: The data of this SchemaDef.  # noqa: E501
        :type: dict(str, object)
        """
        self._version = version
